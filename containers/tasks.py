import shlex

import docker
from django.conf import settings
from django.db import transaction
from docker.types import Ulimit
from projectroles.plugins import get_backend_api

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from containers.models import (
    ContainerBackgroundJob,
    LOG_LEVEL_ERROR,
    STATE_FAILED,
    ACTION_START,
    ACTION_STOP,
    STATE_EXITED,
    STATE_RUNNING,
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
                            text="(Task) Pulling image ...", user=user
                        )
                        for line in cli.pull(
                            repository=container.repository,
                            tag=container.tag,
                            stream=True,
                            decode=True,
                        ):
                            docker_log_line = "(Task|Docker Log) "

                            if line.get("progressDetail"):
                                docker_log_line += "{status} ({progressDetail[current]}/{progressDetail[total]})".format(
                                    **line
                                )
                            else:
                                docker_log_line += line["status"]

                            container.log_entries.create(
                                text=docker_log_line, user=user
                            )
                            job.add_log_entry(docker_log_line)

                        image_details = cli.inspect_image(
                            f"{container.repository}:{container.tag}"
                        )
                        container.image_id = image_details.get("Id")
                        container.save()
                        job.add_log_entry("Pulling image succeeded")
                        container.log_entries.create(
                            text="(Task) Pulling image succeeded", user=user
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
                    container.save()

                    # Starting container
                    container.log_entries.create(
                        text="(Task) Starting ...", user=user
                    )
                    job.add_log_entry("Starting container")
                    cli.start(container=container.container_id)
                    container.state = STATE_RUNNING
                    container.save()
                    job.add_log_entry("Starting container succeeded")
                    container.log_entries.create(
                        text="(Task) Starting succeeded", user=user
                    )

                elif job.action == ACTION_STOP:
                    # Stopping container
                    container.log_entries.create(
                        text="(Task) Stopping ...", user=user
                    )
                    job.add_log_entry("Stopping container")
                    cli.stop(container=container.container_id)
                    container.state = STATE_EXITED
                    container.save()
                    container.log_entries.create(
                        text="(Task) Stopping succeeded", user=user
                    )
                    job.add_log_entry("Stopping container succeeded")

                else:
                    if timeline:
                        tl_event.set_status("FAILED", "action failed")
                    container.log_entries.create(
                        text=f"(Task) Unknown action: {job.action}", user=user
                    )
                    raise RuntimeError(f"Unknown action: {job.action}")

                if timeline:
                    tl_event.set_status("OK", "action succeeded")

        except Exception:
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            container.log_entries.create(
                text="(Task) Action failed: {job.action}",
                user=user,
                level=LOG_LEVEL_ERROR,
            )
            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)
            raise  # re-raise
