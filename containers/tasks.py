import shlex

import docker
import docker.errors
import dateutil.parser

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from docker.types import Ulimit
from projectroles.plugins import get_backend_api

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from containers.models import (
    Container,
    ContainerBackgroundJob,
    LOG_LEVEL_ERROR,
    ACTION_START,
    ACTION_STOP,
    STATE_PULLING,
    STATE_FAILED,
    PROCESS_TASK,
    PROCESS_DOCKER,
)


User = auth.get_user_model()
app_settings = AppSettingAPI()

# Increase the timeout for communication with Docker daemon.
APP_NAME = "containers"
DEFAULT_TIMEOUT = 600


def connect_docker(base_url="unix:///var/run/docker.sock"):
    return docker.APIClient(base_url=base_url, timeout=DEFAULT_TIMEOUT)


@app.task(bind=True)
def container_task(_self, job_id):
    """Task to change a container state"""
    job = ContainerBackgroundJob.objects.get(pk=job_id)
    timeline = get_backend_api("timeline_backend")
    tl_event = None
    user = job.bg_job.user

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

    with job.marks():
        try:
            # Get image, check state, update to pulling.
            with transaction.atomic():
                container = job.container
                job.add_log_entry("Connecting to Docker API...")
                cli = connect_docker()

                if job.action == ACTION_START:
                    if not container.image_id:
                        # Pulling image
                        job.add_log_entry(
                            f"Pulling image {container.repository}:{container.tag} ..."
                        )
                        container.log_entries.create(
                            text="Pulling image ...",
                            process=PROCESS_TASK,
                            user=user,
                        )
                        container.state = STATE_PULLING
                        container.save()

                        for line in cli.pull(
                            repository=container.repository,
                            tag=container.tag,
                            stream=True,
                            decode=True,
                        ):
                            if line.get("progressDetail"):
                                docker_log_line = "{status} ({progressDetail[current]}/{progressDetail[total]})".format(
                                    **line
                                )
                            else:
                                docker_log_line = line["status"]

                            container.log_entries.create(
                                text=docker_log_line,
                                process=PROCESS_DOCKER,
                                date_docker_log=timezone.now(),
                                user=user,
                            )
                            job.add_log_entry(docker_log_line)

                        image_details = cli.inspect_image(
                            f"{container.repository}:{container.tag}"
                        )
                        container.image_id = image_details.get("Id")
                        container.save()
                        job.add_log_entry("Pulling image succeeded")
                        container.log_entries.create(
                            text="Pulling image succeeded",
                            process=PROCESS_TASK,
                            user=user,
                        )

                    # Create container
                    _container = cli.create_container(
                        detach=True,
                        image=container.image_id,
                        environment={},
                        command=shlex.split(container.command)
                        if container.command
                        else None,
                        ports=[container.container_port],
                        host_config=cli.create_host_config(
                            port_bindings={
                                container.container_port: container.host_port
                            },
                            ulimits=[
                                Ulimit(
                                    name="nofile",
                                    soft=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                                    hard=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                                )
                            ],
                        ),
                    )
                    container.container_id = _container.get("Id")

                    if _container.get("State"):
                        container.state = _container.get("State").get("Status")
                        container.save()

                    # Starting container
                    container.log_entries.create(
                        text="Starting ...", process=PROCESS_TASK, user=user
                    )
                    job.add_log_entry("Starting container")
                    cli.start(container=container.container_id)
                    _container = cli.inspect_container(container.container_id)
                    container.state = _container.get("State", {}).get("Status")
                    container.save()
                    job.add_log_entry("Starting container succeeded")
                    container.log_entries.create(
                        text="Starting succeeded",
                        process=PROCESS_TASK,
                        user=user,
                    )

                elif job.action == ACTION_STOP:
                    # Stopping container
                    container.log_entries.create(
                        text="Stopping ...", process=PROCESS_TASK, user=user
                    )
                    job.add_log_entry("Stopping container")
                    cli.stop(container=container.container_id)
                    _container = cli.inspect_container(container.container_id)
                    container.state = _container.get("State", {}).get("Status")
                    container.save()
                    container.log_entries.create(
                        text="Stopping succeeded",
                        process=PROCESS_TASK,
                        user=user,
                    )
                    job.add_log_entry("Stopping container succeeded")

                else:
                    if timeline:
                        tl_event.set_status("FAILED", "action failed")
                    container.log_entries.create(
                        text=f"Unknown action: {job.action}",
                        process=PROCESS_TASK,
                        user=user,
                    )
                    raise RuntimeError(f"Unknown action: {job.action}")

                if timeline:
                    tl_event.set_status("OK", "action succeeded")

        except docker.errors.NotFound as e:
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
                container.container_id = ""
                container.image_id = ""
                container.state = STATE_FAILED
                container.save()

        except docker.errors.DockerException as e:
            # Catch Docker-speficif exceptions
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

        except Exception:
            # Catch all exceptions that are not coming from Docker
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            container.log_entries.create(
                text=f"Action failed: {job.action}",
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

            if state:
                container.state = state
                container.save()

            for line in logs:
                text = line[51:]
                log_date = dateutil.parser.parse(line[:30])

                # Filter out duplicates
                if date_last_logs and log_date <= date_last_logs:
                    continue

                # Write new log entry
                container.log_entries.create(
                    date_docker_log=log_date, text=text, process=PROCESS_DOCKER
                )


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    sender.add_periodic_task(60, sig=poll_docker_status_and_logs.s())
