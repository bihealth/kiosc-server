from config.celery import app
from celery.schedules import crontab

from . import models


@app.task(bind=True)
def pull_image(_self, job_id):
    """Trigger pulling of a Docker image and wait for the result."""


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
    sender.add_periodic_task(
        schedule=crontab(minute="*/1"), sig=update_container_states.s()
    )
