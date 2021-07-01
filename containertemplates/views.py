# Create your views here.
from django.contrib import messages
from django.db import transaction
from django.forms import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    UpdateView,
    ListView,
    DetailView,
)
from django.views.generic.detail import SingleObjectMixin
from projectroles.plugins import get_backend_api
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)

from containertemplates.forms import (
    ContainerTemplateSiteForm,
    ContainerTemplateProjectForm,
)
from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)


APP_NAME = "containertemplates"


class ContainerTemplateSiteCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    CreateView,
):
    """View for creating a site-wide containertemplate."""

    permission_required = "containertemplates.site_create"
    template_name = "containertemplates/site_form.html"
    form_class = ContainerTemplateSiteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        # Add timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=self.request.user,
                event_name="create_containertemplate_site",
                description="created {containertemplate}",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateSiteDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    DeleteView,
):
    """View for deleting a site-wide containertemplate."""

    permission_required = "containertemplates.site_delete"
    template_name = "containertemplates/site_confirm_delete.html"
    model = ContainerTemplateSite
    slug_url_kwarg = "containertemplatesite"
    slug_field = "sodar_uuid"

    def get_success_url(self):
        messages.success(
            self.request,
            "ContainerTemplate deleted.",
        )
        return reverse(
            "containertemplates:site-list",
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
                event_name="delete_containertemplate_site",
                description=f"deleted {obj.get_display_name()}",
                status_type="OK",
            )

        return super().delete(request, *args, **kwargs)


class ContainerTemplateSiteUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    UpdateView,
):
    """View for updating a site-wide ContainerTemplate."""

    permission_required = "containertemplates.site_edit"
    template_name = "containertemplates/site_form.html"
    form_class = ContainerTemplateSiteForm
    model = ContainerTemplateSite
    slug_url_kwarg = "containertemplatesite"
    slug_field = "sodar_uuid"

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        if timeline:
            tl_event = timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=self.request.user,
                event_name="update_containertemplate_site",
                description="updated {containertemplate}",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateSiteListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ListView,
):
    """View for listing site-wide ContainerTemplates."""

    permission_required = "containertemplates.site_view"
    template_name = "containertemplates/site_list.html"
    model = ContainerTemplateSite


class ContainerTemplateSiteDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    DetailView,
):
    """View for details of site-wide containertemplate."""

    permission_required = "containertemplates.site_view"
    template_name = "containertemplates/site_detail.html"
    model = ContainerTemplateSite
    slug_url_kwarg = "containertemplatesite"
    slug_field = "sodar_uuid"


class ContainerTemplateSiteDuplicateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    SingleObjectMixin,
    View,
):
    """View for duplicating a site-wide containertemplate."""

    permission_required = "containertemplates.site_duplicate"
    model = ContainerTemplateSite
    slug_url_kwarg = "containertemplatesite"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")
        obj = self.get_object()
        _redirect = redirect(reverse("containertemplates:site-list"))

        with transaction.atomic():
            if timeline:
                tl_event = timeline.add_event(
                    project=None,
                    app_name=APP_NAME,
                    user=self.request.user,
                    event_name="duplicate_containertemplate_site",
                    description="duplicated {containertemplate} site-wide",
                    status_type="OK",
                )
                tl_event.add_object(
                    obj=obj,
                    label="containertemplate",
                    name=obj.get_display_name(),
                )

            data = model_to_dict(obj, exclude=["id", "sodar_uuid"])
            title_original = data["title"]
            title_new = f"{data['title']} (Duplicate)"
            counter = 1

            while ContainerTemplateSite.objects.filter(
                title=title_new
            ).exists():
                counter += 1
                title_new = f"{title_original} (Duplicate {counter})"

            data["title"] = title_new

            try:
                ContainerTemplateSite.objects.create(**data)

            except Exception as e:
                messages.error(request, e)
                return _redirect

            messages.success(
                request,
                f"Successfully created container template '{title_new}' from '{title_original}'",
            )

            return _redirect


class ContainerTemplateProjectCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    CreateView,
):
    """View for creating a project-wide containertemplate."""

    permission_required = "containertemplates.project_create"
    template_name = "containertemplates/project_form.html"
    form_class = ContainerTemplateProjectForm

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
                event_name="create_containertemplate_project",
                description="created {containertemplate} project-wide",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateProjectDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DeleteView,
):
    """View for deleting a project-wide containertemplate."""

    permission_required = "containertemplates.project_delete"
    template_name = "containertemplates/project_confirm_delete.html"
    model = ContainerTemplateProject
    slug_url_kwarg = "containertemplateproject"
    slug_field = "sodar_uuid"

    def get_success_url(self):
        messages.success(
            self.request,
            "ContainerTemplate deleted.",
        )
        return reverse(
            "containertemplates:project-list",
            kwargs={"project": self.get_project().sodar_uuid},
        )

    def delete(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")

        # Add timeline event
        if timeline:
            timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=request.user,
                event_name="delete_containertemplate_project",
                description=f"deleted {self.get_object().get_display_name()} project-wide",
                status_type="OK",
            )

        return super().delete(request, *args, **kwargs)


class ContainerTemplateProjectUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    UpdateView,
):
    """View for updating a project-wide containertemplate."""

    permission_required = "containertemplates.project_edit"
    template_name = "containertemplates/project_form.html"
    form_class = ContainerTemplateProjectForm
    model = ContainerTemplateProject
    slug_url_kwarg = "containertemplateproject"
    slug_field = "sodar_uuid"

    def get_initial(self):
        """Set hidden project field."""
        initial = super().get_initial()
        initial["project"] = self.get_project()
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        timeline = get_backend_api("timeline_backend")

        if timeline:
            tl_event = timeline.add_event(
                project=self.get_project(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name="update_containertemplate_project",
                description="updated {containertemplate} project-wide",
                status_type="OK",
            )
            tl_event.add_object(
                obj=self.object,
                label="containertemplate",
                name=self.object.get_display_name(),
            )

        return response


class ContainerTemplateProjectListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    ListView,
):
    """View for listing project-wide containertemplate."""

    permission_required = "containertemplates.project_view"
    template_name = "containertemplates/project_list.html"
    model = ContainerTemplateProject
    slug_url_kwarg = "project"
    slug_field = "sodar_uuid"


class ContainerTemplateProjectDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    DetailView,
):
    """View for details of project-wide containertemplate."""

    permission_required = "containertemplates.project_view"
    template_name = "containertemplates/project_detail.html"
    model = ContainerTemplateProject
    slug_url_kwarg = "containertemplateproject"
    slug_field = "sodar_uuid"


class ContainerTemplateProjectDuplicateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    SingleObjectMixin,
    View,
):
    """View for duplicating a project-wide containertemplate."""

    permission_required = "containertemplates.project_duplicate"
    model = ContainerTemplateProject
    slug_url_kwarg = "containertemplateproject"
    slug_field = "sodar_uuid"

    def get(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")
        obj = self.get_object()
        _redirect = redirect(
            reverse(
                "containertemplates:project-list",
                kwargs={"project": obj.project.sodar_uuid},
            )
        )

        with transaction.atomic():
            if timeline:
                tl_event = timeline.add_event(
                    project=obj.project,
                    app_name=APP_NAME,
                    user=self.request.user,
                    event_name="duplicate_containertemplate_site",
                    description="duplicated {containertemplate} site-wide",
                    status_type="OK",
                )
                tl_event.add_object(
                    obj=obj,
                    label="containertemplate",
                    name=obj.get_display_name(),
                )

            data = model_to_dict(obj, exclude=["id", "sodar_uuid", "project"])
            title_original = data["title"]
            title_new = f"{data['title']} (Duplicate)"
            counter = 1

            while ContainerTemplateProject.objects.filter(
                title=title_new
            ).exists():
                counter += 1
                title_new = f"{title_original} (Duplicate {counter})"

            data["title"] = title_new
            data["project"] = obj.project

            try:
                ContainerTemplateProject.objects.create(**data)

            except Exception as e:
                messages.error(request, e)
                return _redirect

            messages.success(
                request,
                f"Successfully created container template '{title_new}' from '{title_original}'",
            )

            return _redirect
