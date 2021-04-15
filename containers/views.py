from bgjobs.models import BackgroundJob
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
from django.views.generic.detail import BaseDetailView
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
)
from containers.tasks import container_task


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

    def get_form_kwargs(self):
        """Pass current user and URL kwargs to form"""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs


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
            container = Container.objects.get(
                sodar_uuid=kwargs.get("container")
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
            container = Container.objects.get(
                sodar_uuid=kwargs.get("container")
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
            container_task.delay(job_id=job.id)

        return redirect(
            reverse(
                "containers:container-detail",
                kwargs={"container": kwargs.get("container")},
            )
        )


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

        upstream = f"http://localhost:{container.host_port}"

        proxy_view = KioscProxyView()
        proxy_view.request = request
        proxy_view.args = args
        proxy_view.kwargs = kwargs
        proxy_view.upstream = upstream
        proxy_view.suppress_empty_body = True

        return proxy_view.dispatch(request, *args, **kwargs)
