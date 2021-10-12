from django import forms
from django.conf import settings
from django.urls import reverse

from containers.models import Container, MASKED_KEYWORD
from filesfolders.models import File


class ContainerForm(forms.ModelForm):
    """ModelForm for creating and updating container."""

    class Meta:
        model = Container
        fields = [
            "title",
            "description",
            "repository",
            "tag",
            "container_port",
            "container_path",
            "containertemplatesite",
            "containertemplateproject",
            "heartbeat_url",
            "host_port",
            "timeout",
            "environment",
            "environment_secret_keys",
            "command",
            "project",
            "max_retries",
            "inactivity_threshold",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide project field
        self.fields["project"].widget = forms.HiddenInput()
        self.fields["containertemplatesite"].widget = forms.HiddenInput()
        self.fields["containertemplateproject"].widget = forms.HiddenInput()

        # Hide host port if in docker-shared mode
        if settings.KIOSC_NETWORK_MODE == "docker-shared":
            self.fields["host_port"].widget = forms.HiddenInput()

        # Make host port field mandatory in host mode
        if settings.KIOSC_NETWORK_MODE == "host":
            self.fields["host_port"].required = True

    def clean(self):
        """Override to check for secret keys in the environment."""
        cleaned_data = super().clean()
        environment = cleaned_data.get("environment", {})
        secret_keys = cleaned_data.get("environment_secret_keys")

        if not environment:
            return

        # Environment must be a dict
        if not isinstance(environment, dict):
            self.add_error("environment", "Environment must be a dictionary!")
            return

        # Check if secret keys are keys of the environment
        if secret_keys:
            secret_keys = [key.strip() for key in secret_keys.split(",")]

            for key in secret_keys:
                if key not in environment:
                    self.add_error(
                        "environment_secret_keys",
                        f'Secret key "{key}" is not in environment!',
                    )
                    return

                # Keep the old value if the masked keyword is preserved
                if environment[key] == MASKED_KEYWORD:
                    environment[key] = self.instance.environment[key]

            cleaned_data["environment_secret_keys"] = ",".join(secret_keys)

        return cleaned_data


class FileSelectorForm(forms.Form):
    """Form for selecting files from the filesfolders app."""

    #: File URL to insert
    file_url = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={"class": "form-control", "style": "width: 400px"}
        ),
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project")

        super().__init__(*args, **kwargs)

        def get_link(obj):
            return "http://{}:8080{}".format(
                settings.KIOSC_DOCKER_WEB_SERVER,
                reverse(
                    "containers:file-serve", kwargs={"file": obj.sodar_uuid}
                ),
            )

        queryset = File.objects.filter(project=project)

        self.fields["file_url"].choices = [
            (
                get_link(obj),
                "{}{}".format(
                    obj.folder.get_path()[4:] if obj.folder else "/", obj.name
                ),
            )
            for obj in queryset
        ]
