# Create your views here.
from django.contrib import messages
from django.db import transaction
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
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
)

from containertemplates.forms import ContainerTemplateForm
from containertemplates.models import ContainerTemplate

APP_NAME = "containertemplates"


class ContainerTemplateCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    CreateView,
):
    """View for creating a containertemplate."""

    permission_required = "containertemplates.create"
    template_name = "containertemplates/form.html"
    form_class = ContainerTemplateForm

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        # Add timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=None,
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
        )

    def delete(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")
        obj = self.get_object()

        # Add timeline event
        if timeline:
            timeline.add_event(
                project=None,
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
                project=None,
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
    ListView,
):
    """View for listing ContainerTemplates."""

    permission_required = "containertemplates.view"
    template_name = "containertemplates/list.html"
    model = ContainerTemplate


class ContainerTemplateDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    DetailView,
):
    """View for details of containertemplate."""

    permission_required = "containertemplates.view"
    template_name = "containertemplates/detail.html"
    model = ContainerTemplate
    slug_url_kwarg = "containertemplate"
    slug_field = "sodar_uuid"


class ContainerTemplateDuplicateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    View,
):
    """View for duplicating a containertemplate."""

    permission_required = "containertemplates.duplicate"
    model = ContainerTemplate
    slug_url_kwarg = "containertemplate"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            containertemplate = get_object_or_404(
                ContainerTemplate,
                sodar_uuid=kwargs.get("containertemplate"),
            )
            data = model_to_dict(
                containertemplate, exclude=["id", "sodar_uuid"]
            )
            title_original = data["title"]
            title_new = f"{data['title']} (Duplicate)"
            counter = 1

            while ContainerTemplate.objects.filter(title=title_new).exists():
                counter += 1
                title_new = f"{title_original} (Duplicate {counter})"

            data["title"] = title_new

            try:
                ContainerTemplate.objects.create(**data)

            except Exception as e:
                messages.error(e)

            messages.success(
                request,
                f"Successfully created container template '{title_new}' from '{title_original}'",
            )

            return redirect(reverse("containertemplates:list"))
