import uuid

from django.conf import settings
from django.db import models
from django.db.models import JSONField
from django.urls import reverse
from django.utils.timezone import localtime
from projectroles.models import Project


class ContainerTemplateBase(models.Model):
    """Base model for a ContainerTemplate* instances."""

    class Meta:
        abstract = True

    #: Title of the template
    title = models.CharField(
        max_length=512,
        help_text="Title of the container template.",
    )

    #: Description of the template
    description = models.TextField(
        help_text="Description of the container template.",
        blank=True,
        null=True,
    )

    #: DateTime of container creation.
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of ContainerTemplate creation"
    )

    #: DateTime of last container modification.
    date_modified = models.DateTimeField(
        auto_now=True,
        help_text="DateTime of last ContainerTemplate modification",
    )

    #: The "repository" of the image.
    repository = models.CharField(
        max_length=512,
        help_text="The repository/name of the image.",
        blank=True,
        null=True,
    )

    #: The "tag" of the image.
    tag = models.CharField(
        max_length=128,
        help_text="The tag of the image.",
        blank=True,
        null=True,
    )

    #: UUID of the container template.
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="ContainerTemplate SODAR UUID",
    )

    #: The port within the Docker container to listen on.
    container_port = models.IntegerField(
        default=80,
        help_text="Server port within the container",
        blank=True,
        null=True,
    )

    #: The path segment of the container URL.
    container_path = models.CharField(
        max_length=512,
        help_text="Path segment of the container URL",
        default="",
        blank=True,
        null=False,
    )

    #: Heartbeat URL to check if server in Docker container is alive.
    heartbeat_url = models.CharField(
        max_length=512,
        help_text="Optional heartbeat URL to check if server in Docker container is alive",
        blank=True,
        null=True,
    )

    #: The time interval in seconds permitted for any Docker action to be performed.
    timeout = models.IntegerField(
        help_text="Interval in seconds for any Docker action to be performed.",
        default=60,
        blank=True,
        null=True,
    )

    #: Define the environment variables to use, as an array of dicts with keys "name" and "value".
    #: This guarantees that the order of environment variable definitions does not change.
    environment = JSONField(
        help_text="The environment variables to use",
        blank=True,
        null=True,
    )

    #: The command to execute.
    command = models.TextField(
        help_text="The command to execute", blank=True, null=True
    )

    #: Max number of retries for an action in case of failure.
    max_retries = models.IntegerField(
        help_text="Maximal number of retries for an action in case of failure",
        blank=True,
        null=True,
        default=5,
    )

    #: Number of days the container can run without proxy access
    inactivity_threshold = models.IntegerField(
        help_text="Number of days the container is allowed to run without proxy access.",
        blank=True,
        null=True,
        default=settings.KIOSC_DOCKER_MAX_INACTIVITY,
    )

    def __str__(self):
        return self.title

    def get_repos_full(self):
        repos = self.repository or "<no_repository>"
        tag = f":{self.tag}" if self.tag else ""
        return f"{repos}{tag}"

    def get_date_created(self):
        return localtime(self.date_created).strftime("%Y-%m-%d %H:%M")

    def get_date_modified(self):
        return localtime(self.date_modified).strftime("%Y-%m-%d %H:%M")


class ContainerTemplateSite(ContainerTemplateBase):
    """Model for a ContainerTemplate instance."""

    class Meta:
        ordering = ("-date_created",)
        unique_together = ("title",)

    def get_absolute_url(self):
        return reverse(
            "containertemplates:site-detail",
            kwargs={"containertemplatesite": self.sodar_uuid},
        )

    def get_display_name(self):
        return f"{self.title} ({self.get_repos_full()})"

    def __repr__(self):
        return f"ContainerTemplateSite({self.title}, {self.get_repos_full()})"


class ContainerTemplateProject(ContainerTemplateBase):
    """Model for a ContainerTemplateProject instance."""

    #: Project the containertemplate belongs to.
    project = models.ForeignKey(
        Project,
        related_name="containertemplates",
        help_text="Project in which the object belongs",
        on_delete=models.CASCADE,
    )

    #: Link to the site-wide containertemplate (optional).
    containertemplatesite = models.ForeignKey(
        ContainerTemplateSite,
        related_name="containertemplateprojects",
        help_text="Link to site-wide container template",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-date_created",)
        unique_together = (
            "title",
            "project",
        )

    def get_display_name(self):
        return f"{self.project} / {self.title} ({self.get_repos_full()})"

    def get_absolute_url(self):
        return reverse(
            "containertemplates:project-detail",
            kwargs={"containertemplateproject": self.sodar_uuid},
        )

    def __repr__(self):
        return f"ContainerTemplateProject({self.project}, {self.title}, {self.get_repos_full()})"
