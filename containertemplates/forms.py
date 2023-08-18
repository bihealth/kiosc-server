from itertools import chain

from django import forms

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)

fields = [
    "title",
    "description",
    "container_port",
    "container_path",
    "heartbeat_url",
    "timeout",
    "environment",
    "command",
    "repository",
    "tag",
    "max_retries",
    "inactivity_threshold",
]


class ContainerTemplateSiteForm(forms.ModelForm):
    """ModelForm for creating and updating containertemplate."""

    class Meta:
        model = ContainerTemplateSite
        fields = fields


class ContainerTemplateProjectForm(forms.ModelForm):
    """ModelForm for creating and updating containertemplate."""

    class Meta:
        model = ContainerTemplateProject
        fields = [
            *fields,
            "project",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hide project field
        self.fields["project"].widget = forms.HiddenInput()


class ContainerTemplateSelectorForm(forms.Form):
    """Form for copying a site-wide containertemplate to a project."""

    #: Source template to copy
    source = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={"class": "form-control", "style": "width: 400px"}
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")

        super().__init__(*args, **kwargs)

        queryset_site = ContainerTemplateSite.objects.all()
        queryset_project = ContainerTemplateProject.objects.all()

        if not user.is_superuser:
            queryset_project = [
                p for p in queryset_project if p.project.has_role(user)
            ]

        choices_project = [
            (f"project:{obj.id}", f"[Project-wide] {obj.get_display_name()}")
            for obj in queryset_project
        ]
        choices_site = [
            (f"site:{obj.id}", f"[Site-wide] {obj.get_display_name()}")
            for obj in queryset_site
        ]

        self.fields["source"].choices = chain(choices_site, choices_project)
