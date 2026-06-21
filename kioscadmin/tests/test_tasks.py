"""Test kioscadmin tasks."""

from datetime import timedelta
from unittest import mock
from unittest.mock import patch, call

import docker.errors
from django.conf import settings
from django.utils import timezone
from django.test import override_settings

from containers.models import (
    ACTION_STOP,
    STATE_EXITED,
    STATE_RUNNING,
    ContainerLogEntry,
    STATE_INITIAL,
    PROCESS_DOCKER,
    ACTION_RESTART,
    ACTION_PAUSE,
    STATE_PAUSED,
    ACTION_UNPAUSE,
    ACTION_START,
    PROCESS_PROXY,
    ContainerBackgroundJob,
)
from kioscadmin.tasks import (
    connect_docker,
    DEFAULT_GRACE_PERIOD_CONTAINER_STATUS,
    stop_inactive_containers,
    prune_zombie_containers,
)
from containers.tasks import container_task

from containers.tests.test_lifecycle import build_testdata_container
from containers.tests.factories import (
    ContainerFactory,
    ContainerBackgroundJobFactory,
    ContainerLogEntryFactory,
)
from containers.tests.helpers import (
    TestBase,
    DockerMock,
    log_entry1,
    log_entry2,
    log_entry3,
    log_entry1_no_date,
)


class TestStopInactiveContainers(TestBase):
    """Tests for ``stop_inactive_containers`` task."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.create_one_container()
        self.container1.container_id = DockerMock.create_container.get('Id')
        self.container1.image_id = DockerMock.inspect_image.get('Id')
        self.container1.save()

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_no_container_id(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        inspect_container.side_effect = docker.errors.NotFound('x')

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_no_state(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        inspect_container.side_effect = [DockerMock.inspect_container_no_info]

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_state_exited(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        self.container1.state = STATE_EXITED
        self.container1.save()

        inspect_container.side_effect = [DockerMock.inspect_container_stopped]

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_no_last_access(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        # Prepare
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_last_access_below_threshold(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        # Prepare
        self.container1.log_entries.create(
            text='Accessing', process=PROCESS_PROXY, user=self.superuser
        )
        self.container1.inactivity_threshold = 1
        self.container1.save()
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_called_once_with(self.container1.container_id)
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch('containers.tasks.sync_container_state')
    @patch('docker.api.client.APIClient.remove_container')
    @patch('docker.api.client.APIClient.unpause')
    @patch('docker.api.client.APIClient.pause')
    @patch('docker.api.client.APIClient.stop')
    @patch('docker.api.client.APIClient.start')
    @patch('docker.api.client.APIClient.pull')
    @patch('docker.api.client.APIClient.inspect_container')
    @patch('docker.api.client.APIClient.inspect_image')
    @patch('docker.api.client.APIClient.create_host_config')
    @patch('docker.api.client.APIClient.create_container')
    def test_last_access_above_threshold(
        self,
        create_container,
        create_host_config,
        inspect_image,
        inspect_container,
        pull,
        start,
        stop,
        pause,
        unpause,
        remove_container,
        sync_container_state,
    ):
        # Prepare
        mock_now = timezone.now() - timedelta(days=2)

        with mock.patch(
            'django.utils.timezone.now', mock.Mock(return_value=mock_now)
        ):
            self.container1.log_entries.create(
                text='Accessing',
                process=PROCESS_PROXY,
                user=self.superuser,
            )

        self.container1.state = STATE_RUNNING
        self.container1.date_last_access = timezone.now() - timedelta(days=2)
        self.container1.inactivity_threshold = 1
        self.container1.save()

        inspect_container.side_effect = [
            DockerMock.inspect_container_started,
            DockerMock.inspect_container_stopped,
        ]

        # Run
        stop_inactive_containers()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)]
        )
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 1)


@override_settings(
    KIOSC_NETWORK_MODE='docker-shared',
    KIOSC_DOCKER_NETWORK='kiosc-docker-network-testing',
)
class TestPruneZombieContainers(TestBase):
    """Tests for ``prune_zombie_containers`` task."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        # Build the sample container image
        build_testdata_container(self.cli, 'sample-app-logging')
        # Create the network
        self.cli.create_network(
            settings.KIOSC_DOCKER_NETWORK, driver='bridge', check_duplicate=True
        )

        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-logging',
            tag='testing',
            host_port=0,
        )

    def tearDown(self):
        network = self.cli.networks(settings.KIOSC_DOCKER_NETWORK)[0]
        self.cli.remove_network(network['Id'])

    def test_prune_zombie_containers(self):
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn('Starting succeeded', logs)
        self.assertEqual(self.container.state, STATE_RUNNING)
        image_id = self.container.image_id
        # Artificially cut the tie between kiosc and the container
        self.container.container_id = None
        self.container.save()
        # Test that pruning the zombies does the job
        prune_zombie_containers()
        for container in self.cli.containers():
            if container['ImageID'] == image_id:
                # Container should not be found
                raise RuntimeError('Container did not stop successfully')
