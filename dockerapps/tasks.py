from datetime import datetime, timedelta
import shlex
import time
import sys

import docker
from bgjobs.models import LOG_LEVEL_ERROR
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from dockerapps.models import (
    ImageBackgroundJob,
    STATE_INITIAL,
    STATE_FAILED,
    STATE_PULLING,
    STATE_IDLE,
    STATE_STOPPING,
    STATE_STARTING,
    STATE_RUNNING,
    ContainerStateControlBackgroundJob,
    DockerProcess,
)
from config.celery import app
from celery.schedules import crontab
from . import models


# Increase the timeout for communication with Docker daemon.
DEFAULT_TIMEOUT = 600


def connect_docker(base_url="unix:///var/run/docker.sock"):
    return docker.APIClient(base_url=base_url, timeout=DEFAULT_TIMEOUT)


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
            if image.username or image.password:
                job.add_log_entry(
                    "Logging into registry %s" % (image.registry or "https://index.docker.io/v1/")
                )
                res = cli.login(
                    username=image.username or None,
                    password=image.password or None,
                    registry=image.registry,
                )
                job.add_log_entry("Login results: %s" % res)
            job.add_log_entry("Pulling image %s:%s..." % (image.repository, image.tag))
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
            image_details = cli.inspect_image("%s:%s" % (image.repository, image.tag))
            with transaction.atomic():
                image.refresh_from_db()
                image.image_id = image_details.get("Id")
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


#: Timeout (in seconds) to wait for job to change state.
TIMEOUT_STATE_CHANGE = 30
#: The step length to sleep (in seconds).
SLEEP_TIME = 0.1


