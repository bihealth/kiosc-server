import logging

import docker
import docker.errors
import statemachine.exceptions

from django.conf import settings

from django.db import transaction
from django.utils import timezone

from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI

from config.celery import app
from django.contrib import auth

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from timeline.models import (
    TL_STATUS_SUBMIT,
    TL_STATUS_CANCEL,
    TL_STATUS_FAILED,
    TL_STATUS_OK,
)

from containers.models import (
    ContainerBackgroundJob,
    LOG_LEVEL_ERROR,
    STATE_EXITED,
    STATE_INITIAL,
    STATE_FAILED,
    STATE_TIMEOUT,
    LOG_LEVEL_WARNING,
    ContainerActionLock,
)
from containers.statemachines import (
    connect_docker,
    ContainerMachine,
    ActionSwitch,
)

User = auth.get_user_model()
app_settings = AppSettingAPI()
plugin_api = PluginAPI()
logger = logging.getLogger(__name__)

# Increase the timeout for communication with Docker daemon.
APP_NAME = 'containers'
DEFAULT_GRACE_PERIOD_CONTAINER_STATUS = 180

# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


class State:
    def __init__(self, state):
        self.state = state


def sync_container_state(container, timeline=None):
    # Update container state
    cli = connect_docker()
    try:
        data = cli.inspect_container(container.container_id)
        actual_state = data.get('State', {}).get('Status')
        if (
            container.state == STATE_TIMEOUT
            and actual_state != STATE_EXITED
            or container.state != STATE_TIMEOUT
            and actual_state != container.state
        ):
            logger.warning(
                '%s: Container state our of sync', container.sodar_uuid
            )
            container.date_last_status_update = timezone.now()
            container.state = actual_state
            container.save()
            if timeline:
                tl_event = timeline.add_event(
                    project=container.project,
                    app_name=APP_NAME,
                    user=None,
                    event_name='container_status_sync',
                    description='Needed to sync container state',
                    status_type=TL_STATUS_OK,
                )
                tl_event.add_object(
                    obj=container,
                    label='container',
                    name=container.get_display_name(),
                )
    except docker.errors.NullResource as ex:
        if container.state not in (STATE_INITIAL, STATE_FAILED):
            logger.error(
                'Failed to sync state: %s: %s (state is %s)',
                container.sodar_uuid,
                ex,
                container.state,
            )
            container.date_last_status_update = timezone.now()
            container.state = STATE_FAILED
            # container.container_id = ''
            container.save()
            if timeline:
                tl_event = timeline.add_event(
                    project=container.project,
                    app_name=APP_NAME,
                    user=None,
                    event_name='container_status_sync',
                    description=ex,
                    status_type=TL_STATUS_FAILED,
                )
                tl_event.add_object(
                    obj=container,
                    label='container',
                    name=container.get_display_name(),
                )
    except docker.errors.NotFound as ex:
        # We mark it as failed. STATE_DELETED could also be an option,
        # but failed is more general. Besides, the container record in the db
        # is NOT deleted.
        logger.error('Container not found: %s', str(ex))
        container.date_last_status_update = timezone.now()
        container.state = STATE_FAILED
        # container.container_id = ''
        container.save()
        if timeline:
            tl_event = timeline.add_event(
                project=container.project,
                app_name=APP_NAME,
                user=None,
                event_name='container_status_sync',
                description=ex,
                status_type=TL_STATUS_FAILED,
            )
            tl_event.add_object(
                obj=container,
                label='container',
                name=container.get_display_name(),
            )


@app.task(bind=True)
def container_task(_self, job_id):
    """Task to change a container state"""
    job = ContainerBackgroundJob.objects.get(pk=job_id)
    bg_job = job.bg_job
    timeline = plugin_api.get_backend_api('timeline_backend')
    container = job.container
    user = bg_job.user
    tl_event = None
    sync_container_state(container, timeline)

    cm = ContainerMachine(State(container.state), job=job)

    if timeline:
        tl_event = timeline.add_event(
            project=job.project,
            app_name=APP_NAME,
            user=user,
            event_name='container_task',
            description=f'{job.action} container {container.title}',
        )
        tl_event.add_object(
            obj=job.container,
            label='container',
            name=job.container.get_display_name(),
        )
        tl_event.add_object(
            obj=job,
            label='action',
            name=job.action,
        )
        tl_event.set_status(TL_STATUS_SUBMIT)

    acs = ActionSwitch(cm, job, tl_event)

    with job.marks():
        try:
            acs.do(job.action, job.container.state)
            tl_event.set_status(TL_STATUS_OK)

        except docker.errors.NotFound as e:
            logger.error(
                'Action "%s" failed (container %s not found from %s): %s',
                job.action,
                job.container.container_id,
                job.container.sodar_uuid,
                e,
            )
            job.add_log_entry(
                f'Action failed: {job.action}: {e}', level=LOG_LEVEL_ERROR
            )
            tl_event.set_status(TL_STATUS_FAILED, str(e))
            with transaction.atomic():
                job.container.refresh_from_db()
                # job.container.container_id = ''
                job.container.image_id = ''
                job.container.state = STATE_FAILED
                job.container.save()

        except docker.errors.DockerException as e:
            logger.error(
                'Action "%s" failed (Docker exception from %s): %s',
                job.action,
                job.container.sodar_uuid,
                e,
            )
            job.add_log_entry(
                f'Action failed: {job.action}: {e}', level=LOG_LEVEL_ERROR
            )
            tl_event.set_status(TL_STATUS_FAILED, str(e))
            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)

        except statemachine.exceptions.StateMachineError as e:
            logger.error(
                'Action "%s" failed (StateMachineError from %s): %s',
                job.action,
                job.container.sodar_uuid,
                e,
            )
            job.add_log_entry(
                f'Action failed: {job.action}: {e}', level=LOG_LEVEL_ERROR
            )
            tl_event.set_status(TL_STATUS_FAILED, str(e))

        except ContainerActionLock.CoolDown as e:
            logger.warning(
                'Action "%s" cancelled (CoolDown from %s): %s',
                job.action,
                job.container.sodar_uuid,
                e,
            )
            job.add_log_entry(
                f'Action cancelled due to cool down ({settings.KIOSC_DOCKER_ACTION_MIN_DELAY}s): {job.action}: {e}',
                level=LOG_LEVEL_WARNING,
            )
            tl_event.set_status(TL_STATUS_CANCEL)

        except Exception as e:
            logger.error(
                'Action "%s" failed (unexpected bug from %s): %s',
                job.action,
                job.container.sodar_uuid,
                e,
            )
            job.add_log_entry(
                f'Action failed: {job.action}: {e}', level=LOG_LEVEL_ERROR
            )
            tl_event.set_status(TL_STATUS_FAILED, str(e))

            with transaction.atomic():
                container.refresh_from_db()
                container.state = STATE_FAILED
                container.save(force_update=True)
