from django import forms

from containertemplates.models import ContainerTemplate


class ContainerTemplateForm(forms.ModelForm):
    """ModelForm for creating and updating containertemplate."""

    class Meta:
        model = ContainerTemplate
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
