"""The views for the dockerapps app."""

import time

import docker
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.detail import BaseDetailView
from projectroles.models import Project
from projectroles.views import LoggedInPermissionMixin, ProjectContextMixin

from kiosc.utils import ProjectPermissionMixin

from .forms import DockerAppForm
from .models import DockerApp
from .views_proxy import ProxyView


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
        # Create the docker app.
        form.instance.project = self.get_project(self.request, self.kwargs)
        result = super().form_valid(form)
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
        # Update docker app record.
        result = super().form_valid(form)
        return result


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
    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"

    @classmethod
    def as_view(cls, **kwargs):
        """Override here to get CSRF exemption..."""
        view = super(BaseDetailView, cls).as_view(**kwargs)
        view.csrf_exempt = True
        return view

    def dispatch(self, request, *args, **kwargs):
        project = Project.objects.get(sodar_uuid=kwargs.pop("project"))
        # TODO: perform project-based access check
        upstream = "http://localhost:%d/" % self._get_container_port(kwargs.pop("dockerapp"))
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

    def _get_container_port(self, dockerapp_sodar_uuid):
        """Get port for container, start container if necessary.
        """
        dockerapp = DockerApp.objects.get(sodar_uuid=dockerapp_sodar_uuid)
        client = docker.from_env()
        for container in client.containers.list():
            if container.image.id == dockerapp.image_id:
                break
        else:
            container = client.containers.run(
                dockerapp.image_id, detach=True, ports={"3838/tcp": 3838}
            )
            time.sleep(5)  # TODO: rather wait for up to 5 seconds for a connection on the port
        low_level_client = docker.APIClient(base_url="unix://var/run/docker.sock")
        port_data = low_level_client.inspect_container(container.id)["NetworkSettings"]["Ports"]
        return int(list(port_data.keys())[0].split("/")[0])
