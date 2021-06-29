"""Tests for the containertemplate views."""
import json

from urllib3_mock import Responses

from django.forms import model_to_dict
from django.urls import reverse

from containertemplates.models import ContainerTemplate
from containertemplates.tests.helpers import TestBase


responses = Responses("requests.packages.urllib3")


class TestContainerTemplateListView(TestBase):
    """Tests for ``ContainerTemplateListView``."""

    def test_get_success_list_empty(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:list",
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["object_list"]), 0)

    def test_get_success_list_one_item(self):
        self.create_one_containertemplate()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:list",
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].id, self.containertemplate1.id)

    def test_get_success_list_two_items(self):
        self.create_two_containertemplates()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:list",
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].id, self.containertemplate2.id)
            self.assertEqual(items[1].id, self.containertemplate1.id)


class TestContainerTemplateCreateView(TestBase):
    """Tests for ``ContainerTemplateCreateView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:create",
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_post_success_min_fields(self):
        post_data = {
            "title": "some other title",
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:create",
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplate.objects.count(), 1)

            containertemplate = ContainerTemplate.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:detail",
                    kwargs={"containertemplate": containertemplate.sodar_uuid},
                ),
            )

            result = model_to_dict(containertemplate, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_success_all_fields(self):
        post_data = {
            "title": "some other title",
            "description": "some other description",
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
            "max_retries": 10,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:create",
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplate.objects.count(), 1)

            containertemplate = ContainerTemplate.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:detail",
                    kwargs={"containertemplate": containertemplate.sodar_uuid},
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(containertemplate, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)


class TestContainerTemplateDeleteView(TestBase):
    """Tests for ``ContainerTemplateDeleteView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplate()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:delete",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(ContainerTemplate.objects.count(), 1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:delete",
                    kwargs={"containertemplate": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplate.objects.count(), 1)

    def test_post_success_deleted(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:delete",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:list",
                ),
            )

            self.assertEqual(ContainerTemplate.objects.count(), 0)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:delete",
                    kwargs={"containertemplate": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplate.objects.count(), 1)


class TestContainerTemplateUpdateView(TestBase):
    """Tests for ``ContainerTemplateUpdateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplate()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:update",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:update",
                    kwargs={"containertemplate": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)

    def test_post_success_min_fields(self):
        post_data = {
            "title": "updated title",
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:update",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplate1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:detail",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                ),
            )

            result = model_to_dict(
                self.containertemplate1, fields=post_data.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_success_all_fields(self):
        post_data = {
            "title": "updated title",
            "description": "updated description",
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.containertemplate1.container_port + 100,
            "timeout": self.containertemplate1.timeout + 60,
            "container_path": "updated/path",
            "heartbeat_url": "https://updated.url",
            "environment_secret_keys": "updated",
            "command": "updated command",
            "max_retries": 13,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:update",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplate1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:detail",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(
                self.containertemplate1, fields=post_data.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_non_existent(self):
        post_data = {
            "title": "some other title",
            "description": "some other description",
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": 443,
            "timeout": 99,
            "max_retries": 10,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:update",
                    kwargs={"containertemplate": self.fake_uuid},
                ),
                post_data,
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateDetailView(TestBase):
    """Tests for ``ContainerTemplateDetailView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplate()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:detail",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context["object"], self.containertemplate1
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:detail",
                    kwargs={"containertemplate": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateDuplicateView(TestBase):
    """Tests for ``ContainerTemplateDuplicateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplate()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:duplicate",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:list",
                ),
            )
            self.assertEqual(ContainerTemplate.objects.count(), 2)
            dup_obj = ContainerTemplate.objects.get(
                title__contains="(Duplicate)"
            )
            orig = model_to_dict(
                self.containertemplate1, exclude=["id", "sodar_uuid", "title"]
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title, f"{self.containertemplate1.title} (Duplicate)"
            )

    def test_get_success_with_existing_duplicate(self):
        with self.login(self.superuser):
            # Create first duplicate
            self.client.get(
                reverse(
                    "containertemplates:duplicate",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            # Create second duplicate
            self.client.get(
                reverse(
                    "containertemplates:duplicate",
                    kwargs={
                        "containertemplate": self.containertemplate1.sodar_uuid
                    },
                )
            )

            self.assertEqual(ContainerTemplate.objects.count(), 3)

            dup_obj = ContainerTemplate.objects.get(
                title__contains="(Duplicate 2)"
            )
            orig = model_to_dict(
                self.containertemplate1, exclude=["id", "sodar_uuid", "title"]
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title, f"{self.containertemplate1.title} (Duplicate 2)"
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:duplicate",
                    kwargs={"containertemplate": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
