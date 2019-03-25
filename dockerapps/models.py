import uuid as uuid_object

import docker
from django.shortcuts import reverse
from django.db import models, transaction

from projectroles.models import Project

#: Token for "idle" state.
STATE_IDLE = "idle"
#: Token for "starting" state.
STATE_STARTING = "starting"
#: Token for "running" state.
STATE_RUNNING = "running"
#: Token for "stopping" state.
STATE_STOPPING = "stopping"
#: Token for "failed" state.
STATE_FAILED = "failed"
#: Django model field choices.
STATE_CHOICES = (
    (STATE_IDLE, STATE_IDLE),
    (STATE_STARTING, STATE_STARTING),
    (STATE_RUNNING, STATE_RUNNING),
    (STATE_STOPPING, STATE_STOPPING),
    (STATE_FAILED, STATE_FAILED),
)


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
    image_id = models.CharField(max_length=100, help_text="Internal ID of the Docker image", blank=True, null=True)

    #: The internal port used by the app, automatically set.
    internal_port = models.PositiveIntegerField(
        help_text="Port used by the Docker image", blank=True, null=True
    )

    #: The host port used by the app, automatically set.
    host_port = models.PositiveIntegerField(
        help_text="Port used by the Docker image", blank=True, null=True, unique=True
    )

    #: The current state.
    state = models.CharField(
        max_length=32,
        choices=STATE_CHOICES,
        help_text="The current docker container state",
        default=STATE_IDLE,
    )

    def get_absolute_url(self):
        return reverse(
            "dockerapps:dockerapp-detail",
            kwargs={"project": self.project.sodar_uuid, "dockerapp": self.sodar_uuid},
        )


@transaction.atomic()
def update_container_states():
    """Look at all starting and stopping ``DockerApp`` objects, and finalize their state."""
    print("updating container states...")
    statuses = {}
    for container in docker.from_env().containers.list():
        statuses[container.image.id] = container.status
    for app in DockerApp.objects.all():
        if statuses.get(app.image_id) == "running":
            app.state = "running"
            app.save()
        elif statuses.get(app.image_id, "exited") == "exited":
            app.state = "idle"
            app.save()
