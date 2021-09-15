"""Tests for the container API views."""
from unittest.mock import patch

from rest_framework import status
from urllib3_mock import Responses

from django.forms import model_to_dict
from django.urls import reverse
from django.test import override_settings

from containers.models import (
    Container,
    ContainerBackgroundJob,
    ACTION_START,
    ACTION_STOP,
    STATE_RUNNING,
    STATE_DELETED,
)
from containers.tests.helpers import TestContainerCreationMixin
from containers.views import CELERY_SUBMIT_COUNTDOWN
from projectroles.models import Project
from projectroles.tests.test_views_api import TestAPIViewsBase

responses = Responses("requests.packages.urllib3")


class TestContainerListAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerListAPIView``."""

    def test_get_success_list_empty(self):
        response = self.request_knox(
            reverse(
                "containers:api-list",
                kwargs={"project": self.project.sodar_uuid},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_get_success_list_one_item(self):
        self.create_one_container()

        response = self.request_knox(
            reverse(
                "containers:api-list",
                kwargs={"project": self.project.sodar_uuid},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = model_to_dict(self.container1, exclude=["id"])
        expected["date_created"] = self.get_drf_datetime(
            self.container1.date_created
        )
        expected["date_modified"] = self.get_drf_datetime(
            self.container1.date_modified
        )
        expected["project"] = str(
            Project.objects.get(id=expected["project"]).sodar_uuid
        )
        expected["sodar_uuid"] = str(expected["sodar_uuid"])
        self.assertEqual(response.json(), [expected])

    def test_get_success_list_two_items(self):
        self.create_two_containers()

        response = self.request_knox(
            reverse(
                "containers:api-list",
                kwargs={"project": self.project.sodar_uuid},
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        container1 = model_to_dict(self.container1, exclude=["id"])
        container1["date_created"] = self.get_drf_datetime(
            self.container1.date_created
        )
        container1["date_modified"] = self.get_drf_datetime(
            self.container1.date_modified
        )
        container1["project"] = str(
            Project.objects.get(id=container1["project"]).sodar_uuid
        )
        container1["sodar_uuid"] = str(container1["sodar_uuid"])
        container2 = model_to_dict(self.container2, exclude=["id"])
        container2["date_created"] = self.get_drf_datetime(
            self.container2.date_created
        )
        container2["date_modified"] = self.get_drf_datetime(
            self.container2.date_modified
        )
        container2["project"] = str(
            Project.objects.get(id=container2["project"]).sodar_uuid
        )
        container2["sodar_uuid"] = str(container2["sodar_uuid"])
        self.assertEqual(response.json(), [container2, container1])


class TestContainerCreateAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerCreateAPIView``."""

    def setUp(self):
        super().setUp()
        self.create_containertemplates()
        self.post_data_min_shared = {
            "title": "Title",
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "project": self.project.pk,
            "max_retries": 10,
            "inactivity_threshold": 20,
        }
        self.post_data_min_host = {
            **self.post_data_min_shared,
            "host_port": 8000,
        }
        self.post_data_all = {
            **self.post_data_min_host,
            "description": "some description",
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
            "containertemplatesite": self.containertemplatesite1.pk,
        }

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_post_success_min_fields_mode_host(self):
        response = self.request_knox(
            reverse(
                "containers:api-create",
                kwargs={"project": self.project.sodar_uuid},
            ),
            method="POST",
            data=self.post_data_min_host,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Container.objects.count(), 1)

        container = Container.objects.first()
        result = model_to_dict(container, fields=self.post_data_min_host.keys())

        # Assert updated properties
        self.assertDictEqual(result, self.post_data_min_host)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_post_success_min_fields_mode_docker_shared(self):
        response = self.request_knox(
            reverse(
                "containers:api-create",
                kwargs={"project": self.project.sodar_uuid},
            ),
            method="POST",
            data=self.post_data_min_shared,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Container.objects.count(), 1)

        container = Container.objects.first()
        result = model_to_dict(
            container, fields=self.post_data_min_shared.keys()
        )

        # Assert updated properties
        self.assertDictEqual(result, self.post_data_min_shared)

    def test_post_success_all_fields(self):
        response = self.request_knox(
            reverse(
                "containers:api-create",
                kwargs={"project": self.project.sodar_uuid},
            ),
            method="POST",
            data=self.post_data_all,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Container.objects.count(), 1)

        container = Container.objects.first()
        result = model_to_dict(container, fields=self.post_data_all.keys())

        # Assert updated properties
        self.assertDictEqual(result, self.post_data_all)


class TestContainerDeleteAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerDeleteAPIView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    def test_delete_success_initial(self):
        response = self.request_knox(
            reverse(
                "containers:api-delete",
                kwargs={"container": self.container1.sodar_uuid},
            ),
            method="DELETE",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Container.objects.count(), 0)
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)

    @patch("containers.tasks.container_task.run")
    def test_delete_success_running(self, mock):
        self.container1.state = STATE_RUNNING
        self.container1.save()

        def _mock_delete(job_id):
            job = ContainerBackgroundJob.objects.get(id=job_id)
            job.container.state = STATE_DELETED
            job.container.save()

        mock.side_effect = _mock_delete

        response = self.request_knox(
            reverse(
                "containers:api-delete",
                kwargs={"container": self.container1.sodar_uuid},
            ),
            method="DELETE",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Container.objects.count(), 0)
        self.assertEqual(ContainerBackgroundJob.objects.count(), 0)
        mock.assert_called()

    def test_delete_non_existent(self):
        response = self.request_knox(
            reverse(
                "containers:api-delete",
                kwargs={"container": self.fake_uuid},
            ),
            method="DELETE",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Container.objects.count(), 1)


class TestContainerDetailAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerDetailAPIView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    def test_get_success(self):
        response = self.request_knox(
            reverse(
                "containers:api-detail",
                kwargs={"container": self.container1.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = model_to_dict(self.container1, exclude=["id"])
        expected["date_created"] = self.get_drf_datetime(
            self.container1.date_created
        )
        expected["date_modified"] = self.get_drf_datetime(
            self.container1.date_modified
        )
        expected["project"] = str(
            Project.objects.get(id=expected["project"]).sodar_uuid
        )
        expected["sodar_uuid"] = str(expected["sodar_uuid"])

        self.assertEqual(response.json(), expected)

    def test_get_non_existent(self):
        response = self.request_knox(
            reverse(
                "containers:api-detail",
                kwargs={"container": self.fake_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestContainerStartAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerStartAPIView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.apply_async")
    def test_get_success(self, mock):
        response = self.request_knox(
            reverse(
                "containers:api-start",
                kwargs={"container": self.container1.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

        job = ContainerBackgroundJob.objects.first()

        self.assertEqual(job.action, ACTION_START)
        self.assertEqual(job.container, self.container1)
        mock.assert_called_with(
            kwargs={"job_id": job.pk}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

    def test_get_non_existent(self):
        response = self.request_knox(
            reverse(
                "containers:api-start",
                kwargs={"container": self.fake_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestContainerStopAPIView(TestContainerCreationMixin, TestAPIViewsBase):
    """Tests for ``ContainerStopAPIView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.apply_async")
    def test_get_success(self, mock):
        response = self.request_knox(
            reverse(
                "containers:api-stop",
                kwargs={"container": self.container1.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

        job = ContainerBackgroundJob.objects.first()

        self.assertEqual(job.action, ACTION_STOP)
        self.assertEqual(job.container, self.container1)
        mock.assert_called_with(
            kwargs={"job_id": job.pk}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

    def test_get_non_existent(self):
        response = self.request_knox(
            reverse(
                "containers:api-stop",
                kwargs={"container": self.fake_uuid},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
