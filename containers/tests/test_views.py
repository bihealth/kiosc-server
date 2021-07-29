"""Tests for the container views."""
import json
from unittest.mock import patch

from django.contrib.messages import get_messages
from urllib3_mock import Responses

from django.forms import model_to_dict
from django.urls import reverse
from django.test import override_settings

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
from containertemplates.forms import ContainerTemplateSelectorForm


responses = Responses("requests.packages.urllib3")


class TestContainerListView(TestBase):
    """Tests for ``ContainerListView``."""

    def test_get_success_list_empty(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:list",
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
                    "containers:list",
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
                    "containers:list",
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

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:create",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(
                response.context["containertemplate_form"],
                ContainerTemplateSelectorForm,
            )

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_post_success_min_fields_mode_host(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                self.post_data_min_host,
            )

            self.assertEqual(Container.objects.count(), 1)

            container = Container.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
                    kwargs={"container": container.sodar_uuid},
                ),
            )

            self.post_data_min_host["environment"] = json.loads(
                self.post_data_min_host["environment"]
            )
            result = model_to_dict(
                container, fields=self.post_data_min_host.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_min_host)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_post_success_min_fields_mode_docker_shared(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                self.post_data_min_shared,
            )

            self.assertEqual(Container.objects.count(), 1)

            container = Container.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
                    kwargs={"container": container.sodar_uuid},
                ),
            )

            self.post_data_min_shared["environment"] = json.loads(
                self.post_data_min_shared["environment"]
            )
            result = model_to_dict(
                container, fields=self.post_data_min_shared.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_min_shared)

    def test_post_success_all_fields(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                self.post_data_all,
            )

            self.assertEqual(Container.objects.count(), 1)

            container = Container.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
                    kwargs={"container": container.sodar_uuid},
                ),
            )

            self.post_data_all["environment"] = json.loads(
                self.post_data_all["environment"]
            )
            result = model_to_dict(container, fields=self.post_data_all.keys())

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_all)


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
                    "containers:delete",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(Container.objects.count(), 1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:delete",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(Container.objects.count(), 1)

    def test_post_success_deleted(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:delete",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containers:list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )

            self.assertEqual(Container.objects.count(), 0)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:delete",
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
        self.post_data_shared = {
            "title": "Title Update",
            "description": "updated description",
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.container1.container_port + 100,
            "timeout": self.container1.timeout + 60,
            "project": self.project.pk,
            "max_retries": 12,
        }
        self.post_data_host = {
            **self.post_data_shared,
            "host_port": self.container1.host_port + 100,
        }

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:update",
                    kwargs={"container": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_post_success_updated_initial_mode_host(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_host,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )

            self.post_data_host["environment"] = json.loads(
                self.post_data_host["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_host.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_host)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_post_success_updated_initial_mode_docker_shared(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_shared,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
            )

            self.post_data_shared["environment"] = json.loads(
                self.post_data_shared["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_shared.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_shared)

    @override_settings(KIOSC_NETWORK_MODE="host")
    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_running_mode_host(self, mock):
        self.container1.state = STATE_RUNNING
        self.container1.save()

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_host,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            self.post_data_host["environment"] = json.loads(
                self.post_data_host["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_host.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_host)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_running_mode_docker_shared(self, mock):
        self.container1.state = STATE_RUNNING
        self.container1.save()

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_shared,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            self.post_data_shared["environment"] = json.loads(
                self.post_data_shared["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_shared.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_shared)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    @override_settings(KIOSC_NETWORK_MODE="host")
    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_paused_mode_host(self, mock):
        self.container1.state = STATE_PAUSED
        self.container1.save()

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_host,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            self.post_data_host["environment"] = json.loads(
                self.post_data_host["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_host.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_host)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    @patch("containers.tasks.container_task.delay")
    def test_post_success_updated_paused_mode_docker_shared(self, mock):
        self.container1.state = STATE_PAUSED
        self.container1.save()

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                self.post_data_shared,
            )

            # Get updated object
            self.container1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containers:restart",
                    kwargs={"container": self.container1.sodar_uuid},
                ),
                status_code=302,
                target_status_code=302,
            )

            self.post_data_shared["environment"] = json.loads(
                self.post_data_shared["environment"]
            )
            result = model_to_dict(
                self.container1, fields=self.post_data_shared.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, self.post_data_shared)

            # Assert job call
            mock.assert_called()

            # Assert background job
            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)
            bg_job = ContainerBackgroundJob.objects.first()
            self.assertEqual(bg_job.action, ACTION_RESTART)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containers:update",
                    kwargs={"container": self.fake_uuid},
                ),
                self.post_data_host,
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
                    "containers:detail",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["object"], self.container1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containers:detail",
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
                    "containers:start",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
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
                    "containers:start",
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
                    "containers:stop",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
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
                    "containers:stop",
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
                    "containers:restart",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
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
                    "containers:restart",
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
                    "containers:pause",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
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
                    "containers:pause",
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
                    "containers:unpause",
                    kwargs={"container": self.container1.sodar_uuid},
                )
            )

            self.assertEqual(ContainerBackgroundJob.objects.count(), 1)

            job = ContainerBackgroundJob.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containers:detail",
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
                    "containers:unpause",
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

    @override_settings(KIOSC_NETWORK_MODE="host")
    @responses.activate
    def test_get_success_mode_host(self):
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
                "localhost",
            )
            self.assertEqual(responses.calls[0].request.url, container_url)

    @override_settings(KIOSC_NETWORK_MODE="host")
    @responses.activate
    def test_get_success_mode_host_host_port_missing(self):
        self.container1.host_port = None
        self.container1.save()

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

            self.assertRedirects(
                response,
                reverse(
                    "containers:list",
                    kwargs={"project": self.container1.project.sodar_uuid},
                ),
            )
            self.assertEqual(
                str(list(get_messages(response.wsgi_request))[0]),
                "Host port not set.",
            )
            self.assertEqual(len(responses.calls), 0)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    @responses.activate
    def test_get_success_mode_docker_shared(self):
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

    @override_settings(KIOSC_NETWORK_MODE="host")
    @responses.activate
    def test_get_success_with_path_mode_host(self):
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
                "localhost",
            )
            self.assertEqual(responses.calls[0].request.url, container_url)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    @responses.activate
    def test_get_success_with_path_mode_docker_shared(self):
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

    @override_settings(KIOSC_NETWORK_MODE="host")
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

    @override_settings(KIOSC_NETWORK_MODE="host")
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

    @override_settings(KIOSC_NETWORK_MODE="host")
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

    @override_settings(KIOSC_NETWORK_MODE="host")
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
