import logging
import traceback

import docker
import docker.errors
import statemachine.exceptions

from bgjobs.models import LOG_LEVEL_DEBUG
from django.conf import settings

from django.db import transaction
from django.utils import timezone

from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from containers.models import (
    ContainerBackgroundJob,
    LOG_LEVEL_ERROR,
    STATE_FAILED,
    PROCESS_TASK,
    PROCESS_DOCKER,
    LOG_LEVEL_WARNING,
    ContainerActionLock,
)
from containers.statemachines import (
    ContainerMachine,
    ActionSwitch,
)

User = auth.get_user_model()
app_settings = AppSettingAPI()
plugin_api = PluginAPI()
logger = logging.getLogger(__name__)

# Increase the timeout for communication with Docker daemon.
APP_NAME = "containers"
DEFAULT_GRACE_PERIOD_CONTAINER_STATUS = 180

# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS["SITE_MODE_TARGET"]
SITE_MODE_SOURCE = SODAR_CONSTANTS["SITE_MODE_SOURCE"]


class State:
    def __init__(self, state):
        self.state = state


@app.task(bind=True)
def container_task(_self, job_id):
    """Task to change a container state"""
    job = ContainerBackgroundJob.objects.get(pk=job_id)
    timeline = plugin_api.get_backend_api("timeline_backend")
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

        except ContainerActionLock.CoolDown:
            job.add_log_entry(
                f"Action not performed: {job.action} (cool-down)",
                level=LOG_LEVEL_WARNING,
            )
            container.log_entries.create(
                text=f"Action not performed: {job.action}. Cool-down is active ({settings.KIOSC_DOCKER_ACTION_MIN_DELAY}s)",
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_WARNING,
            )

        except Exception as e:
            # Catch all exceptions that are not coming from Docker
            job.add_log_entry(
                f"Action failed: {job.action}", level=LOG_LEVEL_ERROR
            )

            for line in traceback.format_exc().split("\n"):
                container.log_entries.create(
                    text=line,
                    process=PROCESS_TASK,
                    user=user,
                    level=LOG_LEVEL_DEBUG,
                )

            container.log_entries.create(
                text="Action failed: {}{}".format(
                    job.action, f" ({str(e)})" if str(e) else ""
                ),
                process=PROCESS_TASK,
                user=user,
                level=LOG_LEVEL_ERROR,
            )

            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)
