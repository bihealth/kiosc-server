from config.celery import app
from celery.schedules import crontab

from . import models


@app.task(bind=True)
def update_container_states(_self):
    models.update_container_states()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    # Mark starting/stopping tasks as running/stopped if they are so.
    sender.add_periodic_task(schedule=crontab(minute="*/1"), sig=update_container_states.s())
