"""Forms for the dockerapps app."""

from django import forms
from django.db import transaction

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
        with transaction.atomic():
            super().save(commit=False)
            self.instance.project = self.project
            if not self.instance.dockercontainer_set:
                self.instance.dockercontainer_set.create()
            self.instance.dockercontainer.internal_port = self.cleaned_data["internal_port"]

            try:
                host_port = DockerImage.objects.order_by(["-host_port"]).first().host_port + 1
            except DockerImage.DoesNotExist:
                host_port = 10001
            self.instance.dockercontainer.host_port = host_port

            if commit:
                self.instance.save()
            return self.instance

    class Meta:
        model = DockerImage
        fields = ("title", "description", "repository", "tag")

    internal_port = forms.IntegerField(
        label="Port inside container",
        help_text="Enter the port number of the service running inside the container",
        required=True,
        initial=80,
    )

    @property
    def dockerimage(self):
        return self.dockerimage_set.first()


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
