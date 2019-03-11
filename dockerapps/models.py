import uuid as uuid_object

from django.shortcuts import reverse
from django.db import models

from projectroles.models import Project


class DockerApp(models.Model):

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: DateTime of last modification
    date_modified = models.DateTimeField(auto_now=True, help_text="DateTime of last modification")

    #: UUID used for identification throughout SODAR.
    sodar_uuid = models.UUIDField(
        default=uuid_object.uuid4, unique=True, help_text="Barcodeset SODAR UUID"
    )

    #: The project containing this barcode set.
    project = models.ForeignKey(Project, help_text="Project in which this objects belongs")

    #: The title of the application
    title = models.CharField(max_length=100, help_text="Title of the docker app")

    #: The description of the application
    description = models.TextField(help_text="Description of the docker app", blank=True, null=True)

    #: The internal image ID.
    image_id = models.CharField(max_length=100, help_text="Internal ID of the Docker image")

    def get_absolute_url(self):
        return reverse(
            "dockerapps:dockerapp-detail",
            kwargs={"project": self.project.sodar_uuid, "dockerapp": self.sodar_uuid},
        )
