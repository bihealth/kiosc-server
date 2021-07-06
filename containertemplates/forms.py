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


class CustomLabelModelChoiceField(forms.ModelChoiceField):
    """Custom ModelChoiceField class for modified labels"""

    def label_from_instance(self, obj):
        return obj.get_display_name()


class ContainerTemplateSiteToProjectCopyForm(forms.Form):
    """Form for copying a site-wide containertemplate to a project."""

    #: Source template to copy
    source = CustomLabelModelChoiceField(
        queryset=ContainerTemplateSite.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    #: Define whether source is site-wide or project-wide container template
    site_or_project = forms.CharField(
        initial="site", widget=forms.HiddenInput()
    )


class ContainerTemplateProjectToProjectCopyForm(forms.Form):
    """Form for copying a project-wide containertemplate to a project."""

    #: Source template to copy
    source = CustomLabelModelChoiceField(
        queryset=ContainerTemplateProject.objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    #: Define whether source is site-wide or project-wide container template
    site_or_project = forms.CharField(
        initial="project", widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")

        super().__init__(*args, **kwargs)

        if user.is_superuser:
            self.fields[
                "source"
            ].queryset = ContainerTemplateProject.objects.all()
        else:
            self.fields[
                "source"
            ].queryset = ContainerTemplateProject.objects.filter(
                project__roles__user=user
            )
