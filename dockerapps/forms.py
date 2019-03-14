"""Forms for the dockerapps app."""

from django import forms

from kiosc.utils import HorizontalFormHelper
from .models import DockerApp


class DockerAppForm(forms.ModelForm):
    """Form for creating and updating ``DockerApp`` records."""

    #: Field for Docker image upload.
    docker_image = forms.FileField(help_text="TAR file of the Docker image")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup crispy-forms helper
        self.helper = HorizontalFormHelper()

    class Meta:
        model = DockerApp
        fields = ("title", "description", "internal_port", "docker_image")


class DockerAppChangeStateForm(forms.ModelForm):
    """Form for updating the state of docker containers."""

    #: The action to perform (either start or stop).
    action = forms.ChoiceField(choices=(("start", "start"), ("stop", "stop")))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup crispy-forms helper
        self.helper = HorizontalFormHelper()

    class Meta:
        model = DockerApp
        fields = ("action",)
