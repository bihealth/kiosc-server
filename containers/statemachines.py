import shlex

import docker
import docker.errors

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from docker.types import Ulimit
from statemachine import StateMachine, State

from containers.models import (
    STATE_CREATED,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_EXITED,
    STATE_DEAD,
    STATE_DELETING,
    STATE_DELETED,
    STATE_PULLING,
    STATE_INITIAL,
    STATE_FAILED,
    PROCESS_TASK,
    PROCESS_DOCKER,
    ACTION_START,
    ACTION_STOP,
    ACTION_RESTART,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    ACTION_DELETE,
)


# Increase the timeout for communication with Docker daemon.
APP_NAME = "containers"
DEFAULT_TIMEOUT_DOCKER_ACTION = 60


ACTION_TO_EXPECTED_STATE = {
    ACTION_START: STATE_RUNNING,
    ACTION_RESTART: STATE_RUNNING,
    ACTION_STOP: STATE_EXITED,
    ACTION_PAUSE: STATE_PAUSED,
    ACTION_UNPAUSE: STATE_RUNNING,
    ACTION_DELETE: STATE_DELETING,
}


def connect_docker(
    base_url="unix:///var/run/docker.sock",
    timeout=DEFAULT_TIMEOUT_DOCKER_ACTION,
):
    return docker.APIClient(base_url=base_url, timeout=timeout)


class ActionSwitch:
    def __init__(self, cm, job, tl_event):
        self.tl_event = tl_event
        self.cm = cm
        self.job = job
        self._switches = {
            ACTION_START: self._start,
            ACTION_STOP: self._stop,
            ACTION_PAUSE: self._pause,
            ACTION_UNPAUSE: self._unpause,
            ACTION_RESTART: self._restart,
            ACTION_DELETE: self._delete,
        }

    def _start(self, state):
        if state == STATE_INITIAL:
            self.cm.pull()
            self.cm.start_pulled()

        elif state == STATE_DELETED:
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_CREATED:
            self.cm.start_created()

        elif state == STATE_EXITED:
            self.cm.delete()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_FAILED:
            self.cm.pull_failed()
            self.cm.start_pulled()

        else:
            raise RuntimeError(f"Action start not allowed in state {state}")

    def _stop(self, state):
        if state == STATE_RUNNING:
            self.cm.stop_running()

        elif state == STATE_PAUSED:
            self.cm.stop_paused()

        else:
            raise RuntimeError(f"Action stop not allowed in state {state}")

    def _pause(self, state):
        if state == STATE_RUNNING:
            self.cm.pause()

        else:
            raise RuntimeError(f"Action pause not allowed in state {state}")

    def _unpause(self, state):
        if state == STATE_PAUSED:
            self.cm.unpause()

        else:
            raise RuntimeError(f"Action unpause not allowed in state {state}")

    def _restart(self, state):
        if state == STATE_RUNNING:
            self.cm.stop_running()
            self.cm.delete()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_EXITED:
            self.cm.delete()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        else:
            raise RuntimeError(f"Action restart not allowed in state {state}")

    def _delete(self, state):
        if state == STATE_INITIAL:
            # nothing to delete
            pass

        elif state == STATE_RUNNING:
            self.cm.stop_running()
            self.cm.delete()
            self.cm.delete_success()

        elif state == STATE_PAUSED:
            self.cm.stop_paused()
            self.cm.delete()
            self.cm.delete_success()

        elif state == STATE_EXITED:
            self.cm.delete()
            self.cm.delete_success()

        elif state == STATE_FAILED:
            self.cm.delete_failed()
            self.cm.delete_success()

        elif state == STATE_CREATED:
            self.cm.delete_created()
            self.cm.delete_success()

        elif state == STATE_DEAD:
            self.cm.delete_dead()
            self.cm.delete_success()

        elif state == STATE_PULLING:
            self.cm.delete_pulling()
            self.cm.delete_success()

        else:
            raise RuntimeError(f"Action delete not allowed in state {state}")

    def do(self, action, state):
        f = self._switches.get(action)

        if not f:
            if self.tl_event:
                self.tl_event.set_status("FAILED", "action failed")
                self.job.container.log_entries.create(
                    text=f"Unknown action: {action}",
                    process=PROCESS_TASK,
                    user=self.job.bg_job.user,
                )
            raise RuntimeError(f"Unknown action: {action}")

        if self.tl_event:
            self.tl_event.set_status("OK", "action succeeded")

        action_locks = self.cm.container.action_lock.all()

        if action_locks.count() == 0:
            self.cm.container.action_lock.create(action=action)

        elif action_locks.count() == 1:
            action_locks.first().lock(action)

        else:
            raise RuntimeError(
                f"Maximal one lock per container expected, got {action_locks.count()}"
            )

        with transaction.atomic():
            f(state)


