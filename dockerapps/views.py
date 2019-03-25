"""The views for the dockerapps app."""

import time

import docker
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import reverse, redirect
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)
from django.views.generic.detail import BaseDetailView
from projectroles.models import Project
from projectroles.views import LoggedInPermissionMixin, ProjectContextMixin

from kiosc.utils import ProjectPermissionMixin

from . import tasks
from .forms import DockerAppForm, DockerAppChangeStateForm
from .models import DockerApp
from .views_proxy import ProxyView

#: Smallest port to use for the Docker image.
FIRST_PORT = 1025


class DockerAppListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ListView,
):
    """Display list of all DockerApp records"""

    template_name = "dockerapps/dockerapp_list.html"
    permission_required = "dockerapps.view_dockerapp"

    model = DockerApp

    def get_queryset(self):
        return super().get_queryset().filter(project__sodar_uuid=self.kwargs["project"])


class DockerAppDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display detail of DockerApp records"""

    template_name = "dockerapps/dockerapp_detail.html"
    permission_required = "dockerapps.view_dockerapp"

    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"


class DockerAppCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """Display list of all DockerApp records"""

    template_name = "dockerapps/dockerapp_create.html"
    permission_required = "dockerapps.add_dockerapp"

    model = DockerApp
    form_class = DockerAppForm

    @transaction.atomic
    def form_valid(self, form):
        """Automatically set the project property."""
        form.instance.project = self.get_project(self.request, self.kwargs)
        # Find a free port...
        docker_apps = DockerApp.objects.order_by("-host_port")
        form.instance.host_port = docker_apps.first().host_port + 1 if docker_apps else FIRST_PORT
        if form.cleaned_data.get("docker_image"):
            # Load the image into Docker
            images = docker.from_env(timeout=300).images.load(form.cleaned_data["docker_image"])
            if len(images) != 1:
                raise ValidationError("The TAR file has to contain exactly one image")
            form.instance.image_id = images[0].id
        try:
            result = super().form_valid(form)
        except ValidationError:  # Remove image and re-raise
            docker.from_env(timeout=300).images.remove(images[0].id)
        return result


class DockerAppUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """Updating of DockerApp records"""

    template_name = "dockerapps/dockerapp_update.html"
    permission_required = "dockerapps.change_dockerapp"

    model = DockerApp
    form_class = DockerAppForm

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def form_valid(self, form):
        # Stop any running container.
        stop_containers(form.instance.image_id)
        if form.cleaned_data.get("docker_image"):
            # Load the image into Docker
            images = docker.from_env(timeout=300).images.load(form.cleaned_data["docker_image"])
            if len(images) != 1:
                raise ValidationError("The TAR file has to contain exactly one image")
            form.instance.image_id = images[0].id
        try:
            result = super().form_valid(form)
        except ValidationError:  # Remove image and re-raise
            docker.from_env(timeout=300).images.remove(images[0].id)
        return result


def stop_containers(image_id):
    """Stop containers for ``image_id``."""
    client = docker.from_env()
    for container in client.containers.list():
        if container.image.id == image_id:
            container.stop()
            return True
    return False


class DockerAppChangeStateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """Starting and stopping of docker containers"""

    template_name = "dockerapps/dockerapp_update.html"  # actually not used
    permission_required = "dockerapps.change_dockerapp"

    model = DockerApp
    form_class = DockerAppChangeStateForm

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"

    def form_valid(self, form):
        # Kick off starting/stopping
        with transaction.atomic():
            if form.cleaned_data["action"] == "start":
                form.instance.state = "starting"
                client = docker.from_env(timeout=300)
                client.containers.run(
                    form.instance.image_id,
                    detach=True,
                    ports={"%d/tcp" % form.instance.internal_port: form.instance.host_port},
                    environment={
                        "DASH_REQUESTS_PATHNAME_PREFIX": reverse(
                            "dockerapps:dockerapp-proxy",
                            kwargs={
                                "project": self.get_context_data()["project"].sodar_uuid,
                                "dockerapp": self.get_context_data()["object"].sodar_uuid,
                                "path": "",
                            },
                        )
                    },
                )
                messages.info(self.request, "Initiated start of docker container...")
            elif form.cleaned_data["action"] == "stop":
                form.instance.state = "stopping"
                if stop_containers(form.instance.image_id):
                    messages.info(self.request, "Initiated stop of docker container...")
            # Update docker app record.
            super().form_valid(form)

        tasks.update_container_states.delay()
        return redirect(
            reverse(
                "dockerapps:dockerapp-list",
                kwargs={"project": self.get_context_data()["project"].sodar_uuid},
            )
        )


class DockerAppUpdateStateView(
    LoginRequiredMixin, LoggedInPermissionMixin, ProjectPermissionMixin, ProjectContextMixin, View
):
    """Starting and stopping of docker containers"""

    permission_required = "dockerapps.change_dockerapp"

    def post(self, *args, **kwargs):
        tasks.update_container_states.delay()
        messages.info(
            self.request,
            "Refreshing container states. You might have to reload the page to see the results",
        )
        return redirect(reverse("dockerapps:dockerapp-list", kwargs={"project": kwargs["project"]}))


class DockerAppDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DeleteView,
):
    """Deletion of DockerApp records"""

    template_name = "dockerapps/dockerapp_confirm_delete.html"
    permission_required = "dockerapps.delete_dockerapp"

    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"

    @transaction.atomic
    def delete(self, *args, **kwargs):
        # Delete docker app record.
        result = super().delete(*args, **kwargs)
        return result

    def get_success_url(self):
        return reverse(
            "dockerapps:dockerapp-list",
            kwargs={"project": self.get_project(self.request, self.kwargs).sodar_uuid},
        )


class DockerProxyView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    BaseDetailView,
):
    permission_required = "dockerapps.view_dockerapp"

    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        kwargs.pop("project")
        kwargs.pop("dockerapp")
        upstream = "http://localhost:%d/" % self.get_object().host_port
        # Hand down into ProxyView
        proxy_view = ProxyView()
        proxy_view.request = request
        proxy_view.args = args
        proxy_view.kwargs = kwargs
        proxy_view.upstream = upstream
        proxy_view.suppress_empty_body = True
        proxy_view.rewrite = (
            (r"^/^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/proxy/^", r"/"),
        )
        return proxy_view.dispatch(request, *args, **kwargs)


class DockerAppRunView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display detail of DockerApp records"""

    template_name = "dockerapps/dockerapp_run.html"
    permission_required = "dockerapps.view_dockerapp"

    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"
