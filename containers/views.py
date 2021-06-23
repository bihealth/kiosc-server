from bgjobs.models import BackgroundJob
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import (
    DeleteView,
    UpdateView,
    DetailView,
    CreateView,
    ListView,
)
from django.views.generic.detail import BaseDetailView
from projectroles.plugins import get_backend_api
from projectroles.views import (
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)
from revproxy.views import ProxyView

from containers.forms import ContainerForm
from containers.models import (
    Container,
    ContainerBackgroundJob,
    ACTION_START,
    ACTION_STOP,
    PROCESS_OBJECT,
    PROCESS_ACTION,
    PROCESS_PROXY,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    ACTION_RESTART,
    STATE_PAUSED,
    STATE_RUNNING,
)
from containers.tasks import container_task


APP_NAME = "containers"


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

    def get_initial(self):
        """Set hidden project field."""
        initial = super().get_initial()
        initial["project"] = self.get_project()
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        # Add timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="create_container",
                description="created {container}",
                status_type="OK",
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
            "containers:container-list",
            kwargs={"project": self.object.project.sodar_uuid},
        )

    def delete(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")
        obj = self.get_object()
        project = self.get_project()

        # Add timeline event
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name="delete_container",
                description=f"deleted {obj.get_display_name()}",
                status_type="OK",
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

    def get_success_url(self):
        if self.object.state not in (STATE_RUNNING, STATE_PAUSED):
            return super().get_success_url()

        messages.success(
            self.request,
            "Container updated and restarted.",
        )
        return reverse(
            "containers:container-restart",
            kwargs={
                "container": self.object.sodar_uuid,
            },
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="update_container",
                description="updated {container}",
                status_type="OK",
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
    View,
):
    """View for starting a container."""

    permission_required = "containers.start_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )
            bg_job = BackgroundJob.objects.create(
                name="Start container",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
            )
            job = ContainerBackgroundJob.objects.create(
                action=ACTION_START,
                project=project,
                container=container,
                bg_job=bg_job,
            )

            # Add container log entry
            container.log_entries.create(
                text="Starting",
                process=PROCESS_ACTION,
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


class ContainerStopView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    View,
):
    """View for stopping a container."""

    permission_required = "containers.stop_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )
            bg_job = BackgroundJob.objects.create(
                name="Start container",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
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
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


class ContainerPauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    View,
):
    """View for pausing a container."""

    permission_required = "containers.pause_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )
            bg_job = BackgroundJob.objects.create(
                name="Pause container",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
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
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


class ContainerUnpauseView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    View,
):
    """View for unpausing a container."""

    permission_required = "containers.unpause_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )
            bg_job = BackgroundJob.objects.create(
                name="Unpause container",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
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
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


class ContainerRestartView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    View,
):
    """View for restarting a container."""

    permission_required = "containers.start_container"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )
            bg_job = BackgroundJob.objects.create(
                name="Restart container",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
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
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


class ContainerProxyLobbyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    View,
):
    """View for proxy lobby."""

    permission_required = "containers.proxy"
    model = Container
    slug_url_kwarg = "container"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        _redirect = redirect(
            reverse(
                "containers:proxy",
                kwargs={
                    "container": kwargs.get("container"),
                    "path": kwargs.get("path"),
                },
            )
        )

        with transaction.atomic():
            project = self.get_project()
            user = request.user
            container = get_object_or_404(
                Container, sodar_uuid=kwargs.get("container")
            )

            if container.state == STATE_RUNNING:
                return _redirect

            elif container.state == STATE_PAUSED:
                action = ACTION_UNPAUSE

            else:
                action = ACTION_START

            bg_job = BackgroundJob.objects.create(
                name="Proxy lobby",
                project=project,
                job_type=ContainerBackgroundJob.spec_name,
                user=user,
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
                user=self.request.user,
            )

            # Schedule task
            container_task.delay(job_id=job.id)

        return _redirect


class KioscProxyView(ProxyView):
    """Inheriting the ProxyView to adjust settings."""

    rewrite = ((r"^/container/proxy/(?P<container>[a-f0-9-]+)/", "/"),)


class ReverseProxyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    BaseDetailView,
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
                "containers:container-list",
                kwargs={
                    "project": container.project.sodar_uuid,
                },
            )
        )

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

        except Exception as e:
            messages.error(request, e)
            return _redirect
