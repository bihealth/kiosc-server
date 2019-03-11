"""The views for the dockerapps app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from projectroles.plugins import get_backend_api
from projectroles.views import LoggedInPermissionMixin, ProjectContextMixin

from kiosc.utils import ProjectPermissionMixin

from .forms import DockerAppForm
from .models import DockerApp


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


class DockerAppRunView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """Display embedded docker app"""

    template_name = "dockerapps/dockerapp_run.html"
    permission_required = "dockerapps.view_dockerapp"

    model = DockerApp

    slug_url_kwarg = "dockerapp"
    slug_field = "sodar_uuid"
