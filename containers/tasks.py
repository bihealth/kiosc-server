from datetime import timedelta

import docker
import docker.errors
import dateutil.parser
import statemachine.exceptions

from django.db import transaction
from django.utils import timezone
from projectroles.plugins import get_backend_api

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from containers.models import (
    Container,
    ContainerBackgroundJob,
    LOG_LEVEL_ERROR,
    STATE_FAILED,
    PROCESS_TASK,
    PROCESS_DOCKER,
    LOG_LEVEL_WARNING,
)
from containers.statemachines import (
    ContainerMachine,
    connect_docker,
    ActionSwitch,
    ACTION_TO_EXPECTED_STATE,
)

User = auth.get_user_model()
app_settings = AppSettingAPI()

# Increase the timeout for communication with Docker daemon.
APP_NAME = "containers"
DEFAULT_GRACE_PERIOD_CONTAINER_STATUS = 180


class State:
    def __init__(self, state):
        self.state = state


@app.task(bind=True)
def container_task(_self, job_id):
    """Task to change a container state"""
    job = ContainerBackgroundJob.objects.get(pk=job_id)
    timeline = get_backend_api("timeline_backend")
    container = job.container
    user = job.bg_job.user
    tl_event = None
    cm = ContainerMachine(State(container.state), job=job)

    if timeline:
        tl_event = timeline.add_event(
            project=job.project,
            app_name=APP_NAME,
            user=user,
            event_name="container_task",
            description="{action} container {container}",
        )
        tl_event.add_object(
            obj=job.container,
            label="container",
            name=job.container.get_display_name(),
        )
        tl_event.add_object(
            obj=job,
            label="action",
            name=job.action,
        )

    acs = ActionSwitch(cm, job, tl_event)

    with job.marks():
        try:
            acs.do(job.action, job.container.state)

        except docker.errors.NotFound as e:
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            job.container.log_entries.create(
                text=f"Action failed: {job.action}",
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            job.container.log_entries.create(
                text=e,
                process=PROCESS_DOCKER,
                date_docker_log=timezone.now(),
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            with transaction.atomic():
                job.container.refresh_from_db()
                job.container.container_id = ""
                job.container.image_id = ""
                job.container.state = STATE_FAILED
                job.container.save()

        except docker.errors.DockerException as e:
            # Catch Docker-specific exceptions
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            container.log_entries.create(
                text=f"Action failed: {job.action}",
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            container.log_entries.create(
                text=e,
                process=PROCESS_DOCKER,
                date_docker_log=timezone.now(),
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)

        except statemachine.exceptions.StateMachineError as e:
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            container.log_entries.create(
                text=f"Action failed: {job.action} ({e})",
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_ERROR,
            )

        except Exception as e:
            # Catch all exceptions that are not coming from Docker
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            container.log_entries.create(
                text=f"Action failed: {job.action} ({e})",
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)


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
    sender.add_periodic_task(60, sig=poll_docker_status_and_logs.s())
    sender.add_periodic_task(
        300, sig=sync_container_state_with_last_user_action.s()
    )