class ContainerMachine(StateMachine):
    """State machine for Docker container status."""

    # States

    #: State when a newly created container fails to start (Docker state).
    created = State(STATE_CREATED)

    #: State when container is started and running (Docker state).
    running = State(STATE_RUNNING)

    #: State when container is paused (Docker state).
    paused = State(STATE_PAUSED)

    #: State when container is stopped (Docker state).
    exited = State(STATE_EXITED)

    #: State when a container failed to delete and was only partly removed (Docker state).
    dead = State(STATE_DEAD)

    #: State when the container hasn't been pulled yet.
    initial = State(STATE_INITIAL, initial=True)

    #: State when in the process of deleting.
    deleting = State(STATE_DELETING)

    #: State when container is deleted.
    deleted = State(STATE_DELETED)

    #: State when image is pulled.
    pulling = State(STATE_PULLING)

    #: State when container failed on action.
    failed = State(STATE_FAILED)

    # Transitions

    #: Transition when a freshly created container object is started (action: start).
    pull = initial.to(pulling)

    #: Transition when starting a deleted container (action: start).
    pull_deleted = deleted.to(pulling)

    #: Transition when starting a failed container (action: start).
    pull_failed = failed.to(pulling)

    #: Transition when switching from pulling to running (no action).
    start_pulled = pulling.to(running)

    #: Transition when a container is started that failed starting and has never been started before (action: start).
    start_created = created.to(running)

    #: Transition when starting an exited container (action: start).
    start_exited = exited.to(running)

    #: Transition when pausing a running container (action: pause).
    pause = running.to(paused)

    #: Transition when starting a paused container (action: unpause).
    unpause = paused.to(running)

    #: Transition when stopping a running container (action: stop).
    stop_running = running.to(exited)

    #: Transition when stopping a paused container (action: stop).
    stop_paused = paused.to(exited)

    #: Transition when deleting a stopped container (action: delete).
    delete = exited.to(deleting)

    #: Transition when successfully finishing deleting a container (no action).
    delete_success = deleting.to(deleted)

    #: Transition when deleting a failed container (action: delete).
    delete_failed = failed.to(deleting)

    #: Transition when deleting a created container (action: delete).
    delete_created = created.to(deleting)

    #: Transition when deleting a dead container (action: delete).
    delete_dead = dead.to(deleting)

    #: Transition when deleting a pulled container (action: delete).
    delete_pulling = pulling.to(deleting)

    #: Transition when a newly created container failed to start (no action).
    failed_start = pulling.to(created)

    #: Transition when a container is not completely deleted (no action).
    failed_delete = deleting.to(dead)

    # Every state can transition to failed.

    #: Transition ``initial`` to ``failed``
    failed_initial = initial.to(failed)

    #: Transition ``initial`` to ``failed``
    failed_pulling = pulling.to(failed)

    #: Transition ``running`` to ``failed``
    failed_running = running.to(failed)

    #: Transition ``exited`` to ``failed``
    failed_exited = exited.to(failed)

    #: Transition ``deleting`` to ``failed``
    failed_deleting = deleting.to(failed)

    #: Transition ``deleted`` to ``failed``
    failed_deleted = deleted.to(failed)

    #: Transition ``created`` to ``failed``
    failed_created = created.to(failed)

    #: Transition ``paused`` to ``failed``
    failed_paused = paused.to(failed)

    def __init__(self, *args, **kwargs):
        job = kwargs.pop("job")
        super().__init__(*args, **kwargs)
        self.container = job.container
        self.job = job
        self.user = job.bg_job.user

        # Connect to Docker
        self.job.add_log_entry("Connecting to Docker API...")
        self.cli = connect_docker(timeout=self.container.timeout)

    def _update_status(self, container_info=None):
        if not container_info:
            container_info = self.cli.inspect_container(
                self.container.container_id
            )

        if container_info.get("State"):
            self.container.state = container_info.get("State").get("Status")

        self.container.container_ip = (
            container_info.get("NetworkSettings", {})
            .get("Networks", {})
            .get(settings.KIOSC_DOCKER_NETWORK, {})
            .get("IPAddress")
        )
        self.container.save()

    def on_pull(self):
        # Pulling image
        self.job.add_log_entry(
            f"Pulling image {self.container.get_repos_full()} ..."
        )
        self.container.log_entries.create(
            text="Pulling image ...",
            process=PROCESS_TASK,
            user=self.user,
        )
        self.container.state = STATE_PULLING
        self.container.save()

        for line in self.cli.pull(
            repository=self.container.repository,
            tag=self.container.tag,
            stream=True,
            decode=True,
        ):
            if line.get("progressDetail"):
                docker_log_line = "{status} ({progressDetail[current]}/{progressDetail[total]})".format(
                    **line
                )
            else:
                docker_log_line = line["status"]

            self.container.log_entries.create(
                text=docker_log_line,
                process=PROCESS_DOCKER,
                date_docker_log=timezone.now(),
                user=self.user,
            )
            self.job.add_log_entry(docker_log_line)

        image_details = self.cli.inspect_image(self.container.get_repos_full())
        self.container.image_id = image_details.get("Id")
        self.container.save()
        self.job.add_log_entry("Pulling image succeeded")
        self.container.log_entries.create(
            text="Pulling image succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )

        options = {}
        options_host_config = {}

        if settings.KIOSC_NETWORK_MODE == "docker-shared":
            options["networking_config"] = self.cli.create_networking_config(
                {
                    settings.KIOSC_DOCKER_NETWORK: self.cli.create_endpoint_config()
                }
            )

        if settings.KIOSC_NETWORK_MODE == "host":
            options_host_config["port_bindings"] = {
                self.container.container_port: self.container.host_port
            }

        environment = (
            dict(self.container.environment)
            if self.container.environment
            else {}
        )
        url_prefix = reverse(
            "containers:proxy",
            kwargs={
                "container": self.container.sodar_uuid,
                "path": self.container.container_path or "",
            },
        )

        for key, value in environment.items():
            if "__KIOSC_URL_PREFIX__" in value:
                environment[key] = value.replace(
                    "__KIOSC_URL_PREFIX__", url_prefix
                )

        environment.update(
            {
                "CONTAINER_PORT": self.container.container_port,
                "TITLE": self.container.title,
                "DESCRIPTION": self.container.description or "",
            }
        )

        # Create container
        container_info = self.cli.create_container(
            detach=True,
            image=self.container.image_id,
            environment=environment,
            command=shlex.split(self.container.command)
            if self.container.command
            else None,
            ports=[self.container.container_port],
            host_config=self.cli.create_host_config(
                ulimits=[
                    Ulimit(
                        name="nofile",
                        soft=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                        hard=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                    )
                ],
                **options_host_config,
            ),
            **options,
        )
        self.container.container_id = container_info.get("Id")
        self.container.save()
        self._update_status(container_info)

    def on_pull_deleted(self):
        self.on_pull()

    def on_pull_failed(self):
        self.on_pull()

    def on_start_pulled(self):
        # Starting container
        self.container.log_entries.create(
            text="Starting ...", process=PROCESS_TASK, user=self.user
        )
        self.job.add_log_entry("Starting container")
        self.cli.start(self.container.container_id)
        self._update_status()
        self.job.add_log_entry("Starting container succeeded")
        self.container.log_entries.create(
            text="Starting succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )

    def on_start_created(self):
        self.on_start_pulled()

    def on_start_exited(self):
        self.on_start_pulled()

    def on_pause(self):
        self.container.log_entries.create(
            text="Pausing ...", process=PROCESS_TASK, user=self.user
        )
        self.job.add_log_entry("Pausing container")
        self.cli.pause(self.container.container_id)
        self._update_status()
        self.job.add_log_entry("Pausing container succeeded")
        self.container.log_entries.create(
            text="Pausing succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )

    def on_unpause(self):
        self.container.log_entries.create(
            text="Unpausing ...", process=PROCESS_TASK, user=self.user
        )
        self.job.add_log_entry("Unpausing container")
        self.cli.unpause(self.container.container_id)
        self._update_status()
        self.job.add_log_entry("Unpausing container succeeded")
        self.container.log_entries.create(
            text="Unpausing succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )

    def on_stop_running(self):
        self.container.log_entries.create(
            text="Stopping ...", process=PROCESS_TASK, user=self.user
        )
        self.job.add_log_entry("Stopping container")

        # Stopping container and updating status
        self.cli.stop(self.container.container_id)
        self._update_status()

        self.container.log_entries.create(
            text="Stopping succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )
        self.job.add_log_entry("Stopping container succeeded")

    def on_stop_paused(self):
        self.on_stop_running()

    def on_delete(self):
        self.container.log_entries.create(
            text="Deleting ...", process=PROCESS_TASK, user=self.user
        )
        self.job.add_log_entry("Deleting container")
        self.container.state = STATE_DELETING
        self.container.save()

        # Removing container and erasing container_id
        try:
            self.cli.remove_container(self.container.container_id)

        except docker.errors.NullResource:
            self.container.log_entries.create(
                text="Empty container ID, don't know what to delete. Continuing.",
                process=PROCESS_TASK,
                user=self.user,
            )

        except docker.errors.NotFound:
            self.container.log_entries.create(
                text=f"Container with {self.container.container_id} not found, nothing to delete",
                process=PROCESS_TASK,
                user=self.user,
            )

    def on_delete_failed(self):
        self.on_delete()

    def on_delete_created(self):
        self.on_delete()

    def on_delete_dead(self):
        self.on_delete()

    def on_delete_pulling(self):
        self.on_delete()

    def on_delete_success(self):
        self.container.state = STATE_DELETED
        self.container.container_id = None
        self.container.save()

        self.container.log_entries.create(
            text="Deleting succeeded",
            process=PROCESS_TASK,
            user=self.user,
        )
        self.job.add_log_entry("Deleting container succeeded")
