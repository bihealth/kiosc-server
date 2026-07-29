from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import shlex

import docker
import docker.errors
import logging

from django.conf import settings
from django.urls import reverse
from docker.types import Ulimit
from statemachine import StateMachine, State
from statemachine.exceptions import StateMachineError

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
    STATE_TERMINATED,
    PROCESS_TASK,
    ACTION_START,
    ACTION_STOP,
    ACTION_TERMINATE,
    ACTION_RESTART,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    ACTION_DELETE,
)

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()

# Increase the timeout for communication with Docker daemon.
APP_NAME = 'containers'
DEFAULT_TIMEOUT_DOCKER_ACTION = 60


ACTION_TO_EXPECTED_STATE = {
    ACTION_START: STATE_RUNNING,
    ACTION_RESTART: STATE_RUNNING,
    ACTION_STOP: STATE_EXITED,
    ACTION_TERMINATE: STATE_EXITED,
    ACTION_PAUSE: STATE_PAUSED,
    ACTION_UNPAUSE: STATE_RUNNING,
    ACTION_DELETE: STATE_DELETING,
}


def connect_docker(
    base_url='unix:///var/run/docker.sock',
    timeout=DEFAULT_TIMEOUT_DOCKER_ACTION,
):
    return docker.APIClient(base_url=base_url, timeout=timeout)


