"""Tests for the container views."""
import json
from unittest.mock import patch

from urllib3_mock import Responses

from django.forms import model_to_dict
from django.urls import reverse

from containers.models import (
    Container,
    ContainerBackgroundJob,
    ACTION_START,
    ACTION_STOP,
    ACTION_RESTART,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_EXITED,
)
from containers.tests.helpers import TestBase


responses = Responses("requests.packages.urllib3")


class TestContainerListView(TestBase):
    """Tests for ``ContainerListView``."""

    def test_get_success_list_empty(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["object_list"]), 0)

    def test_get_success_list_one_item(self):
        self.create_one_container()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].id, self.container1.id)

    def test_get_success_list_two_items(self):
        self.create_two_containers()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].id, self.container2.id)
            self.assertEqual(items[1].id, self.container1.id)


class TestContainerCreateView(TestBase):
    """Tests for ``ContainerCreateView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-create",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_post_success_min_fields(self):
        post_data = {
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "project": self.project.pk,
            "max_retries": 10,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                post_data,
            )

            self.assertEqual(Container.objects.count(), 1)

            container = Container.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": container.sodar_uuid},
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(container, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_success_all_fields(self):
        post_data = {
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "project": self.project.pk,
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
            "max_retries": 10,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                post_data,
            )

            self.assertEqual(Container.objects.count(), 1)

            container = Container.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": container.sodar_uuid},
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(container, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)


class TestContainerDeleteView(TestBase):
    """Tests for ``ContainerDeleteView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-delete",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(Container.objects.count(), 1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-delete",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(Container.objects.count(), 1)

    def test_post_success_deleted(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-delete",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )

            self.assertEqual(Container.objects.count(), 0)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-delete",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(Container.objects.count(), 1)


class TestContainerUpdateView(TestBase):
    """Tests for ``ContainerUpdateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)

    def test_post_success_updated_initial(self):
        post_data = {
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.container1.container_port + 100,
            "timeout": self.container1.timeout + 60,
            "project": self.project.pk,
            "max_retries": 12,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                post_data,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(self.container1, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_running(self, mock):
        self.container1.state = STATE_RUNNING
        self.container1.save()

        post_data = {
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.container1.container_port + 100,
            "timeout": self.container1.timeout + 60,
            "project": self.project.pk,
            "max_retries": 12,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                post_data,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(self.container1, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_paused(self, mock):
        self.container1.state = STATE_PAUSED
        self.container1.save()

        post_data = {
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.container1.container_port + 100,
            "timeout": self.container1.timeout + 60,
            "project": self.project.pk,
            "max_retries": 12,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                post_data,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(self.container1, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    def test_post_non_existent(self):
        post_data = {
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": 443,
            "timeout": 99,
            "project": self.project.pk,
            "max_retries": 10,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:container-update",
                    kwargs={"container": self.fake_uuid},
                ),
                post_data,
            )

            self.assertEqual(response.status_code, 404)


class TestContainerDetailView(TestBase):
    """Tests for ``ContainerDetailView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["object"], self.container1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerStartView(TestBase):
    """Tests for ``ContainerStartView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.delay")
    def test_get_success(self, mock):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-start",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )
            self.assertEqual(job.action, ACTION_START)
            self.assertEqual(job.container, self.container1)
            mock.assert_called_with(job_id=job.pk)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-start",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerStopView(TestBase):
    """Tests for ``ContainerStopView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.delay")
    def test_get_success(self, mock):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-stop",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )
            self.assertEqual(job.action, ACTION_STOP)
            self.assertEqual(job.container, self.container1)
            mock.assert_called_with(job_id=job.pk)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-stop",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerRestartView(TestBase):
    """Tests for ``ContainerRestartView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.delay")
    def test_get_success(self, mock):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-restart",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )
            self.assertEqual(job.action, ACTION_RESTART)
            self.assertEqual(job.container, self.container1)
            mock.assert_called_with(job_id=job.pk)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-restart",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerPauseView(TestBase):
    """Tests for ``ContainerPauseView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.delay")
    def test_get_success(self, mock):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-pause",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )
            self.assertEqual(job.action, ACTION_PAUSE)
            self.assertEqual(job.container, self.container1)
            mock.assert_called_with(job_id=job.pk)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-pause",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerUnpauseView(TestBase):
    """Tests for ``ContainerUnpauseView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @patch("containers.tasks.container_task.delay")
    def test_get_success(self, mock):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-unpause",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:container-detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )
            self.assertEqual(job.action, ACTION_UNPAUSE)
            self.assertEqual(job.container, self.container1)
            mock.assert_called_with(job_id=job.pk)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:container-unpause",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestReverseProxyView(TestBase):
    """Tests for ``ReverseProxyView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @responses.activate
    def test_get_success(self):
        with self.login(self.superuser):

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )
            response = self.client.get(
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(responses.calls), 1)
            self.assertEqual(
                responses.calls[0].request.host,
                self.container1.container_id[:12],
            )
            self.assertEqual(responses.calls[0].request.url, container_url)

    @responses.activate
    def test_get_success_with_path(self):
        with self.login(self.superuser):
            self.container1.container_path = "this/is/some/path"
            self.container1.save()

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )
            response = self.client.get(
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(responses.calls), 1)
            self.assertEqual(
                responses.calls[0].request.host,
                self.container1.container_id[:12],
            )
            self.assertEqual(responses.calls[0].request.url, container_url)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.fake_uuid,
                        "path": "",
                    },
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerProxyLobbyView(TestBase):
    """Tests for ``ContainerProxyLobbyView``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.create_fake_uuid()

    @responses.activate
    def test_get_success_running(self):
        self.container1.state = STATE_RUNNING
        self.container1.save()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:proxy-lobby",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                ),
            )

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                ),
                status_code=302,
                target_status_code=200,
            )

    #    @patch("containers.tasks.container_task.delay")
    @responses.activate
    def test_get_success_running_with_path(self):
        with self.login(self.superuser):
            self.container1.state = STATE_RUNNING
            self.container1.container_path = "this/is/some/path"
            self.container1.save()

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )

            response = self.client.get(
                reverse(
                    "containers:proxy-lobby",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                ),
                status_code=302,
                target_status_code=200,
            )

    @patch("containers.tasks.container_task.delay")
    @responses.activate
    def test_get_success_paused_with_path(self, mock):
        with self.login(self.superuser):
            self.container1.state = STATE_PAUSED
            self.container1.save()

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )

            response = self.client.get(
                reverse(
                    "containers:proxy-lobby",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                ),
                status_code=302,
                target_status_code=200,
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_UNPAUSE)
            mock.assert_called_once_with(job_id=bg_job.id)

    @patch("containers.tasks.container_task.delay")
    @responses.activate
    def test_get_success_stopped_with_path(self, mock):
        with self.login(self.superuser):
            self.container1.state = STATE_EXITED
            self.container1.save()

            def request_callback(request):
                return 200, {}, "abc".encode("utf-8")

            container_url = f"/{self.container1.container_path}"
            responses.add_callback(
                "GET", container_url, callback=request_callback
            )

            response = self.client.get(
                reverse(
                    "containers:proxy-lobby",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:proxy",
                    kwargs={
                        "container": self.container1.sodar_uuid,
                        "path": self.container1.container_path,
                    },
                ),
                status_code=302,
                target_status_code=200,
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_START)
            mock.assert_called_once_with(job_id=bg_job.id)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:proxy-lobby",
                    kwargs={
                        "container": self.fake_uuid,
                        "path": "",
                    },
                )
            )

            self.assertEqual(response.status_code, 404)
