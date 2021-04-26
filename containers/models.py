import contextlib
import uuid

from bgjobs.models import BackgroundJob, JobModelMessageMixin
from django.db.models import JSONField
from django.db import models
from django.urls import reverse
from django.utils.timezone import localtime
from projectroles.models import Project


#: Token for 'created' state of container.
STATE_CREATED = "created"

#: Token for 'restarting' state of container.
STATE_RESTARTING = "restarting"

#: Token for 'running' state of container.
STATE_RUNNING = "running"

#: Token for 'paused' state of container.
STATE_PAUSED = "paused"

#: Token for 'exited' state of container.
STATE_EXITED = "exited"

#: Token for 'dead' state of container.
STATE_DEAD = "dead"

#: Token for 'deleting' state of container (no existing Docker container state).
STATE_DELETING = "deleting"

#: Token for 'deleted' state of container (no existing Docker container state).
STATE_DELETED = "deleted"

#: Token for 'pulling' state of container (no existing Docker container state).
STATE_PULLING = "pulling"

#: Token for 'initial' state of container (no existing Docker container state).
STATE_INITIAL = "initial"

#: Token for 'failed' state of container (no existing Docker container state)
STATE_FAILED = "failed"

#: List of Docker container states.
STATE_CHOICES = [
    # Following states are existing Docker container states
    (STATE_CREATED, STATE_CREATED),
    (STATE_RESTARTING, STATE_RESTARTING),
    (STATE_RUNNING, STATE_RUNNING),
    (STATE_PAUSED, STATE_PAUSED),
    (STATE_EXITED, STATE_EXITED),
    (STATE_DEAD, STATE_DEAD),
    # Following states are NO Docker container states
    (STATE_DELETING, STATE_DELETING),
    (STATE_DELETED, STATE_DELETED),
    (STATE_PULLING, STATE_PULLING),
    (STATE_INITIAL, STATE_INITIAL),
    (STATE_FAILED, STATE_FAILED),
]

#: Background job action for starting a container.
ACTION_START = "start"

#: Background job action for restarting a container.
ACTION_RESTART = "restart"

#: Background job action for stopping a container.
ACTION_STOP = "stop"

#: Background job action choices.
ACTION_CHOICES = [
    (ACTION_START, ACTION_START),
    (ACTION_RESTART, ACTION_RESTART),
    (ACTION_STOP, ACTION_STOP),
]

#: Log level info.
LOG_LEVEL_INFO = "info"

#: Log level warning.
LOG_LEVEL_WARNING = "warning"

#: Log level error.
LOG_LEVEL_ERROR = "error"

#: Log level choices.
LOG_LEVEL_CHOICES = [
    (LOG_LEVEL_INFO, LOG_LEVEL_INFO),
    (LOG_LEVEL_WARNING, LOG_LEVEL_WARNING),
    (LOG_LEVEL_ERROR, LOG_LEVEL_ERROR),
]


class JobModelMessageContextManagerMixin(JobModelMessageMixin):
    @contextlib.contextmanager
    def marks(self):
        """Return a context manager that allows to run tasks between start and success/error marks."""
        self.mark_start()

        try:
            yield
        except Exception as e:
            self.mark_error("Failure: %s" % e)
            raise e
        else:
            self.mark_success()


class ContainerTemplate(models.Model):
    """Model for container templates. TBD"""

    pass


