"""Forms for the dockerapps app."""

import json

from django import forms
from django.db import transaction

from kiosc.utils import HorizontalFormHelper
from .models import DockerImage, DockerProcess


#: Smallest port to use for the Docker container.
FIRST_PORT = 10001


class DockerImageForm(forms.ModelForm):
    """Form for creating and updating ``DockerContainer`` records."""

    def __init__(self, project, internal_port, env_vars, command, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: The project for the Docker image.
        self.project = project
        #: The crispy-forms helper.
        self.helper = HorizontalFormHelper()
        # Setup the fields
        self.fields["internal_port"].initial = internal_port
        self.fields["env_vars"].initial = json.dumps(env_vars)
        self.fields["command"].initial = command

    def save(self, commit=True):
        with transaction.atomic():
            super().save(commit=False)
            self.instance.project = self.project
            self.instance.save()

            # Get first free port
            first_process = DockerProcess.objects.order_by("-host_port").first()
            if first_process:
                host_port = first_process.host_port + 1
            else:
                host_port = 10001

            if self.instance.dockerprocess_set.all():
                process = self.instance.dockerprocess_set.first()
                process.project = self.project
                process.internal_port = self.cleaned_data["internal_port"]
                process.command = self.cleaned_data["command"]
                process.host_port = host_port
                process.environment = json.loads(self.cleaned_data["env_vars"])
                if self.cleaned_data["password"]:
                    process.password = self.cleaned_data["password"]
            else:
                process = self.instance.dockerprocess_set.create(
                    project=self.project,
                    command=self.cleaned_data["command"],
                    host_port=host_port,
                    internal_port=self.cleaned_data["internal_port"],
                    environment=json.loads(self.cleaned_data["env_vars"]),
                )

            if commit:
                self.instance.save()
                process.save()
            return self.instance

    class Meta:
        model = DockerImage
        fields = ("title", "description", "repository", "tag", "username")

    password = forms.CharField(
        label="Password",
        help_text="Leave blank to keep the previous password",
        required=False,
        max_length=1024,
        widget=forms.PasswordInput(),
    )

    internal_port = forms.IntegerField(
        label="Port inside container",
        help_text="Enter the port number of the service running inside the container",
        required=True,
        initial=80,
    )

    env_vars = forms.CharField(max_length=100_000, widget=forms.HiddenInput())

    command = forms.CharField(
        max_length=64000,
        widget=forms.Textarea(),
        help_text="The command to execute. Leave blank to use container default",
        required=False,
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


class DockerImagePullForm(forms.Form):
    """Form for pulling docker image again."""