class ActionSwitch:
    """
    State machine to switch container state.

    Exceptions raised here are caught by ``containers.tasks.container_task()``.
    """

    def __init__(self, cm, job, tl_event):
        self.tl_event = tl_event
        self.cm = cm
        self.job = job
        self._switches = {
            ACTION_START: self._start,
            ACTION_STOP: self._stop,
            ACTION_TERMINATE: self._terminate,
            ACTION_PAUSE: self._pause,
            ACTION_UNPAUSE: self._unpause,
            ACTION_RESTART: self._restart,
            ACTION_DELETE: self._delete,
        }

    def _start(self, state):
        try:
            if state == STATE_INITIAL:
                self.cm.pull()
                self.cm.start_pulled()

            elif state == STATE_DELETED:
                self.cm.pull_deleted()
                self.cm.start_pulled()

            elif state == STATE_CREATED:
                self.cm.start_created()

            elif state == STATE_EXITED:
                # self.cm.delete_exited()
                # self.cm.delete_success()
                # self.cm.pull_deleted()
                self.cm.start_exited()

            elif state == STATE_TERMINATED:
                self.cm.start_terminated()

            elif state == STATE_FAILED:
                self.cm.delete_failed()
                self.cm.delete_success()
                self.cm.pull_deleted()
                self.cm.start_pulled()

            elif state == STATE_RUNNING:
                # Nothing to do, but we don't want to raise an exception
                pass

            else:
                raise StateMachineError(
                    f'Action start not allowed in state {state}'
                )
        except Exception as ex:
            self.job.add_log_entry(f'Failed to start container: {ex}')
            self.job.container.log_entries.create(
                text=f'Failed to start container: {ex}\n',
                process=PROCESS_TASK,
                user=self.job.bg_job.user,
            )
            async_to_sync(channel_layer.group_send)(
                str(self.job.container.sodar_uuid),
                {
                    'type': 'container_task.message',
                    'text': f'Failed to start container: {ex}\n',
                },
            )
            raise ex

    def _stop(self, state):
        if state == STATE_RUNNING:
            self.cm.stop_running()

        elif state == STATE_PAUSED:
            self.cm.stop_paused()

        elif state == STATE_EXITED:
            pass

        else:
            raise StateMachineError(f'Action stop not allowed in state {state}')

    def _terminate(self, state):
        if state == STATE_RUNNING:
            self.cm.terminate_running()

        elif state == STATE_PAUSED:
            self.cm.terminate_paused()

        else:
            raise StateMachineError(
                f'Action terminate not allowed in state {state}'
            )

    def _pause(self, state):
        if state == STATE_RUNNING:
            self.cm.pause()

        else:
            raise StateMachineError(
                f'Action pause not allowed in state {state}'
            )

    def _unpause(self, state):
        if state == STATE_PAUSED:
            self.cm.unpause()

        else:
            raise StateMachineError(
                f'Action unpause not allowed in state {state}'
            )

    def _restart(self, state):
        if state == STATE_INITIAL:
            self.cm.pull()
            self.cm.start_pulled()

        elif state == STATE_CREATED:
            self.cm.delete_created()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_RUNNING:
            self.cm.stop_running()
            self.cm.delete_exited()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_PAUSED:
            self.cm.stop_paused()
            self.cm.delete_exited()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_EXITED:
            self.cm.delete_exited()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_TERMINATED:
            self.cm.delete_terminated()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        elif state == STATE_FAILED:
            self.cm.delete_failed()
            self.cm.delete_success()
            self.cm.pull_deleted()
            self.cm.start_pulled()

        else:
            raise StateMachineError(
                f'Action restart not allowed in state {state}'
            )

    def _delete(self, state):
        if state == STATE_INITIAL:
            # nothing to delete
            pass

        elif state == STATE_RUNNING:
            self.cm.stop_running()
            self.cm.delete_exited()
            self.cm.delete_success()

        elif state == STATE_PAUSED:
            self.cm.stop_paused()
            self.cm.delete_exited()
            self.cm.delete_success()

        elif state == STATE_EXITED:
            self.cm.delete_exited()
            self.cm.delete_success()

        elif state == STATE_TERMINATED:
            self.cm.delete_terminated()
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
            raise StateMachineError(
                f'Action delete not allowed in state {state}'
            )

    def do(self, action, state):
        f = self._switches.get(action)

        if not f:
            raise StateMachineError(f'Unknown action: {action}')

        action_locks = self.cm.container.action_lock.all()

        if action_locks.count() == 0:
            self.cm.container.action_lock.create(action=action)

        elif action_locks.count() == 1:
            action_locks.first().lock(action)

        else:
            raise RuntimeError(
                f'Maximal one lock per container expected, got {action_locks.count()}'
            )

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

    #: State when container is stopped due to inactivity.
    terminated = State(STATE_TERMINATED)

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

    #: Transition when starting a terminated container (action: start).
    start_terminated = terminated.to(running)

    #: Transition when pausing a running container (action: pause).
    pause = running.to(paused)

    #: Transition when starting a paused container (action: unpause).
    unpause = paused.to(running)

    #: Transition when stopping a running container (action: stop).
    stop_running = running.to(exited)

    #: Transition when stopping a paused container (action: stop).
    stop_paused = paused.to(exited)

    #: Transition when timing out a running container (action: terminate).
    terminate_running = running.to(terminated)

    #: Transition when timing out a paused container (action: terminate).
    terminate_paused = paused.to(terminated)

    #: Transition when deleting an exited container (action: delete).
    delete_exited = exited.to(deleting)

    #: Transition when deleting a terminated container (action: delete).
    delete_terminated = terminated.to(deleting)

    #: Transition when deleting a failed container (action: delete).
    delete_failed = failed.to(deleting)

    #: Transition when deleting a created container (action: delete).
    delete_created = created.to(deleting)

    #: Transition when deleting a dead container (action: delete).
    delete_dead = dead.to(deleting)

    #: Transition when deleting a pulled container (action: delete).
    delete_pulling = pulling.to(deleting)

    #: Transition when successfully finishing deleting a container (no action).
    delete_success = deleting.to(deleted)

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

    #: Transition ``terminated`` to ``failed``
    failed_terminated = terminated.to(failed)

    #: Transition ``deleting`` to ``failed``
    failed_deleting = deleting.to(failed)

    #: Transition ``deleted`` to ``failed``
    failed_deleted = deleted.to(failed)

    #: Transition ``created`` to ``failed``
    failed_created = created.to(failed)

    #: Transition ``paused`` to ``failed``
    failed_paused = paused.to(failed)

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job')
        super().__init__(*args, **kwargs)
        self.container = job.container
        self.job = job
        self.user = job.bg_job.user

        # Connect to Docker
        self.job.add_log_entry('Connecting to Docker API...')
        self.cli = connect_docker(timeout=self.container.timeout)

    def _update_status(self, container_info=None):
        if not container_info:
            container_info = self.cli.inspect_container(
                self.container.container_id
            )

        if container_info.get('State'):
            self.container.state = container_info.get('State').get('Status')

        self.container.container_ip = (
            container_info.get('NetworkSettings', {})
            .get('Networks', {})
            .get(settings.KIOSC_DOCKER_NETWORK, {})
            .get('IPAddress')
        )
        self.container.save()

    def _log_task(self, text):
        """Add logs for the current task.

        In general, logs must be added in three places:

        - The background job;
        - The channel layer, so that they are forwarded in real time
          to the ContainerWatcherConsumer;
        - The database, so that they are stored with persistence.
        """
        self.job.add_log_entry(text)
        textnl = text + '\n'
        self.container.log_entries.create(
            text=textnl,
            process=PROCESS_TASK,
            user=self.user,
        )
        async_to_sync(channel_layer.group_send)(
            str(self.container.sodar_uuid),
            {
                'type': 'container_task.message',
                'text': textnl,
            },
        )

    def on_pull(self):
        # Pulling image
        self.container.state = STATE_PULLING
        self.container.container_id = None
        self.container.save()

        if self.container.repository.startswith(
            str(self.container.project.sodar_uuid)
        ):
            registry = settings.KIOSC_CUSTOM_REGISTRY_DOCKER_URL
            image_repository = f'{registry}/{self.container.repository}'
            image_reference = f'{registry}/{self.container.get_repos_full()}'
        else:
            image_repository = self.container.repository
            image_reference = self.container.get_repos_full()

        need_to_pull = True
        for image in self.cli.images(self.container.repository):
            if image_reference in image['RepoTags']:
                need_to_pull = False
                break

        if need_to_pull:
            self._log_task(
                f'Pulling image {self.container.get_repos_full()} ...'
            )
            need_to_login = self.container.registry_user is not None
            if need_to_login:
                try:
                    image_registry = self.container.repository.split('/', 1)[0]
                    logger.info(
                        'Logging in to registry %s for %s/%s on behalf of %s',
                        image_registry,
                        self.container.project.title,
                        self.container.title,
                        self.user,
                    )
                    self._log_task(
                        f'Logging in to registry {image_registry} with user credentials...'
                    )
                    self.cli.login(
                        self.container.registry_user,
                        self.container.registry_password,
                        registry=image_registry,
                    )
                    self._log_task('Logged in successfully.')
                except Exception as ex:
                    logger.error('Failed to login to registry: %s', ex)
                    self._log_task(f'Login failed: {ex}')
                    raise ex
            for line in self.cli.pull(
                repository=image_repository,
                tag=self.container.tag,
                stream=True,
                decode=True,
            ):
                pull_log = {'text': line.get('status', line.get('error'))}
                if (line_id := line.get('id')) and (
                    line_progress := line.get('progressDetail')
                ):
                    pull_log['id'] = line_id
                    pull_log['status'] = f'{line_id}: {line.get("status")}'
                    if line_progress.get('current') and line_progress.get(
                        'total'
                    ):
                        pull_log['status'] += (
                            f' [{line_progress.get("current")}/{line_progress.get("total")}]'
                        )
                    elif line_progress.get('current') and line_progress.get(
                        'units'
                    ):
                        pull_log['status'] += (
                            f' [{line_progress.get("current")}{line_progress.get("units")}]'
                        )
                    else:
                        # We create persistent log entries only for status lines
                        # that don't change
                        self.container.log_entries.create(
                            text=pull_log['status'] + '\n',
                            process=PROCESS_TASK,
                            user=self.user,
                        )
                        self.job.add_log_entry(pull_log['status'])
                else:
                    pull_log_status = line.get('status', line.get('error'))
                    pull_log = {'status': pull_log_status}
                    self.container.log_entries.create(
                        text=pull_log_status + '\n',
                        process=PROCESS_TASK,
                        user=self.user,
                    )
                    self.job.add_log_entry(pull_log_status)

                async_to_sync(channel_layer.group_send)(
                    str(self.container.sodar_uuid),
                    {
                        'type': 'container_pull.message',
                        **pull_log,
                    },
                )
            self._log_task('Pulling image succeeded')
        else:
            self._log_task(
                f'Using cached image for {self.container.get_repos_full()}'
            )

        image_details = self.cli.inspect_image(image_reference)
        self.container.image_id = image_details.get('Id')
        self.container.save()

        options = {}
        options_host_config = {}

        if settings.KIOSC_NETWORK_MODE == 'docker-shared':
            options['networking_config'] = self.cli.create_networking_config(
                {
                    settings.KIOSC_DOCKER_NETWORK: self.cli.create_endpoint_config()
                }
            )

        if settings.KIOSC_NETWORK_MODE == 'host':
            options_host_config['port_bindings'] = {
                self.container.container_port: self.container.host_port
            }

        environment = (
            dict(self.container.environment)
            if self.container.environment
            else {}
        )
        url_prefix = reverse(
            'containers:proxy',
            kwargs={
                'container': self.container.sodar_uuid,
                'path': self.container.get_path(),
            },
        )

        for key, value in environment.items():
            if isinstance(value, str) and '__KIOSC_URL_PREFIX__' in value:
                environment[key] = value.replace(
                    '__KIOSC_URL_PREFIX__', url_prefix
                )

        environment.update(
            {
                'CONTAINER_PORT': self.container.container_port,
                'TITLE': self.container.title,
                'DESCRIPTION': self.container.description or '',
            }
        )

        # Volume
        if volume_name := str(self.container.volume_name):
            kiosc_volume_mountpoint = '/kiosc'
            self.cli.create_volume(volume_name)
            options_host_config['binds'] = {
                volume_name: {
                    'bind': kiosc_volume_mountpoint,
                    'mode': 'rw',
                },
            }
            options['volumes'] = [kiosc_volume_mountpoint]

        self._log_task('Initializing the container...')

        # Create container
        container_info = self.cli.create_container(
            detach=True,
            image=image_details['RepoTags'][0],
            environment=environment,
            command=(
                shlex.split(self.container.command)
                if self.container.command
                else None
            ),
            ports=[self.container.container_port],
            host_config=self.cli.create_host_config(
                ulimits=[
                    Ulimit(
                        name='nofile',
                        soft=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                        hard=settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                    )
                ],
                **options_host_config,
            ),
            **options,
        )
        self.container.container_id = container_info.get('Id')
        self.container.save()

        self._log_task('Container initialized successfully.')
        self._update_status(container_info)

    def on_pull_deleted(self):
        self.on_pull()

    def on_pull_failed(self):
        self.on_pull()

    def on_start_pulled(self):
        # Starting container
        self._log_task('Starting...')
        self.cli.start(self.container.container_id)
        self._update_status()
        self._log_task('Container started successfully')

    def on_start_created(self):
        self.on_start_pulled()

    def on_start_exited(self):
        self.on_start_pulled()

    def on_start_terminated(self):
        self.on_start_pulled()

    def on_pause(self):
        self._log_task('Pausing container')
        self.cli.pause(self.container.container_id)
        self._update_status()
        self._log_task('Pausing container succeeded')

    def on_unpause(self):
        self._log_task('Unpausing container')
        self.cli.unpause(self.container.container_id)
        self._update_status()
        self._log_task('Unpausing container succeeded')

    def on_stop_running(self):
        self._log_task('Stopping container')

        # Stopping container and updating status
        self.cli.stop(self.container.container_id)
        self._update_status()

        self._log_task('Stopping container succeeded')

    def on_stop_paused(self):
        self.on_stop_running()

    def on_terminate_running(self):
        self._log_task('Terminating container due to inactivity...')

        # Timing out container and updating status
        self.cli.stop(self.container.container_id)
        self.container.state = STATE_TERMINATED
        self.container.save()

        self._log_task('Container terminated due to inactivity.')

    def on_terminate_paused(self):
        self.on_terminate_running()

    def on_delete_exited(self):
        self.job.add_log_entry('Deleting container')
        self.container.state = STATE_DELETING
        self.container.save()
        self.container.log_entries.all().delete()

        if not self.container.container_id:
            # Nothing to do, the container probably doesn't even exist
            logger.warning('Trying to delete container with no id')
            return

        # Removing container and erasing container_id
        # NOTE: this will also remove the volumes associated with the container
        # (thanks to the v=True flag in remove_container())
        try:
            self.cli.remove_container(
                self.container.container_id, force=True, v=True
            )
        except docker.errors.NotFound:
            # The container doesn't exist, so there is nothing to delete
            logger.warning("Trying to delete container which doesn't exist")
            pass

    def on_delete_terminated(self):
        self.on_delete_exited()

    def on_delete_failed(self):
        self.on_delete_exited()

    def on_delete_created(self):
        self.on_delete_exited()

    def on_delete_dead(self):
        self.on_delete_exited()

    def on_delete_pulling(self):
        self.on_delete_exited()

    def on_delete_success(self):
        self.container.state = STATE_DELETED
        self.container.container_id = None
        self.container.save()
        self._log_task('Previous container was deleted.')
