# Create your views here.
from django.contrib import messages
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    UpdateView,
    ListView,
    DetailView,
)
from projectroles.plugins import get_backend_api
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
)

from containertemplates.forms import ContainerTemplateForm
from containertemplates.models import ContainerTemplate

APP_NAME = "containertemplates"


class ContainerTemplateCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """View for creating a containertemplate."""

    permission_required = "containertemplates.create"
    template_name = "containertemplates/form.html"
    form_class = ContainerTemplateForm

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
                event_name="create_containertemplate",
                description="created {containertemplate}",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DeleteView,
):
    """View for deleting a containertemplate."""

    permission_required = "containertemplates.delete"
    template_name = "containertemplates/confirm_delete.html"
    model = ContainerTemplate
    slug_url_kwarg = "containertemplate"
    slug_field = "sodar_uuid"

    def get_success_url(self):
        messages.success(
            self.request,
            "ContainerTemplate deleted.",
        )
        return reverse(
            "containertemplates:list",
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
                event_name="delete_containertemplate",
                description=f"deleted {obj.get_display_name()}",
                status_type="OK",
            )

        return super().delete(request, *args, **kwargs)


class ContainerTemplateUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """View for updating a ContainerTemplate."""

    permission_required = "containertemplates.edit"
    template_name = "containertemplates/form.html"
    form_class = ContainerTemplateForm
    model = ContainerTemplate
    slug_url_kwarg = "containertemplate"
    slug_field = "sodar_uuid"

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="update_containertemplate",
                description="updated {containertemplate}",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ListView,
):
    """View for listing ContainerTemplates."""

    permission_required = "containertemplates.view"
    template_name = "containertemplates/list.html"
    model = ContainerTemplate
    slug_url_kwarg = "project"
    slug_field = "sodar_uuid"


class ContainerTemplateDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """View for details of containertemplate."""

    permission_required = "containertemplates.view"
    template_name = "containertemplates/detail.html"
    model = ContainerTemplate
    slug_url_kwarg = "containertemplate"
    slug_field = "sodar_uuid"
