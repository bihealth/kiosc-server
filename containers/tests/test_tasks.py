"""Test container tasks."""
from unittest.mock import patch

import docker.errors
from django.test import tag

from containers.models import (
    ACTION_STOP,
    STATE_EXITED,
    STATE_RUNNING,
    Container,
)
from containers.tasks import container_task, connect_docker
from containers.tests.factories import ContainerBackgroundJobFactory
from containers.tests.helpers import TestBase, DockerMock


class TestContainerTask(TestBase):
    """Tests for container tasks."""

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
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_start_container_task_mocked(self, pull, start, stop):
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_called_once_with(
            repository=self.container1.repository,
            tag=self.container1.tag,
            stream=True,
            decode=True,
        )
        start.assert_called_once_with(container=self.container1.container_id)
        start.assert_called_once_with(container=self.container1.container_id)
        stop.assert_not_called()
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
    @patch("docker.api.client.APIClient.stop")
    @patch("docker.api.client.APIClient.start")
    @patch("docker.api.client.APIClient.pull")
    def test_stop_container_task_mocked(self, pull, start, stop):
        self.bg_job.action = ACTION_STOP
        self.bg_job.save()
        self.container1.image_id = "1"
        self.container1.container_id = "1"
        self.container1.state = STATE_RUNNING
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        pull.assert_not_called()
        start.assert_not_called()
        stop.assert_called_once_with(container=self.container1.container_id)
        self.assertEqual(self.container1.state, STATE_EXITED)

    @tag("docker-server")
    def test_start_stop_container_task(self):
        self.container1.repository = "brndnmtthws/nginx-echo-headers"
        self.container1.tag = "latest"
        self.container1.host_port = "8888"
        self.container1.save()
        container_task(job_id=self.bg_job.pk)
        self.container1.refresh_from_db()
        self.assertEqual(
            self.cli.inspect_container(self.container1.container_id)
            .get("State")
            .get("Status"),
            STATE_RUNNING,
        )
        self.assertEqual(self.container1.state, STATE_RUNNING)
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
