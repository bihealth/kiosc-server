"""Test container tasks."""
import time
from unittest.mock import patch, call

import docker.errors
from django.conf import settings
from django.test import tag, override_settings

from containers.models import (
    ACTION_STOP,
    STATE_EXITED,
    STATE_RUNNING,
    Container,
    STATE_INITIAL,
    ACTION_RESTART,
    ACTION_PAUSE,
    STATE_PAUSED,
    ACTION_UNPAUSE,
    ACTION_DELETE,
    STATE_DELETED,
)
from containers.statemachines import connect_docker
from containers.tasks import container_task
from containers.tests.factories import ContainerBackgroundJobFactory
from containers.tests.helpers import (
    TestBase,
    DockerMock,
)


class TestContainerTask(TestBase):
    """Tests for ``container_task``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.container1.container_id = None
        self.container1.save()
        self.bg_job = ContainerBackgroundJobFactory(
            project=self.project, user=self.superuser, container=self.container1
        )
        self.cli = connect_docker()

    @tag("docker-server")
    def tearDown(self):
        for container in Container.objects.all():
            if container.container_id and not len(container.container_id) < 3:
                try:
                    self.cli.stop(container.container_id)
                except docker.errors.NotFound:
                    pass

        time.sleep(1)
        self.cli.prune_containers()
        self.cli.prune_images()

    @override_settings(KIOSC_NETWORK_MODE="host")
    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_start_mocked_mode_host(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Assert mocks
        create_container.assert_called_once_with(
            detach=True,
            image=self.container1.image_id,
            environment=self.container1.environment,
            command=self.container1.command or None,
            ports=[self.container1.container_port],
            host_config=None,
        )
        create_host_config.assert_called_once_with(
            ulimits=[
                {
                    "Name": "nofile",
                    "Soft": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                    "Hard": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                }
            ],
            port_bindings={
                self.container1.container_port: self.container1.host_port
            },
        )
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_called_once_with(self.container1.get_repos_full())
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(self.container1.container_id)
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_start_mocked_mode_docker_shared(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        create_networking_config.side_effect = [
            DockerMock.create_networking_config
        ]
        create_endpoint_config.side_effect = [DockerMock.create_endpoint_config]
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Assert mocks
        create_container.assert_called_once_with(
            detach=True,
            image=self.container1.image_id,
            environment=self.container1.environment,
            command=self.container1.command or None,
            ports=[self.container1.container_port],
            host_config=None,
            networking_config={},
        )
        create_host_config.assert_called_once_with(
            ulimits=[
                {
                    "Name": "nofile",
                    "Soft": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                    "Hard": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                }
            ],
        )
        create_networking_config.assert_called_once_with(
            {settings.KIOSC_DOCKER_NETWORK: {}}
        )
        create_endpoint_config.assert_called_once_with()
        inspect_image.assert_called_once_with(self.container1.get_repos_full())
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(self.container1.container_id)
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=10)
    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_start_stop_second_blocked_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        bg_job2 = ContainerBackgroundJobFactory(
            project=self.project,
            user=self.superuser,
            container=self.container1,
            action="stop",
        )

        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        create_networking_config.side_effect = [
            DockerMock.create_networking_config
        ]
        create_endpoint_config.side_effect = [DockerMock.create_endpoint_config]
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)
        container_task(job_id=bg_job2.pk)

        self.container1.refresh_from_db()

        self.assertEqual(
            self.container1.log_entries.last().text,
            f"Action not performed: {bg_job2.action}. Cool-down is active ({settings.KIOSC_DOCKER_ACTION_MIN_DELAY}s)",
        )

        # Assert mocks
        create_container.assert_called_once_with(
            detach=True,
            image=self.container1.image_id,
            environment=self.container1.environment,
            command=self.container1.command or None,
            ports=[self.container1.container_port],
            host_config=None,
        )
        create_host_config.assert_called_once_with(
            ulimits=[
                {
                    "Name": "nofile",
                    "Soft": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                    "Hard": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                }
            ],
            port_bindings={
                self.container1.container_port: self.container1.host_port
            },
        )
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_called_once_with(self.container1.get_repos_full())
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(self.container1.container_id)
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_start_stop_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        bg_job2 = ContainerBackgroundJobFactory(
            project=self.project,
            user=self.superuser,
            container=self.container1,
            action="stop",
        )

        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        create_networking_config.side_effect = [
            DockerMock.create_networking_config
        ]
        create_endpoint_config.side_effect = [DockerMock.create_endpoint_config]
        inspect_container.side_effect = [
            DockerMock.inspect_container_started,
            DockerMock.inspect_container_stopped,
        ]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)
        container_task(job_id=bg_job2.pk)

        self.container1.refresh_from_db()

        self.assertEqual(
            self.container1.log_entries.last().text, "Stopping succeeded"
        )

        create_container.assert_called_once_with(
            detach=True,
            image=self.container1.image_id,
            environment=self.container1.environment,
            command=self.container1.command or None,
            ports=[self.container1.container_port],
            host_config=None,
        )
        create_host_config.assert_called_once_with(
            ulimits=[
                {
                    "Name": "nofile",
                    "Soft": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                    "Hard": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                }
            ],
            port_bindings={
                self.container1.container_port: self.container1.host_port
            },
        )
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_called_once_with(self.container1.get_repos_full())
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)] * 2
        )
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(self.container1.container_id)
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_stop_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [DockerMock.inspect_container_stopped]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_EXITED)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_restart_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        self.bg_job.action = ACTION_RESTART
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [
            DockerMock.inspect_container_stopped,
            DockerMock.inspect_container_started,
        ]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Assert mocks
        create_container.assert_called_once_with(
            detach=True,
            image=self.container1.image_id,
            environment=self.container1.environment,
            command=self.container1.command or None,
            ports=[self.container1.container_port],
            host_config=None,
        )
        create_host_config.assert_called_once_with(
            ulimits=[
                {
                    "Name": "nofile",
                    "Soft": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT,
                    "Hard": settings.KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD,
                }
            ],
            port_bindings={
                self.container1.container_port: self.container1.host_port
            },
        )
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_called_once_with(self.container1.get_repos_full())
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)] * 2
        )
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(self.container1.container_id)
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_called_once_with(self.container1.container_id)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_pause_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        self.bg_job.action = ACTION_PAUSE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [DockerMock.inspect_container_paused]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_PAUSED)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_called_once_with(self.container1.container_id)
        unpause.assert_not_called()
        remove_container.assert_not_called()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_unpause_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        self.bg_job.action = ACTION_UNPAUSE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.state = STATE_PAUSED
        self.container1.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_called_once_with(self.container1.container_id)
        remove_container.assert_not_called()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_delete_initial_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        container_id = DockerMock.create_container.get("Id")
        self.bg_job.action = ACTION_DELETE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = container_id
        self.container1.state = STATE_INITIAL
        self.container1.save()

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_INITIAL)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_not_called()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.not_called()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_delete_running_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        container_id = DockerMock.create_container.get("Id")
        self.bg_job.action = ACTION_DELETE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = container_id
        self.container1.state = STATE_RUNNING
        self.container1.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [DockerMock.inspect_container_stopped]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_DELETED)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_called_once_with(container_id)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_networking_config")
    @patch("docker.api.client.APIClient.create_endpoint_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_delete_exited_mocked(
        self,
        create_container,
        create_endpoint_config,
        create_networking_config,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
    ):
        # Prepare
        container_id = DockerMock.create_container.get("Id")
        self.bg_job.action = ACTION_DELETE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.container_id = container_id
        self.container1.state = STATE_EXITED
        self.container1.save()

        # Run
        container_task(job_id=self.bg_job.pk)

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_DELETED)

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        create_networking_config.assert_not_called()
        create_endpoint_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_not_called()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_called_once_with(container_id)

    @tag("docker-server")
    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
    def test_start_stop(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.save()

        # Start
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Stop
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_EXITED,
        )
        self.assertEqual(self.container1.state, STATE_EXITED)

    @tag("docker-server")
    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
    def test_start_pause_unpause(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.save()

        # Start
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Pause
        self.bg_job.action = ACTION_PAUSE
        self.bg_job.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_PAUSED,
        )
        self.assertEqual(self.container1.state, STATE_PAUSED)

        # Unpause
        self.bg_job.action = ACTION_UNPAUSE
        self.bg_job.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @tag("docker-server")
    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
    def test_start_restart(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.save()

        # Start
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)

        # Restart
        self.bg_job.action = ACTION_RESTART
        self.bg_job.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @tag("docker-server")
    @override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
    def test_start_delete(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.save()

        # Start
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)
        container_id = self.container1.container_id

        # Delete
        self.bg_job.action = ACTION_DELETE
        self.bg_job.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertIsNone(self.container1.container_id)
        self.assertEqual(self.container1.state, STATE_DELETED)

        with self.assertRaises(docker.errors.NotFound):
            self.cli.inspect_container(container_id)
