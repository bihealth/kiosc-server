"""Test container tasks."""
import time
from unittest.mock import patch

import docker.errors
from django.test import tag

from containers.models import (
    ACTION_STOP,
    STATE_EXITED,
    STATE_RUNNING,
    Container,
    ContainerLogEntry,
    STATE_INITIAL,
    PROCESS_DOCKER,
    ACTION_RESTART,
    ACTION_PAUSE,
    STATE_PAUSED,
    ACTION_UNPAUSE,
)
from containers.tasks import (
    container_task,
    connect_docker,
    poll_docker_status_and_logs,
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
)


class TestContainerTask(TestBase):
    """Tests for ``container_task``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.bg_job = ContainerBackgroundJobFactory(
            project=self.project, user=self.superuser, container=self.container1
        )
        self.cli = connect_docker()

    @tag("docker-server")
    def tearDown(self):
        for container in Container.objects.all():
            if container.image_id and container.container_id:
                try:
                    self.cli.stop(container=container.container_id)
                except docker.errors.NotFound:
                    pass

        time.sleep(1)
        self.cli.prune_containers()
        self.cli.prune_images()

    @patch(
        "docker.api.client.APIClient.inspect_image", DockerMock.inspect_image
    )
    @patch(
        "docker.api.client.APIClient.create_container",
        DockerMock.create_container,
    )
    @patch(
        "docker.api.client.APIClient.create_host_config",
        DockerMock.create_host_config,
    )
    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_started,
    )
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.restart")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_start_container_task_mocked(
        self, pull, start, stop, restart, pause, unpause
    ):
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(container=self.container1.container_id)
        stop.assert_not_called()
        restart.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @patch(
        "docker.api.client.APIClient.inspect_image", DockerMock.inspect_image
    )
    @patch(
        "docker.api.client.APIClient.create_container",
        DockerMock.create_container,
    )
    @patch(
        "docker.api.client.APIClient.create_host_config",
        DockerMock.create_host_config,
    )
    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_stopped,
    )
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.restart")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_stop_container_task_mocked(
        self, pull, start, stop, restart, pause, unpause
    ):
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image(None).get("Id")
        self.container1.container_id = DockerMock.create_container(
            None, None, None, None, None, None
        ).get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(container=self.container1.container_id)
        restart.assert_not_called()
        pause.assert_not_called()
        unpause.assert_not_called()
        self.assertEqual(self.container1.state, STATE_EXITED)

    @patch(
        "docker.api.client.APIClient.inspect_image", DockerMock.inspect_image
    )
    @patch(
        "docker.api.client.APIClient.create_container",
        DockerMock.create_container,
    )
    @patch(
        "docker.api.client.APIClient.create_host_config",
        DockerMock.create_host_config,
    )
    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_restarted,
    )
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.restart")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_restart_container_task_mocked(
        self, pull, start, stop, restart, pause, unpause
    ):
        self.bg_job.action = ACTION_RESTART
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image(None).get("Id")
        self.container1.container_id = DockerMock.create_container(
            None, None, None, None, None, None
        ).get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        restart.assert_called_once_with(container=self.container1.container_id)
        pause.assert_not_called()
        unpause.assert_not_called()
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @patch(
        "docker.api.client.APIClient.inspect_image", DockerMock.inspect_image
    )
    @patch(
        "docker.api.client.APIClient.create_container",
        DockerMock.create_container,
    )
    @patch(
        "docker.api.client.APIClient.create_host_config",
        DockerMock.create_host_config,
    )
    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_paused,
    )
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.restart")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_pause_container_task_mocked(
        self, pull, start, stop, restart, pause, unpause
    ):
        self.bg_job.action = ACTION_PAUSE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image(None).get("Id")
        self.container1.container_id = DockerMock.create_container(
            None, None, None, None, None, None
        ).get("Id")
        self.container1.state = STATE_RUNNING
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        restart.assert_not_called()
        pause.assert_called_once_with(container=self.container1.container_id)
        unpause.assert_not_called()
        self.assertEqual(self.container1.state, STATE_PAUSED)

    @patch(
        "docker.api.client.APIClient.inspect_image", DockerMock.inspect_image
    )
    @patch(
        "docker.api.client.APIClient.create_container",
        DockerMock.create_container,
    )
    @patch(
        "docker.api.client.APIClient.create_host_config",
        DockerMock.create_host_config,
    )
    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_unpaused,
    )
    @patch("docker.api.client.APIClient.unpause")
    @patch("docker.api.client.APIClient.pause")
    @patch("docker.api.client.APIClient.restart")
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_unpause_container_task_mocked(
        self, pull, start, stop, restart, pause, unpause
    ):
        self.bg_job.action = ACTION_UNPAUSE
        self.bg_job.save()
        self.container1.image_id = DockerMock.inspect_image(None).get("Id")
        self.container1.container_id = DockerMock.create_container(
            None, None, None, None, None, None
        ).get("Id")
        self.container1.state = STATE_PAUSED
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_not_called()
        restart.assert_not_called()
        pause.assert_not_called()
        unpause.assert_called_once_with(container=self.container1.container_id)
        self.assertEqual(self.container1.state, STATE_RUNNING)

    @tag("docker-server")
    def test_start_stop_container_task(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.host_port = "8888"
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
    def test_start_pause_unpause_container_task(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.host_port = "8888"
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
    def test_start_restart_container_task(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.host_port = "8888"
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


class TestPollDockerStatusAndLogsTask(TestBase):
    """Tests for ``poll_docker_status_and_logs_task``."""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.create_one_container()
        self.container1.container_id = DockerMock.create_container(
            None, None, None, None, None, None
        ).get("Id")
        self.container1.image_id = DockerMock.inspect_image(None).get("Id")
        self.container1.save()
        self.bg_job = ContainerBackgroundJobFactory(
            project=self.project, user=self.superuser, container=self.container1
        )

    @tag("docker-server")
    def tearDown(self):
        for container in Container.objects.all():
            if container.image_id and container.container_id:
                try:
                    self.cli.stop(container=container.container_id)
                except docker.errors.NotFound:
                    pass
        self.cli.prune_containers()
        self.cli.prune_images()

    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_started,
    )
    @patch(
        "docker.api.client.APIClient.logs",
        DockerMock.logs,
    )
    def test_poll_docker_status_and_logs_tasks(self):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        poll_docker_status_and_logs()
        self.container1.refresh_from_db()
        # Check updated status
        self.assertEqual(self.container1.state, STATE_RUNNING)
        # Check logs
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
                log_entry1()[1][51:],
                log_entry2()[1][51:],
                log_entry3()[1][51:],
            ],
        )

    @patch(
        "docker.api.client.APIClient.inspect_container",
        DockerMock.inspect_container_started,
    )
    @patch(
        "docker.api.client.APIClient.logs",
        DockerMock.logs_since,
    )
    def test_poll_docker_status_and_logs_tasks_since(self):
        self.assertEqual(self.container1.state, STATE_INITIAL)
        dt1, entry1 = log_entry1()
        dt2, entry2 = log_entry2()
        ContainerLogEntryFactory(
            text=entry1[51:],
            container=self.container1,
            process=PROCESS_DOCKER,
            date_docker_log=dt1,
            user=None,
        )
        ContainerLogEntryFactory(
            text=entry2[51:],
            container=self.container1,
            process=PROCESS_DOCKER,
            date_docker_log=dt2,
            user=None,
        )
        poll_docker_status_and_logs()
        self.container1.refresh_from_db()
        # Check updated status
        self.assertEqual(self.container1.state, STATE_RUNNING)
        # Check logs
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
                log_entry1()[1][51:],
                log_entry2()[1][51:],
                log_entry3()[1][51:],
            ],
        )
