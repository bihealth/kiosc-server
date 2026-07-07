import inspect
import logging
from ipaddress import ip_address
from typing import AsyncGenerator, Optional
from urllib3.exceptions import NewConnectionError, MaxRetryError
from urllib3.response import is_fp_closed
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseForbidden,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views import View
from django.views.generic import (
    DeleteView,
    UpdateView,
    DetailView,
    CreateView,
    ListView,
)
from django.views.generic.detail import SingleObjectMixin
from revproxy.response import get_streaming_amt
from revproxy.utils import (
    set_response_headers,
    should_stream,
    cookie_from_string,
)
from revproxy.views import ProxyView

from config.settings.base import KIOSC_CONTAINER_DEFAULT_LOG_LINES
from bgjobs.models import BackgroundJob
from timeline.models import TL_STATUS_FAILED, TL_STATUS_OK
from containers.templatetags.container_tags import colorize_state, state_bell
from filesfolders.models import File, FileData
from filesfolders.views import storage
from projectroles.plugins import PluginAPI
from projectroles.views import (
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)

from containers.forms import ContainerForm, FileSelectorForm
from containers.models import (
    Container,
    ContainerBackgroundJob,
    ACTION_START,
    ACTION_STOP,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    ACTION_RESTART,
    ACTION_DELETE,
    PROCESS_OBJECT,
    STATE_PULLING,
    STATE_RUNNING,
    STATE_DELETED,
    STATE_INITIAL,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    MASKED_KEYWORD,
)
from containers.tasks import container_task, sync_container_state
from containertemplates.forms import ContainerTemplateSelectorForm


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()
User = get_user_model()

APP_NAME = 'containers'
CELERY_SUBMIT_COUNTDOWN = 0.5
LOBBY_WAITING_PHRASES = [
    'The container is loading...',
    "Updating Windows, please don't turn off your computer...",
    'Just one more second...',
    'This could take a while, go get a coffee...',
    'You can close this page and come back later...',
]


async def _stream_response(
    proxy_response: HttpResponse,
    amt: int,
    decode_content: Optional[bool] = None,
) -> AsyncGenerator[bytes, None]:
    """Asynchronously stream an HttpResponse.

    This function is similar to HTTPResponse.stream() from urllib3.response,
    but it uses async methods to return the response chunks (if applicable).
    """
    if proxy_response.chunked and proxy_response.supports_chunked_reads():
        stream = proxy_response.read_chunked(amt, decode_content=decode_content)
        if inspect.iscoroutinefunction(stream):
            async for chunk in stream:
                yield chunk
        else:
            for chunk in stream:
                yield chunk
    else:
        while (
            not is_fp_closed(proxy_response._fp)
            or len(proxy_response._decoded_buffer) > 0
            or (
                proxy_response._decoder
                and proxy_response._decoder.has_unconsumed_tail
            )
        ):
            data = proxy_response.read(amt=amt, decode_content=decode_content)

            if data:
                yield data


class ContainerModifyMixin:
    @classmethod
    @transaction.atomic
    def _container_delete_docker(cls, container: Container, user: User) -> bool:
        """Delete a container

        This method deletes the container from Docker as a background job. It
        also creates log entries and timeline events.

        NOTE: the container is NOT deleted from the database with this method,
        just from the Docker daemon.

        :param container: Container object to be deleted
        :param user: User on behalf of whom the action is performed
        :return: True if the action succeeded, False otherwise
        """
        project = container.project
        timeline = plugin_api.get_backend_api('timeline_backend')
        bg_job = BackgroundJob.objects.create(
            name='Delete container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_DELETE,
            project=project,
            container=container,
            bg_job=bg_job,
        )
        job.add_log_entry('Deleting container...', level=LOG_LEVEL_INFO)
        if timeline:
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=user,
                event_name='delete_container',
                description=f'Delete container "{container.get_display_name()}"',
                status_type=timeline.TL_STATUS_SUBMIT,
            )
        else:
            tl_event = None

        # No async task
        container_task(job_id=job.id)
        container.refresh_from_db()

        if container.state not in (STATE_INITIAL, STATE_DELETED):
            # Add timeline event
            logger.error(
                f'Failed deleting container {container.get_display_name()}',
            )
            job.add_log_entry(
                f'Failed deleting container {container.get_display_name()}',
                level=LOG_LEVEL_ERROR,
            )
            if tl_event:
                tl_event.set_status(TL_STATUS_FAILED)
            return False

        if tl_event:
            tl_event.set_status(TL_STATUS_OK)
        return True


class ContainerCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """View for creating a container."""

    permission_required = 'containers.create_container'
    template_name = 'containers/container_form.html'
    form_class = ContainerForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['containertemplate_form'] = ContainerTemplateSelectorForm(
            auto_id='containertemplate_%s', user=self.request.user
        )

        if settings.KIOSC_EMBEDDED_FILES:
            context['files_form'] = FileSelectorForm(project=self.get_project())

        return context

    def get_initial(self):
        """Set hidden project field."""
        initial = super().get_initial()
        initial['project'] = self.get_project()
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = plugin_api.get_backend_api('timeline_backend')

        # Add timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name='create_container',
                description='Create container {container}',
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object,
                label='container',
                name=self.object.get_display_name(),
            )

        # Add container log entry
        self.object.log_entries.create(
            text='Created.\n',
            process=PROCESS_OBJECT,
            user=self.request.user,
        )

        return response


class ContainerDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ContainerModifyMixin,
    DeleteView,
):
    """View for deleting a container."""

    permission_required = 'containers.delete_container'
    template_name = 'containers/container_confirm_delete.html'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    def get_success_url(self):
        messages.success(
            self.request,
            'Container deleted.',
        )
        return reverse(
            'containers:list',
            kwargs={'project': self.object.project.sodar_uuid},
        )

    def delete(self, request, *args, **kwargs):
        container = self.get_object()
        project = self.get_project()
        success = self._container_delete_docker(container, request.user)

        if not success:
            messages.error(
                request,
                f'Failed deleting container {container.get_display_name()}',
            )

            return redirect(
                reverse(
                    'containers:list',
                    kwargs={'project': project.sodar_uuid},
                )
            )

        return super().delete(request, *args, **kwargs)


class ContainerUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """View for updating a container."""

    permission_required = 'containers.edit_container'
    template_name = 'containers/container_form.html'
    form_class = ContainerForm
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    def get_initial(self):
        initial = super().get_initial()
        initial['environment'] = self.object.get_environment_masked()
        initial['registry_user'] = (
            MASKED_KEYWORD
            if self.object.registry_user
            else self.object.registry_user
        )
        initial['registry_password'] = (
            MASKED_KEYWORD
            if self.object.registry_password
            else self.object.registry_password
        )
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['containertemplate_form'] = ContainerTemplateSelectorForm(
            auto_id='containertemplate_%s', user=self.request.user
        )

        if settings.KIOSC_EMBEDDED_FILES:
            context['files_form'] = FileSelectorForm(project=self.get_project())

        return context

    def get_success_url(self):
        # if self.object.state not in (STATE_RUNNING, STATE_PAUSED):
        #     return super().get_success_url()

        container = self.get_object()

        bg_job = BackgroundJob.objects.create(
            name='Delete container',
            project=container.project,
            job_type=ContainerBackgroundJob.spec_name,
            user=self.request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_DELETE,
            project=container.project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task synchronously
        logger.info(
            f'The container object was updated, so we schedule a job to delete the Docker container. The container id is {container.container_id}'
        )
        container_task(job_id=job.id)
        container.refresh_from_db()
        logger.info('Container deleted after update')

        messages.success(
            self.request,
            'Container updated. Please restart it in order for the changes to take effect.',
        )

        return super().get_success_url()
        # return reverse(
        #     'containers:detail',
        #     kwargs={'container': self.object.sodar_uuid},
        # )

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = plugin_api.get_backend_api('timeline_backend')

        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name='update_container',
                description='Update {container}',
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object,
                label='container',
                name=self.object.get_display_name(),
            )

        return response


class ContainerListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ListView,
):
    """View for listing containers."""

    permission_required = 'containers.view_container'
    template_name = 'containers/container_list.html'
    model = Container
    slug_url_kwarg = 'project'
    slug_field = 'sodar_uuid'


class ContainerDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """View for details of container."""

    permission_required = 'containers.view_container'
    template_name = 'containers/container_detail.html'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    def get(self, request, *args, **kwargs):
        sync_container_state(self.get_object())
        return super().get(request, *args, **kwargs)


