import docker
from bgjobs.models import LOG_LEVEL_ERROR
from django.db import transaction

from dockerapps.models import (
    ImageBackgroundJob,
    STATE_INITIAL,
    STATE_FAILED,
    STATE_PULLING,
    STATE_IDLE,
    DockerImage,
)
from config.celery import app
from celery.schedules import crontab
from . import models


def connect_docker():
    return docker.APIClient(base_url="unix:///var/run/docker.sock")


@app.task(bind=True)
def pull_image(_self, job_id):
    """Trigger pulling of a Docker image and wait for the result."""
    job = ImageBackgroundJob.objects.get(pk=job_id)
    with job.marks():
        try:
            # Get image, check state, update to pulling.
            with transaction.atomic():
                image = job.image
                if image.state not in (STATE_INITIAL, STATE_FAILED, STATE_IDLE):
                    raise RuntimeError("Cannot pull image, invalid state: %s" % image.state)
                else:
                    image.state = STATE_PULLING
                    image.save()

            job.add_log_entry("Connecting to Docker API...")
            cli = connect_docker()
            job.add_log_entry("Pulling image %s/%s..." % (image.repository, image.tag))
            for line in cli.pull(
                repository=image.repository, tag=image.tag, stream=True, decode=True
            ):
                if line.get("progressDetail"):
                    job.add_log_entry(
                        "Docker log: {status} ({progressDetail[current]}/{progressDetail[total]})".format(
                            **line
                        )
                    )
                else:
                    job.add_log_entry("Docker log: {status}".format(**line))
            with transaction.atomic():
                image.refresh_from_db()
                image.state = STATE_IDLE
                image.save()
                job.add_log_entry("Pulling image succeeded")
        except Exception:
            job.add_log_entry("Pulling image failed", level=LOG_LEVEL_ERROR)
            with transaction.atomic():
                image.refresh_from_db()
                image.state = STATE_FAILED
                image.save(force_update=True)
            raise  # re-raise


@app.task(bind=True)
def control_container_state(_self, job_id):
    """Control container job state (start/stop/restart)."""


@app.task(bind=True)
def delete_image(_self, job_id):
    """Delete a Docker image, shut it down when necessary."""


@app.task(bind=True)
def update_container_states(_self):
    """Trigger container state updating (in database from Docker)."""
    models.update_container_states()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    # Mark starting/stopping tasks as running/stopped if they are so.
    sender.add_periodic_task(schedule=crontab(minute="*/1"), sig=update_container_states.s())
