import contextlib
import uuid
from datetime import timedelta

from bgjobs.models import BackgroundJob, JobModelMessageMixin, LOG_LEVEL_DEBUG
from django.conf import settings
from django.db.models import JSONField
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime
from projectroles.models import Project


#: Django user model.
from containertemplates.models import (
    ContainerTemplateProject,
    ContainerTemplateSite,
)

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")

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

#: Background job action for pausing a container.
ACTION_PAUSE = "pause"

#: Background job action for unpausing a container.
ACTION_UNPAUSE = "unpause"

#: Background job action for deleting a container.
ACTION_DELETE = "delete"

#: Background job action choices.
ACTION_CHOICES = [
    (ACTION_START, ACTION_START),
    (ACTION_RESTART, ACTION_RESTART),
    (ACTION_STOP, ACTION_STOP),
    (ACTION_PAUSE, ACTION_PAUSE),
    (ACTION_UNPAUSE, ACTION_UNPAUSE),
    (ACTION_DELETE, ACTION_DELETE),
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

#: Process ``object`` reporting the log entry.
PROCESS_OBJECT = "object"

#: Process ``task`` reporting the log entry.
PROCESS_TASK = "task"

#: Process ``proxy`` reporting the log entry.
PROCESS_PROXY = "proxy"

#: Process ``docker`` reporting the log entry.
PROCESS_DOCKER = "docker"

#: Process ``action`` reporting the log entry.
PROCESS_ACTION = "action"

#: Process choices.
PROCESS_CHOICES = [
    (PROCESS_OBJECT, PROCESS_OBJECT),
    (PROCESS_TASK, PROCESS_TASK),
    (PROCESS_PROXY, PROCESS_PROXY),
    (PROCESS_DOCKER, PROCESS_DOCKER),
    (PROCESS_ACTION, PROCESS_ACTION),
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


class Container(models.Model):
    """Model for a Docker container instance."""

    class Meta:
        ordering = ("-date_created",)
        unique_together = ("project", "title")
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_site_or_project_or_null_template",
                check=(
                    models.Q(
                        containertemplateproject__isnull=False,
                        containertemplatesite__isnull=True,
                    )
                    | models.Q(
                        containertemplateproject__isnull=True,
                        containertemplatesite__isnull=False,
                    )
                    | models.Q(
                        containertemplateproject__isnull=True,
                        containertemplatesite__isnull=True,
                    )
                ),
            )
        ]

    #: DateTime of container creation.
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of container creation"
    )

    #: DateTime of last container modification.
    date_modified = models.DateTimeField(
        auto_now=True, help_text="DateTime of last container modification"
    )

    #: DateTime of last status update.
    date_last_status_update = models.DateTimeField(
        blank=True, null=True, help_text="DateTime of last status update"
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
        blank=True,
        null=True,
        unique=True,
    )

    #: The time interval in seconds permitted for any Docker action to be performed.
    timeout = models.IntegerField(
        help_text="Interval in seconds for any Docker action to be performed.",
        default=60,
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
    environment = JSONField(
        help_text="The environment variables to use", blank=True, null=True
    )

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

    #: Max number of retries for an action in case of failure.
    max_retries = models.IntegerField(
        help_text="Maximal number of retries for an action in case of failure",
        blank=False,
        null=False,
        default=5,
    )

    #: Link to ``ContainerTemplateSite`` (optional)
    containertemplatesite = models.ForeignKey(
        ContainerTemplateSite,
        related_name="containers",
        help_text="Link to site-wide container template",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    #: Link to ``ContainerTemplateProject`` (optional)
    containertemplateproject = models.ForeignKey(
        ContainerTemplateProject,
        related_name="containers",
        help_text="Link to project-wide container template",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    #: Title of the container
    title = models.CharField(
        max_length=512,
        help_text="Title of the container.",
    )

    #: Description of the container
    description = models.TextField(
        help_text="Description of the container.",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.title} [{self.state}]"

    def __repr__(self):
        return f"Container({self.title}, {self.state})"

    def get_repos_full(self):
        tag = f":{self.tag}" if self.tag else ""
        return f"{self.repository}{tag}"

    def get_absolute_url(self):
        return reverse(
            "containers:detail", kwargs={"container": self.sodar_uuid}
        )

    def get_date_created(self):
        return localtime(self.date_created).strftime("%Y-%m-%d %H:%M")

    def get_date_modified(self):
        return localtime(self.date_modified).strftime("%Y-%m-%d %H:%M")

    def get_display_name(self):
        return self.title


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
        related_name="containerbackgroundjob",
        on_delete=models.CASCADE,
    )

    #: The action to perform.
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)

    #: Retry count
    retries = models.IntegerField(
        help_text="Number of retries for the action.",
        default=0,
    )

    #: The background job that is specialized.
    bg_job = models.ForeignKey(
        BackgroundJob,
        null=False,
        blank=False,
        related_name="%(app_label)s_%(class)s_related",
        help_text="Background job for state etc.",
        on_delete=models.CASCADE,
    )


class ContainerLogEntryManager(models.Manager):
    def merge_order(self, *args, **kwargs):
        is_superuser = (
            kwargs.pop("user").is_superuser if "user" in kwargs else False
        )
        qs = self.get_queryset().filter(*args, **kwargs)

        # Show DEBUG level only to superuser
        if not is_superuser:
            qs = qs.exclude(level=LOG_LEVEL_DEBUG)

        return sorted(
            qs,
            key=lambda a: a.date_docker_log
            if a.date_docker_log
            else a.date_created,
        )

    def get_date_last_docker_log(self, *args, **kwargs):
        obj = (
            self.get_queryset()
            .filter(*args, *kwargs)
            .filter(process=PROCESS_DOCKER)
            .last()
        )

        if not obj:
            return None

        return obj.get_date_docker_log()


class ContainerLogEntry(models.Model):
    """Model for container log entries."""

    #: Custom manager for sorting
    objects = ContainerLogEntryManager()

    #: DateTime of creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="DateTime of creation"
    )

    #: DateTime of Docker log entry
    date_docker_log = models.DateTimeField(
        blank=True, null=True, help_text="DateTime of Docker log entry"
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

    #: The ``user`` causing the log entry.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="log_entries",
        help_text="User who caused the log entry",
    )

    #: The process reporting the log entry.
    process = models.CharField(
        max_length=32,
        blank=False,
        null=False,
        choices=PROCESS_CHOICES,
        default=PROCESS_OBJECT,
        help_text="Process that reports the entry",
    )

    def get_date_created(self):
        return localtime(self.date_created).strftime("%Y-%m-%d %H:%M:%S")

    def get_date_docker_log(self):
        return (
            localtime(self.date_docker_log).strftime("%Y-%m-%d %H:%M:%S")
            if self.date_docker_log
            else ""
        )

    def get_date_order_by(self):
        return self.get_date_docker_log() or self.get_date_created()

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"[{self.get_date_order_by()} {self.level.upper()} {username}] ({self.process.capitalize()}) {self.text}"

    def __repr__(self):
        return f"ContainerLogEntry({self.container.get_display_name()},{self.get_date_created()})"


class ContainerActionLock(models.Model):
    """Model for tracking container actions (with the purpose of limiting them)."""

    #: DateTime of creation
    date_of_action = models.DateTimeField(
        auto_now=True, help_text="DateTime of action"
    )

    #: ``Container`` the action was performed on.
    container = models.ForeignKey(
        Container,
        related_name="action_lock",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    #: Action
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)

    class CoolDown(Exception):
        pass

    def queryset(self):
        return self.__class__.objects.filter(id=self.id)

    def is_locked(self):
        return timezone.now() < self.date_of_action + timedelta(
            seconds=settings.KIOSC_DOCKER_ACTION_MIN_DELAY
        )

    def lock(self, action):
        if self.is_locked():
            raise ContainerActionLock.CoolDown

        with transaction.atomic():
            lock = self.queryset().select_for_update().get()

            if lock.is_locked():
                raise ContainerActionLock.CoolDown

            lock.action = action
            lock.save()
