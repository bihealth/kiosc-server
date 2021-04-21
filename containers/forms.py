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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide project field
        self.fields["project"].widget = forms.HiddenInput()

    def clean(self):
        """Override to check for secret keys in the environment."""
        cleaned_data = super().clean()
        environment = cleaned_data.get("environment")
        secret_keys = cleaned_data.get("environment_secret_keys")

        # This error is already caught
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
                if key not in environment.keys():
                    self.add_error(
                        "environment_secret_keys",
                        f'Secret key "{key}" is not in environment!',
                    )
                    return

            cleaned_data["environment_secret_keys"] = ",".join(secret_keys)

        return cleaned_data
