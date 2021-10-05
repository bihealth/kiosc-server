"""Test kioscadmin tasks."""

from datetime import timedelta
from unittest import mock
from unittest.mock import patch, call

import docker.errors
from django.conf import settings
from django.utils import timezone

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
    poll_docker_status_and_logs,
    sync_container_state_with_last_user_action,
    DEFAULT_GRACE_PERIOD_CONTAINER_STATUS,
    stop_inactive_containers,
)
from containers.tests.factories import (
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


class TestPollDockerStatusAndLogsTask(TestBase):
    """Tests for ``poll_docker_status_and_logs`` task."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.create_one_container()
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.save()
        self.bg_job = ContainerBackgroundJobFactory(
            project=self.project, user=self.superuser, container=self.container1
        )

    @patch("docker.api.client.APIClient.logs")
    @patch("docker.api.client.APIClient.inspect_container")
    def test_all_new_entries(self, inspect_container, _logs):
        self.assertEqual(self.container1.state, STATE_INITIAL)

        # Prepare
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        _logs.side_effect = [DockerMock.logs]

        # Run
        poll_docker_status_and_logs()

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)
        self.assertEqual(
            ContainerLogEntry.objects.filter(container=self.container1).count(),
            3,
        )
        logs = [
            entry.text
            for entry in ContainerLogEntry.objects.filter(
                container=self.container1
            )
        ]
        self.assertEqual(
            logs,
            [
                log_entry1()[1][31:],
                log_entry2()[1][31:],
                log_entry3()[1][31:],
            ],
        )

        # Assert mocks
        inspect_container.assert_called_once_with(self.container1.container_id)
        _logs.assert_called_once_with(
            self.container1.container_id, timestamps=True
        )

    @patch("docker.api.client.APIClient.logs")
    @patch("docker.api.client.APIClient.inspect_container")
    def test_all_new_entries_no_date(self, inspect_container, _logs):
        self.assertEqual(self.container1.state, STATE_INITIAL)

        # Prepare
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        _logs.side_effect = [DockerMock.logs_no_date]

        # Run
        poll_docker_status_and_logs()

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)
        self.assertEqual(
            ContainerLogEntry.objects.filter(container=self.container1).count(),
            1,
        )
        logs = [
            entry.text
            for entry in ContainerLogEntry.objects.filter(
                container=self.container1
            )
        ]
        self.assertEqual(
            logs,
            [
                "Docker log has no timestamp! ({})".format(
                    log_entry1_no_date()
                ),
            ],
        )

        # Assert mocks
        inspect_container.assert_called_once_with(self.container1.container_id)
        _logs.assert_called_once_with(
            self.container1.container_id, timestamps=True
        )

    @patch("docker.api.client.APIClient.logs")
    @patch("docker.api.client.APIClient.inspect_container")
    def test_add_entries_since_date(self, inspect_container, _logs):
        self.assertEqual(self.container1.state, STATE_INITIAL)

        # Prepare
        dt1, entry1 = log_entry1()
        dt2, entry2 = log_entry2()
        ContainerLogEntryFactory(
            text=entry1[31:],
            container=self.container1,
            process=PROCESS_DOCKER,
            date_docker_log=dt1,
            user=None,
        )
        last_log = ContainerLogEntryFactory(
            text=entry2[31:],
            container=self.container1,
            process=PROCESS_DOCKER,
            date_docker_log=dt2,
            user=None,
        )
        inspect_container.side_effect = [DockerMock.inspect_container_started]
        _logs.side_effect = [DockerMock.logs_since]

        # Run
        poll_docker_status_and_logs()

        # Assert objects
        self.container1.refresh_from_db()
        self.assertEqual(self.container1.state, STATE_RUNNING)
        self.assertEqual(
            ContainerLogEntry.objects.filter(container=self.container1).count(),
            3,
        )
        logs = [
            entry.text
            for entry in ContainerLogEntry.objects.filter(
                container=self.container1
            )
        ]
        self.assertEqual(
            logs,
            [
                log_entry1()[1][31:],
                log_entry2()[1][31:],
                log_entry3()[1][31:],
            ],
        )

        # Assert mocks
        inspect_container.assert_called_once_with(self.container1.container_id)
        _logs.assert_called_once_with(
            self.container1.container_id,
            timestamps=True,
            since=last_log.date_docker_log.replace(tzinfo=None),
        )


class TestSyncContainerStateWithLastUserActionTask(TestBase):
    """Tests for ``sync_container_state_with_last_user_action`` task."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.create_one_container()
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.save()
        self.bg_job = ContainerBackgroundJobFactory(
            project=self.project, user=self.superuser, container=self.container1
        )

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_no_last_status_update(
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
    ):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_no_job(
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
    ):
        # Prepare
        self.bg_job.delete()
        self.container1.date_last_status_update = timezone.now()
        self.container1.save()
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        sync_container_state_with_last_user_action()

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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.save()
        inspect_container.side_effect = [DockerMock.inspect_container_no_info]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_state_as_expected_start(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_START
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_as_expected_restart(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_RESTART
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_restarted]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_as_expected_stop(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_EXITED
        self.container1.save()
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_stopped]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_state_as_expected_pause(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_PAUSED
        self.container1.save()
        self.bg_job.action = ACTION_PAUSE
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_paused]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_state_as_expected_unpause(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_UNPAUSE
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_unpaused]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_timeout_not_yet_passed(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 0)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_max_retries_hit(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now() - timedelta(
            seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS + 20
        )
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_STOP
        self.bg_job.retries = self.container1.max_retries
        self.bg_job.save()
        inspect_container.side_effect = [DockerMock.inspect_container_started]

        # Run
        sync_container_state_with_last_user_action()

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
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, self.container1.max_retries)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_stopping(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now() - timedelta(
            seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS + 20
        )
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        inspect_container.side_effect = [
            DockerMock.inspect_container_started,
            DockerMock.inspect_container_stopped,
        ]

        # Run
        sync_container_state_with_last_user_action()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)] * 2
        )
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.container1.refresh_from_db()
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 1)
        self.assertEqual(self.container1.state, STATE_EXITED)

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
    def test_starting(
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
        self.container1.date_last_status_update = timezone.now() - timedelta(
            seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS + 20
        )
        self.container1.state = STATE_EXITED
        self.container1.save()
        self.bg_job.action = ACTION_START
        self.bg_job.save()
        create_container.side_effect = [DockerMock.create_container]
        create_host_config.side_effect = [DockerMock.create_host_config]
        inspect_container.side_effect = [
            DockerMock.inspect_container_stopped,
            DockerMock.inspect_container_started,
        ]
        inspect_image.side_effect = [DockerMock.inspect_image]

        # Run
        sync_container_state_with_last_user_action()

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
        create_endpoint_config.assert_not_called(),
        create_networking_config.assert_not_called(),
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
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_called_once_with(self.container1.container_id)

        # Assert objects
        self.container1.refresh_from_db()
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 1)
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_pausing(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now() - timedelta(
            seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS + 20
        )
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.bg_job.action = ACTION_PAUSE
        self.bg_job.save()
        inspect_container.side_effect = [
            DockerMock.inspect_container_started,
            DockerMock.inspect_container_paused,
        ]

        # Run
        sync_container_state_with_last_user_action()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)] * 2
        )
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_called_once_with(self.container1.container_id)
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.container1.refresh_from_db()
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 1)
        self.assertEqual(self.container1.state, STATE_PAUSED)

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
    def test_unpausing(
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
    ):
        # Prepare
        self.container1.date_last_status_update = timezone.now() - timedelta(
            seconds=DEFAULT_GRACE_PERIOD_CONTAINER_STATUS + 20
        )
        self.container1.state = STATE_PAUSED
        self.container1.save()
        self.bg_job.action = ACTION_UNPAUSE
        self.bg_job.save()
        inspect_container.side_effect = [
            DockerMock.inspect_container_paused,
            DockerMock.inspect_container_unpaused,
        ]

        # Run
        sync_container_state_with_last_user_action()

        # Assert mocks
        create_container.assert_not_called()
        create_host_config.assert_not_called()
        inspect_image.assert_not_called()
        inspect_container.assert_has_calls(
            [call(self.container1.container_id)] * 2
        )
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        pause.assert_not_called()
        unpause.assert_called_once_with(self.container1.container_id)
        remove_container.assert_not_called()

        # Assert objects
        self.container1.refresh_from_db()
        self.bg_job.refresh_from_db()
        self.assertEqual(self.bg_job.retries, 1)
        self.assertEqual(self.container1.state, STATE_RUNNING)


