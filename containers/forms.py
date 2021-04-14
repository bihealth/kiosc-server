from django import forms

from containers.models import Container


class ContainerForm(forms.ModelForm):
    """ModelForm for creating and updating container."""

    class Meta:
        model = Container
        fields = [
            "container_port",
            "container_path",
            "heartbeat_url",
            "host_port",
            "timeout",
            "environment",
            "environment_secret_keys",
            "command",
            "project",
            "repository",
            "tag",
        ]

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        if instance:
            self.initial["project"] = instance.project
        elif project:
            self.initial["project"] = project

        self.fields["project"].widget = forms.HiddenInput()
