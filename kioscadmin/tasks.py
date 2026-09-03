import logging
from datetime import timedelta

import docker
import docker.errors

from bgjobs.models import BackgroundJob
from celery.schedules import crontab
from django.conf import settings

from django.utils import timezone

from containers.tasks import container_task, sync_container_state

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI

from containers.models import (
    Container,
    ContainerBackgroundJob,
    # STATE_FAILED,
    # STATE_INITIAL,
    # STATE_DELETED,
    # PROCESS_TASK,
    STATE_RUNNING,
    STATE_PAUSED,
    ACTION_TERMINATE,
)
from containers.statemachines import (
    connect_docker,
    # ACTION_TO_EXPECTED_STATE,
)

User = auth.get_user_model()
app_settings = AppSettingAPI()
plugin_api = PluginAPI()
logger = logging.getLogger(__name__)

# Increase the timeout for communication with Docker daemon.
APP_NAME = 'kioscadmin'
DEFAULT_GRACE_PERIOD_CONTAINER_STATUS = 180

# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


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

        state = data.get('State', {}).get('Status')

        if not state or state not in (STATE_RUNNING, STATE_PAUSED):
            continue

        # Get latest proxy access datetime (or start date if never accessed)
        last_access = container.date_last_access

        threshold = last_access + timedelta(
            days=min(
                container.inactivity_threshold,
                settings.KIOSC_DOCKER_MAX_INACTIVITY,
            )
        )

        if threshold < timezone.now():
            bg_job = BackgroundJob.objects.create(
                name='Terminate container',
                project=container.project,
                job_type=ContainerBackgroundJob.spec_name,
                user=User.objects.get(
                    username=settings.PROJECTROLES_DEFAULT_ADMIN
                ),
            )
            job = ContainerBackgroundJob.objects.create(
                action=ACTION_TERMINATE,
                project=container.project,
                container=container,
                bg_job=bg_job,
            )

            logger.warning(
                'Submitting job to terminate {}'.format(container.title)
            )

            container_task.apply_async(kwargs={'job_id': job.id}, countdown=0.5)

            msgs.append('Submitted job to terminate {}'.format(container.title))

    return msgs


@app.task(bind=True)
def poll_docker_status(_self):
    timeline = plugin_api.get_backend_api('timeline_backend')
    for container in Container.objects.all():
        sync_container_state(container, timeline)


@app.task(bind=True)
def prune_zombie_containers(_self):
    if settings.KIOSC_NETWORK_MODE != 'docker-shared':
        # Only run in docker-shared mode: we don't want to kill containers which
        # are not our own.
        return

    cli = connect_docker()
    for container in cli.containers(all=True):
        container_networks = container['NetworkSettings']['Networks']
        if len(container_networks) > 1 or not container_networks.get(
            settings.KIOSC_DOCKER_NETWORK
        ):
            # Leave this container alone, it doesn't belong to KIOSC
            # (or it is kiosc itself)
            continue

        try:
            container = Container.objects.get(container_id=container['Id'])
        except Container.DoesNotExist:
            logger.warning('Found zombie container: %s', container['Id'])
            # NOTE: this will also remove the volumes associated with the
            # container (thanks to the v=True flag in remove_container())
            cli.remove_container(container['Id'], force=True, v=True)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    sender.add_periodic_task(30, sig=poll_docker_status.s())
    sender.add_periodic_task(
        crontab(hour=1, minute=11), sig=stop_inactive_containers.s()
    )
    sender.add_periodic_task(
        crontab(hour='*', minute=30), sig=prune_zombie_containers.s()
    )
