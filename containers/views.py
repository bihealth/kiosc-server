import logging
from ipaddress import ip_address
from wsgiref.util import FileWrapper

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseForbidden,
    JsonResponse,
)

from bgjobs.models import BackgroundJob, LOG_LEVEL_DEBUG
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
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

from config.settings.base import KIOSC_CONTAINER_DEFAULT_LOG_LINES
from containers.templatetags.container_tags import colorize_state, state_bell
from filesfolders.models import File, FileData
from filesfolders.views import storage
from projectroles.plugins import PluginAPI
from projectroles.views import (
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)
from revproxy.views import ProxyView
from urllib3.exceptions import NewConnectionError

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
    PROCESS_ACTION,
    PROCESS_PROXY,
    STATE_PAUSED,
    STATE_RUNNING,
    STATE_DELETED,
    STATE_INITIAL,
    LOG_LEVEL_ERROR,
)
from containers.tasks import container_task
from containertemplates.forms import ContainerTemplateSelectorForm


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()

APP_NAME = "containers"
CELERY_SUBMIT_COUNTDOWN = 0.5


class ContainerCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """View for creating a container."""

    permission_required = "containers.create_container"
    template_name = "containers/container_form.html"
    form_class = ContainerForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["containertemplate_form"] = ContainerTemplateSelectorForm(
            auto_id="containertemplate_%s", user=self.request.user
        )

        if settings.KIOSC_EMBEDDED_FILES:
            context["files_form"] = FileSelectorForm(project=self.get_project())

        return context

    def get_initial(self):
        """Set hidden project field."""
        initial = super().get_initial()
        initial["project"] = self.get_project()
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = plugin_api.get_backend_api("timeline_backend")

        # Add timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="create_container",
                description="created {container}",
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object,
                label="container",
                name=self.object.get_display_name(),
            )

        # Add container log entry
        self.object.log_entries.create(
            text="Created",
            process=PROCESS_OBJECT,
            user=self.request.user,
        )

        return response


class ContainerDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DeleteView,
):
    """View for deleting a container."""

    permission_required = "containers.delete_container"
    template_name = "containers/container_confirm_delete.html"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get_success_url(self):
        messages.success(
            self.request,
            "Container deleted.",
        )
        return reverse(
            "containers:list",
            kwargs={"project": self.object.project.sodar_uuid},
        )

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        timeline = plugin_api.get_backend_api("timeline_backend")
        container = self.get_object()
        project = self.get_project()

        bg_job = BackgroundJob.objects.create(
            name="Delete container",
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_DELETE,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Add container log entry
        container.log_entries.create(
            text="Delete",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # No async task
        container_task(job_id=job.id)
        container.refresh_from_db()

        if container.state not in (STATE_INITIAL, STATE_DELETED):
            # Add timeline event
            if timeline:
                timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=request.user,
                    event_name="delete_container",
                    description=f"deleting of {container.get_display_name()} failed",
                    status_type=timeline.TL_STATUS_FAILED,
                )

            messages.error(
                request,
                f"Failed deleting container {container.get_display_name()}",
            )

            return redirect(
                reverse(
                    "containers:list",
                    kwargs={"project": project.sodar_uuid},
                )
            )

        # Add timeline event
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name="delete_container",
                description=f"deleted {container.get_display_name()}",
                status_type=timeline.TL_STATUS_OK,
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

    permission_required = "containers.edit_container"
    template_name = "containers/container_form.html"
    form_class = ContainerForm
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get_initial(self):
        initial = super().get_initial()
        initial["environment"] = self.object.get_environment_masked()
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["containertemplate_form"] = ContainerTemplateSelectorForm(
            auto_id="containertemplate_%s", user=self.request.user
        )

        if settings.KIOSC_EMBEDDED_FILES:
            context["files_form"] = FileSelectorForm(project=self.get_project())

        return context

    def get_success_url(self):
        if self.object.state not in (STATE_RUNNING, STATE_PAUSED):
            return super().get_success_url()

        messages.success(
            self.request,
            "Container updated and restarted.",
        )
        return reverse(
            "containers:restart",
            kwargs={"container": self.object.sodar_uuid},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = plugin_api.get_backend_api("timeline_backend")

        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="update_container",
                description="updated {container}",
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object,
                label="container",
                name=self.object.get_display_name(),
            )

        # Add container log entry
        self.object.log_entries.create(
            text="Updated",
            process=PROCESS_OBJECT,
            user=self.request.user,
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

    permission_required = "containers.view_container"
    template_name = "containers/container_list.html"
    model = Container
    slug_url_kwarg = "project"
    slug_field = "sodar_uuid"


class ContainerDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """View for details of container."""

    permission_required = "containers.view_container"
    template_name = "containers/container_detail.html"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"


class ContainerStartView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for starting a container."""

    permission_required = "containers.start_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name="Start container",
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

        # Add container log entry
        container.log_entries.create(
            text="Start",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(
            reverse(
                "containers:detail",
                kwargs={"container": container.sodar_uuid},
            )
        )


class ContainerStopView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for stopping a container."""

    permission_required = "containers.stop_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name="Stop container",
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

        # Add container log entry
        container.log_entries.create(
            text="Stop",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(
            reverse(
                "containers:detail",
                kwargs={"container": container.sodar_uuid},
            )
        )


class ContainerPauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for pausing a container."""

    permission_required = "containers.pause_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name="Pause container",
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

        # Add container log entry
        container.log_entries.create(
            text="Pause",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(
            reverse(
                "containers:detail",
                kwargs={"container": container.sodar_uuid},
            )
        )


class ContainerUnpauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for unpausing a container."""

    permission_required = "containers.unpause_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name="Unpause container",
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

        # Add container log entry
        container.log_entries.create(
            text="Unpause",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(
            reverse(
                "containers:detail",
                kwargs={"container": container.sodar_uuid},
            )
        )


class ContainerRestartView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for restarting a container."""

    permission_required = "containers.start_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()
        bg_job = BackgroundJob.objects.create(
            name="Restart container",
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

        # Add container log entry
        container.log_entries.create(
            text="Restart",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return redirect(
            reverse(
                "containers:detail",
                kwargs={"container": container.sodar_uuid},
            )
        )


class ContainerProxyLobbyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """View for proxy lobby."""

    permission_required = "containers.proxy"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"
    template_name = "containers/container_proxylobby.html"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = self.get_object()

        if container.state == STATE_RUNNING:
            return redirect(
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": container.sodar_uuid,
                        "path": container.container_path,
                    },
                )
            )

        elif container.state == STATE_PAUSED:
            action = ACTION_UNPAUSE

        else:
            action = ACTION_START

        bg_job = BackgroundJob.objects.create(
            name="Proxy lobby",
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )

        job = ContainerBackgroundJob.objects.create(
            action=action,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Add container log entry
        container.log_entries.create(
            text="Proxy lobby",
            process=PROCESS_ACTION,
            user=request.user,
        )

        container_task.apply_async(kwargs={"job_id": job.id}, countdown=0.5)

        return super().get(request, *args, **kwargs)


class KioscProxyView(ProxyView):
    """Inheriting the ProxyView to adjust settings."""

    rewrite = ((r"^/container/proxy/(?P<container>[a-f0-9-]+)/", "/"),)


class ReverseProxyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for reverse proxy."""

    permission_required = "containers.proxy"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()

        container = self.get_object()
        kwargs.pop("container")

        _redirect = redirect(
            reverse(
                "containers:list",
                kwargs={"project": container.project.sodar_uuid},
            )
        )

        if not container.state == STATE_RUNNING:
            messages.error(
                request, f"Container '{container.title}' not running."
            )
            return _redirect

        if settings.KIOSC_NETWORK_MODE == "host":
            if container.host_port:
                upstream = f"http://localhost:{container.host_port}"

            else:
                messages.error(request, "Host port not set.")
                return _redirect

        else:
            upstream = f"http://{container.container_id[:12]}:{container.container_port}"

        proxy_view = KioscProxyView()
        proxy_view.request = request
        proxy_view.args = args
        proxy_view.kwargs = kwargs
        proxy_view.upstream = upstream
        proxy_view.suppress_empty_body = True

        # Add container log entry
        container.log_entries.create(
            text=f"Accessing {upstream}",
            process=PROCESS_PROXY,
            user=request.user,
        )

        try:
            return proxy_view.dispatch(request, *args, **kwargs)

        except NewConnectionError as e:
            container.log_entries.create(
                text=str(e),
                process=PROCESS_PROXY,
                user=request.user,
                level=LOG_LEVEL_DEBUG,
            )
            container.log_entries.create(
                text=f"Access {upstream} failed",
                process=PROCESS_PROXY,
                user=request.user,
                level=LOG_LEVEL_ERROR,
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
            file = File.objects.get(sodar_uuid=kwargs["file"])

        except File.DoesNotExist:
            return HttpResponseNotFound()

        # Check access
        for k in (
            "HTTP_X_FORWARDED_FOR",
            "X_FORWARDED_FOR",
            "FORWARDED",
            "REMOTE_ADDR",
        ):
            v = self.request.META.get(k)
            if v:
                client_ip = ip_address(v.split(",")[0])
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
                "Container with IP {} does not belong to the project {} the file {} is in. Access denied!".format(
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

    permission_required = "containers.view_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, *args, **kwargs):
        container = self.get_object()
        last_job = container.containerbackgroundjob.last()
        last_action = last_job.action if last_job else None
        log_lines = int(
            self.request.GET.get("log_lines", KIOSC_CONTAINER_DEFAULT_LOG_LINES)
        )
        logs = ""

        if log_lines > 0:
            logs = container.log_entries.get_logs_as_str(
                user=self.request.user,
                log_lines=log_lines,
            )

        response = {
            "state": container.state,
            "state_color": colorize_state(container.state),
            "state_bell": state_bell(container.state, last_action),
            "logs": logs,
            "container_id": container.container_id,
            "container_ip": container.container_ip,
            "date_last_docker_log": container.log_entries.get_date_last_docker_log(),
        }

        if last_job:
            response["retries"] = last_job.retries

        return JsonResponse(response)
