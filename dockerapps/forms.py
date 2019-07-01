"""Forms for the dockerapps app."""

from django import forms

from kiosc.utils import HorizontalFormHelper
from .models import DockerImage, DockerProcess


class DockerImageForm(forms.ModelForm):
    """Form for creating and updating ``DockerContainer`` records."""

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: The project for the Docker image.
        self.project = project
        #: The crispy-forms helper.
        self.helper = HorizontalFormHelper()

    def save(self, commit=True):
        super().save(commit=False)
        self.instance.project = self.project
        if commit:
            self.instance.save()
        return self.instance

    class Meta:
        model = DockerImage
        fields = ("title", "description", "repository", "tag")


class DockerProcessJobControlForm(forms.ModelForm):
    """Form for updating the state of ``DockerProcess``."""

    #: The action to perform (either start, restart, or stop).
    action = forms.ChoiceField(
        choices=(("start", "start"), ("restart", "restart"), ("stop", "stop"))
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup crispy-forms helper
        self.helper = HorizontalFormHelper()

    class Meta:
        model = DockerProcess
        fields = ("action",)