class ContainerStartView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for starting a container."""

    permission_required = 'containers.start_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name='Start container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_START,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task
        container.date_last_access = timezone.now()
        container.save()
        container_task.apply_async(
            kwargs={'job_id': job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(request.headers.get('Referer', reverse('home')))


class ContainerStopView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for stopping a container."""

    permission_required = 'containers.stop_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name='Stop container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_STOP,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={'job_id': job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(request.headers.get('Referer', reverse('home')))


class ContainerPauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for pausing a container."""

    permission_required = 'containers.pause_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name='Pause container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_PAUSE,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={'job_id': job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(request.headers.get('Referer', reverse('home')))


class ContainerUnpauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for unpausing a container."""

    permission_required = 'containers.unpause_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name='Unpause container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_UNPAUSE,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={'job_id': job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(request.headers.get('Referer', reverse('home')))


class ContainerRestartView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for restarting a container."""

    permission_required = 'containers.start_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name='Restart container',
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_RESTART,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={'job_id': job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(request.headers.get('Referer', reverse('home')))


class KioscProxyView(ProxyView):
    """Inheriting the ProxyView to adjust settings.

    This view is routed to the "Open App" button for containers. It dispatches
    the request to the actual reverse proxy.
    """

    rewrite = ((r'^/container/proxy/(?P<container>[a-f0-9-]+)/', '/'),)

    def dispatch(self, request, path):
        """Override the dispatch method.

        This avoids a warning about Django needing asynchronous iterators
        to process StreamingHttpResponse objects. This function combines
        ProxyView.dispatch() from revproxy.views and get_django_response()
        from revproxy.utils.
        """
        self.request_headers = self.get_request_headers()

        redirect_to = self._format_path_to_redirect(request)
        if redirect_to:
            return redirect(redirect_to)

        try:
            proxy_response = self._created_proxy_response(request, path)
        except MaxRetryError as ex:
            logger.warning(
                'Container not yet available for the reverse proxy: %s', str(ex)
            )
            raise MaxRetryError(ex.pool, ex.url)

        self._replace_host_on_redirect_location(request, proxy_response)
        self._set_content_type(request, proxy_response)

        status = proxy_response.status
        headers = proxy_response.headers

        logger.debug('Proxy response headers: %s', headers)

        content_type = headers.get('Content-Type')

        logger.debug('Content-Type: %s', content_type)

        if should_stream(proxy_response):
            if self.streaming_amount is None:
                amt = get_streaming_amt(proxy_response)
            else:
                amt = self.streaming_amount

            logger.debug(
                (
                    'Starting streaming HTTP Response, buffering amount='
                    '"%s bytes"'
                ),
                amt,
            )
            response = StreamingHttpResponse(
                _stream_response(proxy_response, amt),
                status=status,
                content_type=content_type,
            )
        else:
            content = proxy_response.data or b''
            response = HttpResponse(
                content, status=status, content_type=content_type
            )

        set_response_headers(response, headers)

        cookies = proxy_response.headers.getlist('set-cookie')
        for cookie_string in cookies:
            cookie_dict = cookie_from_string(
                cookie_string, strict_cookies=False
            )
            # if cookie is invalid cookie_dict will be None
            if cookie_dict:
                response.set_cookie(**cookie_dict)

        logger.debug('Response cookies: %s', response.cookies)

        logger.debug('RESPONSE RETURNED: %s', response)
        return response


class ReverseProxyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    KioscProxyView,
):
    """View for reverse proxy."""

    permission_required = 'containers.proxy'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()

        container = self.get_object()
        kwargs.pop('container')

        # We don't need to track all accesses. First, Kiosc will pass a
        # Kiosc-Preflight header when doing automated checks. Second, we don't
        # need to track internal requests to the app, just tracking the initial
        # request should be enough.
        if (
            not request.headers.get('Kiosc-Preflight')
            and kwargs['path'] == container.container_path
        ):
            timeline = plugin_api.get_backend_api('timeline_backend')
        else:
            timeline = None

        if timeline:
            tl_event = timeline.add_event(
                project=container.project,
                app_name=APP_NAME,
                user=request.user,
                event_name='access_container',
                description='Access app {container}',
                status_type=timeline.TL_STATUS_INIT,
            )
            tl_event.add_object(
                obj=container,
                label='container',
                name=container.get_display_name(),
            )
        else:
            tl_event = None

        _redirect = redirect(request.headers.get('Referer', reverse('home')))

        if container.state not in (STATE_RUNNING, STATE_PULLING):
            if tl_event:
                tl_event.set_status(
                    TL_STATUS_FAILED,
                    'Tried to access the app while the container was not running',
                )
            messages.error(
                request, f'Container "{container.title}" not running.'
            )
            return _redirect

        if settings.KIOSC_NETWORK_MODE == 'host':
            if container.host_port:
                upstream = f'http://localhost:{container.host_port}'

            else:
                if tl_event:
                    tl_event.set_status(
                        TL_STATUS_FAILED,
                        'The host port is not set, please update the container.',
                    )
                messages.error(request, 'Host port not set.')
                return _redirect

        else:
            upstream = (
                f'http://{container.container_ip}:{container.container_port}'
            )

        self.upstream = upstream
        self.suppress_empty_body = True

        try:
            res = super().dispatch(request, *args, **kwargs)
            container.date_last_access = timezone.now()
            container.save()
            if tl_event:
                tl_event.set_status(TL_STATUS_OK)
            return res

        except MaxRetryError:
            if tl_event:
                tl_event.set_status(
                    TL_STATUS_FAILED,
                    'The app is not ready to take connections, please wait a moment.',
                )
            # The upstream app in the container is not ready yet
            # XXX: Maybe we should use a custom header instead of custom return code
            return render(
                request,
                'containers/container_proxylobby.html',
                {'object': container, 'waiting_phrases': LOBBY_WAITING_PHRASES},
                status=299,
            )
        except NewConnectionError as e:
            logger.error(f'Connection error in proxy: {e}')
            if tl_event:
                tl_event.set_status(
                    TL_STATUS_FAILED, f'Error connecting to the app: {e}'
                )
            messages.error(
                request,
                f"Web-interface of container '{container.title}' not reachable.",
            )
            return _redirect


class FileServeView(View):
    """View for serving file to a container.

    Code mostly copied from ``filesfolders.views.FileServeView``.
    """

    def get(self, *args, **kwargs):
        """GET request to return the file as attachment"""

        # Get File object
        try:
            file = File.objects.get(sodar_uuid=kwargs['file'])

        except File.DoesNotExist:
            return HttpResponseNotFound()

        # Check access
        for k in (
            'HTTP_X_FORWARDED_FOR',
            'X_FORWARDED_FOR',
            'FORWARDED',
            'REMOTE_ADDR',
        ):
            v = self.request.META.get(k)
            if v:
                client_ip = ip_address(v.split(',')[0])
                break

        else:  # Can't fetch client ip address
            logger.error("Requester is unknown. Can't check permissions.")
            return HttpResponseForbidden()  # can't identify requester

        try:
            Container.objects.get(
                project=file.project,
                container_ip=client_ip,
            )
        except Container.DoesNotExist:
            logger.error(
                'Container with IP {} does not belong to the project {} the file {} is in. Access denied!'.format(
                    client_ip, file.project.sodar_uuid, file.name
                )
            )
            return HttpResponseForbidden()  # no permission

        # Get corresponding FileData object with file content
        try:
            file_data = FileData.objects.get(file_name=file.file.name)

        except FileData.DoesNotExist:
            return HttpResponseNotFound()

        # Open file for serving
        try:
            file_content = storage.open(file_data.file_name)

        except Exception:
            return HttpResponseBadRequest()

        # Return file as attachment
        return HttpResponse(
            FileWrapper(file_content), content_type=file_data.content_type
        )


class ContainerGetDynamicDetailsApiView(
    LoggedInPermissionMixin,
    LoginRequiredMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """AJAX view for getting Docker status and logs of a container."""

    permission_required = 'containers.view_container'
    model = Container
    slug_url_kwarg = 'container'
    slug_field = 'sodar_uuid'

    def get(self, *args, **kwargs):
        container = self.get_object()
        last_job = container.containerbackgroundjob.last()
        last_action = last_job.action if last_job else None
        log_lines = int(
            self.request.GET.get('log_lines', KIOSC_CONTAINER_DEFAULT_LOG_LINES)
        )
        logs = ''

        if log_lines > 0:
            logs = container.log_entries.get_logs_as_str(
                user=self.request.user,
                log_lines=log_lines,
            )

        response = {
            'state': container.state,
            'state_color': colorize_state(container.state),
            'state_bell': state_bell(container.state, last_action),
            'logs': logs,
            'container_id': container.container_id,
            'container_ip': container.container_ip,
            'date_last_docker_log': container.log_entries.get_date_last_docker_log(),
        }

        if last_job:
            response['retries'] = last_job.retries

        return JsonResponse(response)
