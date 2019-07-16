"""The views for the dockerapps app."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import reverse, redirect, get_object_or_404
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, FormView
from django.views.generic.detail import BaseDetailView
from projectroles.views import LoggedInPermissionMixin, ProjectContextMixin

from dockerapps.tasks import pull_image, control_container_state
from kiosc.utils import ProjectPermissionMixin

from .forms import DockerImageForm, DockerProcessJobControlForm, DockerImagePullForm
from .models import (
    DockerImage,
    DockerProcess,
    ImageBackgroundJob,
    ContainerStateControlBackgroundJob,
)
from .views_proxy import ProxyView


class DockerImageListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ListView,
):
    """Display list of all DockerImage records"""

    template_name = "dockerapps/dockerimage_list.html"
    permission_required = "dockerapps.view_dockerimage"

    model = DockerImage

    def get_queryset(self):
        return super().get_queryset().filter(project__sodar_uuid=self.kwargs["project"])


class DockerImageDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display detail of DockerImage records"""

    template_name = "dockerapps/dockerimage_detail.html"
    permission_required = "dockerapps.view_dockerimage"

    model = DockerImage

    slug_url_kwarg = "image"
    slug_field = "sodar_uuid"


class DockerImageCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """Display list of all DockerImage records"""

    template_name = "dockerapps/dockerimage_create.html"
    permission_required = "dockerapps.add_dockerimage"

    model = DockerImage
    form_class = DockerImageForm

    def get_form_kwargs(self):
        """Extend form kwargs with the project."""
        result = super().get_form_kwargs()
        result["project"] = self.get_project()
        result["internal_port"] = None
        result["env_vars"] = []
        result["command"] = None
        return result

    def form_valid(self, form):
        result = super().form_valid(form)
        bgjob = ImageBackgroundJob.construct(self.object, self.request.user, "pull_image")
        pull_image.delay(bgjob.pk)
        return result


class DockerImageUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """Updating of DockerImage records"""

    template_name = "dockerapps/dockerimage_update.html"
    permission_required = "dockerapps.change_dockerimage"

    model = DockerImage
    form_class = DockerImageForm

    slug_url_kwarg = "image"
    slug_field = "sodar_uuid"

    def get_form_kwargs(self):
        """Extend form kwargs with the project."""
        result = super().get_form_kwargs()
        result["project"] = self.get_project()
        result["internal_port"] = self.object.dockerprocess_set.first().internal_port
        result["env_vars"] = self.object.dockerprocess_set.first().environment
        result["command"] = self.object.dockerprocess_set.first().command
        return result

    def form_valid(self, form):
        result = super().form_valid(form)
        bgjob = ImageBackgroundJob.construct(self.object, self.request.user, "pull_image")
        pull_image.delay(bgjob.pk)
        return result


class DockerImageJobControlView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """Starting and stopping of docker containers"""

    template_name = "dockerapps/dockerimage_update.html"  # actually not used
    permission_required = "dockerapps.change_dockerimage"

    model = DockerImage
    form_class = DockerProcessJobControlForm

    slug_url_kwarg = "image"
    slug_field = "sodar_uuid"

    def form_valid(self, form):
        # Kick off starting/stopping
        if form.cleaned_data["action"] in ("start", "restart", "stop"):
            messages.info(self.request, "Initiating %s of container" % form.cleaned_data["action"])
            job = ContainerStateControlBackgroundJob.construct(
                self.get_object().process, self.request.user, form.cleaned_data["action"]
            )
            control_container_state.delay(job.pk)
        else:
            messages.error(self.request, "Invalid action %s" % form.cleaned_data["action"])

        return redirect(
            reverse(
                "dockerapps:image-list",
                kwargs={"project": self.get_context_data()["project"].sodar_uuid},
            )
        )


class DockerImageDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DeleteView,
):
    """Deletion of DockerImage records"""

    template_name = "dockerapps/dockerimage_confirm_delete.html"
    permission_required = "dockerapps.delete_dockerimage"

    model = DockerImage

    slug_url_kwarg = "image"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def delete(self, *args, **kwargs):
        # Delete docker app record.
        result = super().delete(*args, **kwargs)
        return result

    def get_success_url(self):
        return reverse(
            "dockerapps:image-list",
            kwargs={"project": self.get_project(self.request, self.kwargs).sodar_uuid},
        )


class DockerImagePullView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    FormView,
):
    """Pull docker image again"""

    template_name = "dockerapps/dockerimage_confirm_pull.html"
    permission_required = "dockerapps.update_dockerimage"

    form_class = DockerImagePullForm

    slug_url_kwarg = "image"
    slug_field = "sodar_uuid"

    def get_context_data(self, *args, **kwargs):
        result = super().get_context_data(*args, **kwargs)
        result["object"] = get_object_or_404(
            DockerImage.objects.filter(project=result["project"]), sodar_uuid=self.kwargs["image"]
        )
        return result

    def form_valid(self, form):
        image = self.get_context_data()["object"]
        bgjob = ImageBackgroundJob.construct(image, self.request.user, "pull_image")
        pull_image.delay(bgjob.pk)
        messages.info(
            self.request, "Pulling Docker image %s:%s again" % (image.repository, image.tag)
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "dockerapps:image-list",
            kwargs={"project": self.get_project(self.request, self.kwargs).sodar_uuid},
        )


class ImageBackgroundJobDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display status and further details of the image background job.
    """

    permission_required = "dockerapps.view_data"
    template_name = "dockerapps/image_job_detail.html"
    model = ImageBackgroundJob
    slug_url_kwarg = "job"
    slug_field = "sodar_uuid"


class ContainerStateControlBackgroundJobDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display status and further details of the image background job.
    """

    permission_required = "dockerapps.view_data"
    template_name = "dockerapps/container_job_detail.html"
    model = ContainerStateControlBackgroundJob
    slug_url_kwarg = "job"
    slug_field = "sodar_uuid"


class DockerProxyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    BaseDetailView,
):
    permission_required = "dockerapps.view_dockerimage"

    model = DockerProcess

    slug_url_kwarg = "process"
    slug_field = "sodar_uuid"

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        kwargs.pop("project")
        kwargs.pop("image")
        kwargs.pop("process")
        upstream = "http://localhost:%d/" % self.get_object().host_port
        # Hand down into ProxyView
        proxy_view = ProxyView()
        proxy_view.request = request
        proxy_view.args = args
        proxy_view.kwargs = kwargs
        proxy_view.upstream = upstream
        proxy_view.suppress_empty_body = True
        proxy_view.rewrite = (
            (
                r"^/^(?P<project>[0-9a-f-]+)/dockerapps/(?P<image>[0-9a-f-]+)/proxy/(?P<process>[0-9a-f-]+)/^",
                r"/",
            ),
        )
        return proxy_view.dispatch(request, *args, **kwargs)
