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
    "environment_secret_keys",
    "command",
    "repository",
    "tag",
    "max_retries",
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
