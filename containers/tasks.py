import json
import logging
import ssl
import traceback
import urllib.request
from datetime import timedelta

import docker
import docker.errors
import dateutil.parser
import statemachine.exceptions
from django.urls import reverse

from bgjobs.models import LOG_LEVEL_DEBUG, BackgroundJob
from celery.schedules import crontab
from django.conf import settings

from django.db import transaction
from django.utils import timezone

from projectroles.models import SODAR_CONSTANTS, RemoteSite
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
    ContainerActionLock,
    PROCESS_PROXY,
    STATE_RUNNING,
    STATE_PAUSED,
    ACTION_STOP,
)
from containers.statemachines import (
    ContainerMachine,
    connect_docker,
    ActionSwitch,
    ACTION_TO_EXPECTED_STATE,
)
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION

User = auth.get_user_model()
app_settings = AppSettingAPI()
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


@app.task(bind=True)
def stop_inactive_containers(_self):
    cli = connect_docker()

    for container in Container.objects.all():
        if not container.container_id:
            continue

        # Check if container exists
        try:
            data = cli.inspect_container(container.container_id)

        except docker.errors.NotFound:
            continue

        else:
            state = data.get("State", {}).get("Status")

            if not state or state not in (STATE_RUNNING, STATE_PAUSED):
                continue

            # Get latest proxy entry
            obj = (
                container.log_entries.filter(process=PROCESS_PROXY)
                .order_by("-date_created")
                .first()
            )

            if obj:
                last_access = obj.date_created

            else:
                continue

            threshold = last_access + timedelta(
                days=min(
                    container.inactivity_threshold,
                    settings.KIOSC_DOCKER_MAX_INACTIVITY,
                )
            )

            if threshold < timezone.now():
                bg_job = BackgroundJob.objects.create(
                    name="Stop container",
                    project=container.project,
                    job_type=ContainerBackgroundJob.spec_name,
                    user=User.objects.get(
                        username=settings.PROJECTROLES_DEFAULT_ADMIN
                    ),
                )
                job = ContainerBackgroundJob.objects.create(
                    action=ACTION_STOP,
                    project=container.project,
                    container=container,
                    bg_job=bg_job,
                )

                container_task.apply_async(
                    kwargs={"job_id": job.id}, countdown=0.5
                )


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


@app.task(bind=True)
def sync_upstream(_self):
    if getattr(settings, "PROJECTROLES_DISABLE_CATEGORIES", False):
        logger.info(
            "Project categories and nesting disabled, " "remote sync disabled"
        )
        return

    if settings.PROJECTROLES_SITE_MODE != SITE_MODE_TARGET:
        logger.error("Site not in TARGET mode, unable to sync")
        return

    try:
        site = RemoteSite.objects.get(mode=SITE_MODE_SOURCE)

    except RemoteSite.DoesNotExist:
        logger.error("No source site defined, unable to sync")
        return

    if getattr(settings, "PROJECTROLES_ALLOW_LOCAL_USERS", False):
        logger.info(
            "PROJECTROLES_ALLOW_LOCAL_USERS=True, will sync "
            "roles for existing local users"
        )

    logger.info(
        'Retrieving data from remote site "{}" ({})..'.format(
            site.name, site.get_url()
        )
    )

    api_url = site.get_url() + reverse(
        "projectroles:api_remote_get", kwargs={"secret": site.secret}
    )

    try:
        api_req = urllib.request.Request(api_url)
        api_req.add_header(
            "accept",
            "{}; version={}".format(
                CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION
            ),
        )
        response = urllib.request.urlopen(api_req)
        remote_data = json.loads(response.read())

    except Exception as ex:
        helper_text = ""
        if (
            isinstance(ex, urllib.error.URLError)
            and isinstance(ex.reason, ssl.SSLError)
            and ex.reason.reason == "WRONG_VERSION_NUMBER"
        ):
            helper_text = " (most likely server cannot handle HTTPS requests)"

        logger.error(
            "Unable to retrieve data from remote site: {}{}".format(
                ex, helper_text
            )
        )
        return

    remote_api = RemoteProjectAPI()
    try:
        remote_api.sync_source_data(site, remote_data)

    except Exception as ex:
        logger.error("Remote sync cancelled with exception: {}".format(ex))
        return


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    sender.add_periodic_task(30, sig=poll_docker_status_and_logs.s())
    sender.add_periodic_task(
        60, sig=sync_container_state_with_last_user_action.s()
    )
    sender.add_periodic_task(
        crontab(hour=1, minute=11), sig=stop_inactive_containers.s()
    )
    sender.add_periodic_task(300, sig=sync_upstream.s())
