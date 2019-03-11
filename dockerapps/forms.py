"""Forms for the dockerapps app."""

from django import forms

from kiosc.utils import HorizontalFormHelper
from .models import DockerApp


class DockerAppForm(forms.ModelForm):
    """Form for creating and updating ``DockerApp`` records."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup crispy-forms helper
        self.helper = HorizontalFormHelper()

    class Meta:
        model = DockerApp
        fields = ("title", "description", "image_id")
