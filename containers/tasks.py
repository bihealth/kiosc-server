import shlex

import docker
from django.conf import settings
from django.db import transaction
from docker.types import Ulimit

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

APP_NAME = "containers"

User = auth.get_user_model()


app_settings = AppSettingAPI()


# Increase the timeout for communication with Docker daemon.
DEFAULT_TIMEOUT = 600


def connect_docker(base_url="unix:///var/run/docker.sock"):
    return docker.APIClient(base_url=base_url, timeout=DEFAULT_TIMEOUT)


@app.task(bind=True)
def container_task(_self, job_id):
    """Task to change a container state"""

    job = ContainerBackgroundJob.objects.get(pk=job_id)

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
                        for line in cli.pull(
                            repository=container.repository,
                            tag=container.tag,
                            stream=True,
                            decode=True,
                        ):
                            if line.get("progressDetail"):
                                job.add_log_entry(
                                    "Docker log: {status} ({progressDetail[current]}/{progressDetail[total]})".format(
                                        **line
                                    )
                                )
                            else:
                                job.add_log_entry(
                                    f"Docker log: {line['status']}"
                                )
                        image_details = cli.inspect_image(
                            f"{container.repository}:{container.tag}"
                        )
                        container.image_id = image_details.get("Id")
                        container.save()
                        job.add_log_entry("Pulling image succeeded")

                    if not container.container_id:
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
                    cli.start(container=container.container_id)
                    container.state = STATE_RUNNING
                    container.save()
                elif job.action == ACTION_STOP:
                    # Stopping container
                    cli.stop(container=container.container_id)
                    container.state = STATE_EXITED
                    container.save()

                else:
                    raise RuntimeError(f"Unknown action: {job.action}")

        except Exception:
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )
            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)
            raise  # re-raise
