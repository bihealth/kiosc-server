import logging
from datetime import timedelta

import docker
import docker.errors
import dateutil.parser

from bgjobs.models import BackgroundJob
from celery.schedules import crontab
from django.conf import settings

from django.utils import timezone

from containers.tasks import container_task
from projectroles.models import SODAR_CONSTANTS

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from containers.models import (
    Container,
    ContainerBackgroundJob,
    STATE_FAILED,
    PROCESS_TASK,
    PROCESS_DOCKER,
    LOG_LEVEL_WARNING,
    PROCESS_PROXY,
    STATE_RUNNING,
    STATE_PAUSED,
    ACTION_STOP,
)
from containers.statemachines import (
    connect_docker,
    ACTION_TO_EXPECTED_STATE,
)

User = auth.get_user_model()
app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)

# Increase the timeout for communication with Docker daemon.
APP_NAME = "kioscadmin"
DEFAULT_GRACE_PERIOD_CONTAINER_STATUS = 180

# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS["SITE_MODE_TARGET"]
SITE_MODE_SOURCE = SODAR_CONSTANTS["SITE_MODE_SOURCE"]


@app.task(bind=True)
def stop_inactive_containers(_self):
    cli = connect_docker()
    msgs = []

    for container in Container.objects.all():
        if not container.container_id:
            continue

        # Check if container exists
        try:
            data = cli.inspect_container(container.container_id)

        except docker.errors.NotFound:
            continue

        else:
            state = data.get("State", {}).get("Status")

            if not state or state not in (STATE_RUNNING, STATE_PAUSED):
                continue

            # Get latest proxy entry
            obj = (
                container.log_entries.filter(process=PROCESS_PROXY)
                .order_by("-date_created")
                .first()
            )

            if obj:
                last_access = obj.date_created

            else:
                continue

            threshold = last_access + timedelta(
                days=min(
                    container.inactivity_threshold,
                    settings.KIOSC_DOCKER_MAX_INACTIVITY,
                )
            )

            if threshold < timezone.now():
                bg_job = BackgroundJob.objects.create(
                    name="Stop container",
                    project=container.project,
                    job_type=ContainerBackgroundJob.spec_name,
                    user=User.objects.get(
                        username=settings.PROJECTROLES_DEFAULT_ADMIN
                    ),
                )
                job = ContainerBackgroundJob.objects.create(
                    action=ACTION_STOP,
                    project=container.project,
                    container=container,
                    bg_job=bg_job,
                )

                container_task.apply_async(
                    kwargs={"job_id": job.id}, countdown=0.5
                )

                msgs.append("Submitted job to stop {}".format(container.title))

    return msgs


@app.task(bind=True)
def poll_docker_status_and_logs(_self):
    cli = connect_docker()

    for container in Container.objects.all():
        if not container.container_id:
            continue

        try:
            data = cli.inspect_container(container.container_id)

        except docker.errors.NotFound:
            container.container_id = ""
            container.state = STATE_FAILED
            container.save()

        else:
            state = data.get("State", {}).get("Status")
            last_log = container.log_entries.filter(
                process=PROCESS_DOCKER
            ).last()
            fetch_logs_parameters = {"timestamps": True}
            date_last_logs = None

            if last_log:
                date_last_logs = last_log.date_docker_log
                fetch_logs_parameters["since"] = date_last_logs.replace(
                    tzinfo=None
                )

            # Get most recent logs. ``since`` does not consider milliseconds,
            # so we need to post-filter to avoid duplicates.
            try:
                logs = (
                    cli.logs(container.container_id, **fetch_logs_parameters)
                    .decode("utf-8")
                    .strip()
                    .split("\n")
                )

            except docker.errors.DockerException as e:
                # Log somewhere?
                raise e

            if state and not container.state == state:
                container.date_last_status_update = timezone.now()
                container.state = state
                container.save()

            for line in logs:
                try:
                    text = line[31:]
                    log_date = dateutil.parser.parse(line[:30])
                except dateutil.parser.ParserError:
                    container.log_entries.create(
                        text=f"Docker log has no timestamp! ({line})",
                        level=LOG_LEVEL_WARNING,
                        process=PROCESS_TASK,
                    )
                    continue

                # Filter out duplicates
                if date_last_logs and log_date <= date_last_logs:
                    continue

                # Write new log entry
                container.log_entries.create(
                    date_docker_log=log_date, text=text, process=PROCESS_DOCKER
                )


@app.task(bind=True)
def sync_container_state_with_last_user_action(_self):
    cli = connect_docker()

    for container in Container.objects.all():
        if not container.container_id:
            continue

        try:
            data = cli.inspect_container(container.container_id)

        except docker.errors.NotFound:
            continue

        else:
            state = data.get("State", {}).get("Status")
            job = container.containerbackgroundjob.last()

            if not (state and job and container.date_last_status_update):
                continue

            # Do nothing, Docker state needs to be synced first
            if not container.state == state:
                continue

            # Reset counter when action and state are in harmony
            if ACTION_TO_EXPECTED_STATE[job.action] == state:
                job.retries = 0
                job.save()
                continue

            if (
                container.date_last_status_update
                <= timezone.now()
                - timedelta(seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS)
                and job.retries < container.max_retries
            ):
                container.log_entries.create(
                    text=f"Syncing last registered container state ({container.state}) with current Docker state ({state})",
                    process=PROCESS_TASK,
                )

                # No async task
                container_task(job.id)
                job.retries += 1
                job.save()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    sender.add_periodic_task(30, sig=poll_docker_status_and_logs.s())
    sender.add_periodic_task(
        60, sig=sync_container_state_with_last_user_action.s()
    )
    sender.add_periodic_task(
        crontab(hour=1, minute=11), sig=stop_inactive_containers.s()
    )