class TestStopInactiveContainers(TestBase):
    """Tests for ``stop_inactive_containers`` task."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.create_one_container()
        self.container1.container_id = DockerMock.create_container.get("Id")
        self.container1.image_id = DockerMock.inspect_image.get("Id")
        self.container1.save()

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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
    ):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        inspect_container.side_effect = docker.errors.NotFound("x")

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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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
    ):
        # Prepare
        self.container1.log_entries.create(
            text="Accessing", process=PROCESS_PROXY, user=self.superuser
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

    @patch("docker.api.client.APIClient.remove_container")
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    @patch("docker.api.client.APIClient.inspect_container")
    @patch("docker.api.client.APIClient.inspect_image")
    @patch("docker.api.client.APIClient.create_host_config")
    @patch("docker.api.client.APIClient.create_container")
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
    ):
        # Prepare
        mock_now = timezone.now() - timedelta(days=2)

        with mock.patch(
            "django.utils.timezone.now", mock.Mock(return_value=mock_now)
        ):
            self.container1.log_entries.create(
                text="Accessing",
                process=PROCESS_PROXY,
                user=self.superuser,
            )

        self.container1.state = STATE_RUNNING
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
            [call(self.container1.container_id)] * 2
        )
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        remove_container.assert_not_called()

        # Assert objects
        self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