class ContainerStateControllerHelper:
    """Helper class that helps controlling job state.

    The main purpose is to be structure the job control actions into different functions.
    """

    def __init__(self, job_id, timeout=TIMEOUT_STATE_CHANGE, sleep_time=SLEEP_TIME):
        #: The ID of the job to use for getting image (and process) from.
        self.job_id = job_id
        #: The timeout (in seconds).
        self.timeout = timeout
        #: The sleep time (in seconds)
        self.sleep_time = sleep_time
        #: The job to run for.
        self.job = ContainerStateControlBackgroundJob.objects.get(pk=self.job_id)
        #: The project that the objects are contained in.
        self.process = self.job.process
        #: The process to run for.
        self.process = self.job.process
        #: The image to run for.
        self.image = self.process.image
        #: The Docker APIClient to use
        self.cli = connect_docker()

    def run(self):
        """Apply the job state change, running in context manager ``self.job.mark()``."""
        with self.job.marks():
            try:
                {"start": self._run_start, "restart": self._run_restart, "stop": self._run_stop}[
                    self.job.action
                ]()
            except Exception:
                with transaction.atomic():
                    self.job.process.state = STATE_FAILED
                    self.job.process.save()
                raise  # re-raise

    def _run_start(self):
        """Run "start" action job (without context manager)."""
        self._run_start_wait_stopping()
        self._run_start_start()

    def _run_start_wait_stopping(self):
        """Wait for the job to stop if stopping"""
        if self.process.state == STATE_STOPPING:
            self.job.add_log_entry(
                "Process is stopping. Waiting up to %d sec for it to finish." % TIMEOUT_STATE_CHANGE
            )
            timeout_start = time.time()
            while time.time() < timeout_start + TIMEOUT_STATE_CHANGE:
                self.process.refresh_from_db()
                if self.process.state != STATE_STOPPING:
                    self.job.add_log_entry("Process stopping finished.")
                    break  # else will not be run
                time.sleep(self.sleep_time)
            else:
                self.job.add_log_entry("Did not stop on time.")

    def _run_start_start(self):
        """Start the container and wait for it to finish starting"""
        # Get the value of the URL prefix that the app will have to the outside.
        url_prefix = reverse(
            "dockerapps:docker-proxy",
            kwargs={
                "project": self.process.project.sodar_uuid,
                "image": self.image.sodar_uuid,
                "process": self.image.process.sodar_uuid,
                "path": "",
            },
        )

        with transaction.atomic():
            self.process.refresh_from_db()
            if self.process.state in (STATE_IDLE, STATE_FAILED):
                self.job.add_log_entry(
                    "Starting container for %s:%s..." % (self.image.repository, self.image.tag)
                )
                # Build environment, interpreting placeholders.
                environment = {}
                for entry in self.process.environment:
                    if "__KIOSC_URL_PREFIX__" in entry["value"]:
                        environment[entry["name"]] = entry["value"].replace(
                            "__KIOSC_URL_PREFIX__", url_prefix
                        )
                    else:
                        environment[entry["name"]] = entry["value"]
                # Create and start the Docker container, update database record.
                container = self.cli.create_container(
                    detach=True,
                    image=self.image.image_id,
                    environment=environment,
                    command=shlex.split(self.process.command) if self.process.command else None,
                    ports=[self.process.internal_port],
                    host_config=self.cli.create_host_config(
                        port_bindings={self.process.internal_port: self.process.host_port}
                    ),
                )
                self.cli.start(container=container.get("Id"))
                self.process.container_id = container.get("Id")
                self.process.state = STATE_STARTING
                self.process.save()
            else:
                self.job.add_log_entry(
                    "Process state is %s, not attempting to start" % self.process.state
                )
        self.job.add_log_entry("Waiting for container to start...")
        timeout_start = time.time()
        while time.time() < timeout_start + self.timeout:
            if (
                self.cli.inspect_container(self.process.container_id)
                .get("State", {})
                .get("Running")
            ):
                self.job.add_log_entry("Container is running...")
                with transaction.atomic():
                    self.process.refresh_from_db()
                    self.process.state = STATE_RUNNING
                    self.process.save()
                break
            time.sleep(self.sleep_time)
        else:
            raise RuntimeError("Container did not start on time")

    def _run_stop(self):
        """Run "stop" action job (without context manager)."""
        self._run_stop_wait()
        self._run_stop_stop()

    def _run_stop_wait(self):
        """Wait for starting/stopping job to be done."""
        if self.process.state in (STATE_STARTING, STATE_STOPPING):
            old_state = self.process.state
            self.job.add_log_entry(
                "Process is %s. Waiting up to %d sec for it to finish."
                % (old_state, TIMEOUT_STATE_CHANGE)
            )
            timeout_start = time.time()
            while time.time() < timeout_start + TIMEOUT_STATE_CHANGE:
                self.process.refresh_from_db()
                if self.process.state != STATE_STOPPING:
                    self.job.add_log_entry("Process %s finished." % old_state)
                    break  # else will not be run
                time.sleep(self.sleep_time)
            else:
                self.job.add_log_entry("Did not finish %s on time." % old_state)

    def _run_stop_stop(self):
        """Stop the container and wait for it to finish stopping."""
        self.process.refresh_from_db()
        if self.process.state in (STATE_RUNNING, STATE_STARTING, STATE_STOPPING):
            self.job.add_log_entry(
                "Stopping container for %s:%s..." % (self.image.repository, self.image.tag)
            )
            with transaction.atomic():
                self.process.refresh_from_db()
                self.process.state = STATE_STOPPING
                self.process.save()
            container = self.cli.inspect_container(self.process.container_id)
            self.cli.stop(container=container.get("Id"), timeout=self.timeout)
            with transaction.atomic():
                self.process.refresh_from_db()
                self.process.state = STATE_IDLE
                self.process.save()
        else:
            self.job.add_log_entry(
                "Process state is %s, not attempting to stop" % self.process.state
            )

    def _run_restart(self):
        """Run "restart" action job (without context manager)."""
        if self.process.state in (STATE_IDLE, STATE_FAILED):
            self.job.add_log_entry("Container not running, just starting")
            self._run_start_start()
        else:
            self.job.add_log_entry("Stopping container for restart.")
            self._run_stop()
            self.job.add_log_entry("Starting container for restart.")
            self._run_start()
            self.job.add_log_entry(
                "Done restarting process for %s:%s" % (self.image.repository, self.image.tag)
            )


@app.task(bind=True)
def control_container_state(_self, job_id):
    """Control container job state (start/stop/restart)."""
    return ContainerStateControllerHelper(job_id).run()


@app.task(bind=True)
def delete_image(_self, job_id):
    """Delete a Docker image, shut it down when necessary."""


@app.task(bind=True)
def update_container_states(_self):
    """Trigger container state updating (in database from Docker)."""
    models.update_container_states()


@app.task(bind=True)
def update_docker_logs(_self):
    """Trigger pulling updated docker locks."""
    cli = connect_docker()
    for process in DockerProcess.objects.all():
        print("Updating logs for %s" % process, file=sys.stderr)
        with transaction.atomic():
            process.refresh_from_db()
            start_logs = process.date_last_logs
            end_logs = timezone.now()
            if process.container_id:
                content = cli.logs(
                    container=process.container_id,
                    timestamps=True,
                    since=int(datetime.timestamp(start_logs)),
                    until=int(datetime.timestamp(end_logs)),
                )
                print("Logs are: %s" % content, file=sys.stderr)
                if content:
                    process.processlogchunk_set.create(content=content)
            process.date_last_logs = end_logs
            process.save()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """Register periodic tasks"""
    # TODO: need recurring task for looking whether containers are still running
    # Mark starting/stopping tasks as running/stopped if they are so.
    sender.add_periodic_task(schedule=crontab(minute="*/1"), sig=update_container_states.s())
    # Get log from docker container.
    sender.add_periodic_task(schedule=timedelta(seconds=5), sig=update_docker_logs.s())