class Container(models.Model):
    """Model for a Docker container instance."""

    class Meta:
        ordering = ("-date_created",)

    #: DateTime of container creation.
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of container creation"
    )

    #: DateTime of last container modification.
    date_modified = models.DateTimeField(
        auto_now=True, help_text="DateTime of last container modification"
    )

    #: DateTime of last pulling of logs.
    date_last_logs = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of last log pull"
    )

    #: The "repository" of the image.
    repository = models.CharField(
        max_length=512,
        help_text="The repository/name of the image.",
        blank=False,
        null=False,
    )

    #: The "tag" of the image.
    tag = models.CharField(
        max_length=128,
        help_text="The tag of the image.",
    )

    #: UUID of the container.
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text="Container SODAR UUID"
    )

    #: The project containing this container.
    project = models.ForeignKey(
        Project,
        related_name="containers",
        help_text="Project in which this container belongs",
        on_delete=models.CASCADE,
    )

    #: The ID of the image.
    image_id = models.CharField(
        max_length=128, help_text="Image ID", blank=True, null=True
    )

    #: The ID of the Docker container (when running).
    container_id = models.CharField(
        max_length=128, help_text="Container ID", blank=True, null=True
    )

    #: The port within the Docker container to listen on.
    container_port = models.IntegerField(
        default=80,
        help_text="Server port within the container",
        blank=False,
        null=False,
    )

    #: The path segment of the container URL.
    container_path = models.CharField(
        max_length=512,
        help_text="Path segment of the container URL",
        blank=True,
        null=True,
    )

    #: Heartbeat URL to check if server in Docker container is alive.
    heartbeat_url = models.CharField(
        max_length=512,
        help_text="Optional heartbeat URL to check if server in Docker container is alive",
        blank=True,
        null=True,
    )

    #: The port on the host (to redirect the requests/web socket to).
    host_port = models.IntegerField(
        help_text="Port of the container on the host",
        blank=False,
        null=False,
        unique=True,
    )

    #: The time interval in seconds permitted for a container to remain in start up state.
    timeout = models.IntegerField(
        help_text="Interval in seconds for a container remain in start up state.",
        default=60,
        blank=False,
        null=False,
    )

    #: Flag whether container timed out during last start up.
    timeout_exceeded = models.BooleanField(
        default=False,
        help_text="Whether or not the container has timed out during start up",
        blank=False,
        null=False,
    )

    #: The current state.
    state = models.CharField(
        max_length=32,
        help_text="The state of the container.",
        choices=STATE_CHOICES,
        default=STATE_INITIAL,
        blank=False,
        null=False,
    )

    #: Define the environment variables to use, as an array of dicts with keys "name" and "value".
    #: This guarantees that the order of environment variable definitions does not change.
    environment = JSONField(help_text="The environment variables to use")

    #: List if keys that when defined in ``environment`` are set but no displayed.
    environment_secret_keys = models.CharField(
        max_length=512,
        help_text="Comma-separated list of keys in the environment that are set but not read (use for tokens/keys).",
        blank=True,
        null=True,
    )

    #: The command to execute.
    command = models.TextField(
        help_text="The command to execute", blank=True, null=True
    )

    def __str__(self):
        tag = f":{self.tag}" if self.tag else ""
        return (
            f"Container: {self.repository}{tag}:{self.host_port} [{self.state}]"
        )

    def __repr__(self):
        tag = f":{self.tag}" if self.tag else ""
        return f"Container({self.repository}{tag}:{self.host_port})"

    def get_absolute_url(self):
        return reverse(
            "containers:container-detail", kwargs={"container": self.sodar_uuid}
        )

    def get_date_created(self):
        return localtime(self.date_created).strftime("%Y-%m-%d %H:%M")

    def get_date_modified(self):
        return localtime(self.date_modified).strftime("%Y-%m-%d %H:%M")

    def get_display_name(self):
        tag = f":{self.tag}" if self.tag else ""
        return f"{self.repository}{tag}:{self.host_port}"


class ContainerBackgroundJob(JobModelMessageContextManagerMixin, models.Model):
    """Model for container background jobs."""

    spec_name = "containers.container_bg_job"

    #: DateTime of creation.
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of creation"
    )

    #: UUID of the job.
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Background job specialization SODAR UUID",
    )

    #: The project that the job belongs to.
    project = models.ForeignKey(
        Project,
        help_text="Project in which this objects belongs",
        on_delete=models.CASCADE,
    )

    #: The ``Container`` that the job belongs to.
    container = models.ForeignKey(
        Container,
        help_text="The container that the job belongs to",
        on_delete=models.CASCADE,
    )

    #: The action to perform.
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)

    #: The background job that is specialized.
    bg_job = models.ForeignKey(
        BackgroundJob,
        null=False,
        blank=False,
        related_name="%(app_label)s_%(class)s_related",
        help_text="Background job for state etc.",
        on_delete=models.CASCADE,
    )


class ContainerLogEntry(models.Model):
    """Model for container log entries."""

    #: DateTime of creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of creation"
    )

    #: The level of the log entry.
    level = models.CharField(
        max_length=32,
        choices=LOG_LEVEL_CHOICES,
        default=LOG_LEVEL_INFO,
        help_text="Level of log entry",
        blank=False,
        null=False,
    )

    #: The log entry text.
    text = models.TextField()

    #: The ``Container`` that the log entry is for.
    container = models.ForeignKey(
        Container,
        related_name="log_entries",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
