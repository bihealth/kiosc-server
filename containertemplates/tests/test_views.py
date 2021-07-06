"""Tests for the containertemplate views."""
import json

from django.contrib.messages import get_messages
from urllib3_mock import Responses

from django.forms import model_to_dict
from django.urls import reverse

from containertemplates.forms import (
    ContainerTemplateSiteToProjectCopyForm,
    ContainerTemplateProjectToProjectCopyForm,
)
from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)
from containertemplates.tests.helpers import TestBase


responses = Responses("requests.packages.urllib3")


class TestContainerTemplateSiteListView(TestBase):
    """Tests for ``ContainerTemplateSiteListView``."""

    def test_get_success_list_empty(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-list",
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["object_list"]), 0)

    def test_get_success_list_one_item(self):
        self.create_one_containertemplatesite()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-list",
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].id, self.containertemplatesite1.id)

    def test_get_success_list_two_items(self):
        self.create_two_containertemplatesites()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-list",
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].id, self.containertemplatesite2.id)
            self.assertEqual(items[1].id, self.containertemplatesite1.id)


class TestContainerTemplateSiteCreateView(TestBase):
    """Tests for ``ContainerTemplateSiteCreateView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-create",
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
                    "containertemplates:site-create",
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplateSite.objects.count(), 1)

            containertemplate = ContainerTemplateSite.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-detail",
                    kwargs={
                        "containertemplatesite": containertemplate.sodar_uuid
                    },
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
                    "containertemplates:site-create",
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplateSite.objects.count(), 1)

            containertemplate = ContainerTemplateSite.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-detail",
                    kwargs={
                        "containertemplatesite": containertemplate.sodar_uuid
                    },
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(containertemplate, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)


class TestContainerTemplateSiteDeleteView(TestBase):
    """Tests for ``ContainerTemplateSiteDeleteView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-delete",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(ContainerTemplateSite.objects.count(), 1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-delete",
                    kwargs={"containertemplatesite": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplateSite.objects.count(), 1)

    def test_post_success_deleted(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:site-delete",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-list",
                ),
            )

            self.assertEqual(ContainerTemplateSite.objects.count(), 0)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:site-delete",
                    kwargs={"containertemplatesite": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplateSite.objects.count(), 1)


class TestContainerTemplateSiteUpdateView(TestBase):
    """Tests for ``ContainerTemplateSiteUpdateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-update",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-update",
                    kwargs={"containertemplatesite": self.fake_uuid},
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
                    "containertemplates:site-update",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplatesite1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-detail",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                ),
            )

            result = model_to_dict(
                self.containertemplatesite1, fields=post_data.keys()
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
            "container_port": self.containertemplatesite1.container_port + 100,
            "timeout": self.containertemplatesite1.timeout + 60,
            "container_path": "updated/path",
            "heartbeat_url": "https://updated.url",
            "environment_secret_keys": "updated",
            "command": "updated command",
            "max_retries": 13,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:site-update",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplatesite1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-detail",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(
                self.containertemplatesite1, fields=post_data.keys()
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
                    "containertemplates:site-update",
                    kwargs={"containertemplatesite": self.fake_uuid},
                ),
                post_data,
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateSiteDetailView(TestBase):
    """Tests for ``ContainerTemplateSiteDetailView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-detail",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context["object"], self.containertemplatesite1
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-detail",
                    kwargs={"containertemplatesite": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateSiteDuplicateView(TestBase):
    """Tests for ``ContainerTemplateSiteDuplicateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-duplicate",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:site-list",
                ),
            )
            self.assertEqual(ContainerTemplateSite.objects.count(), 2)
            dup_obj = ContainerTemplateSite.objects.get(
                title__contains="(Duplicate)"
            )
            orig = model_to_dict(
                self.containertemplatesite1,
                exclude=["id", "sodar_uuid", "title"],
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title,
                f"{self.containertemplatesite1.title} (Duplicate)",
            )

    def test_get_success_with_existing_duplicate(self):
        with self.login(self.superuser):
            # Create first duplicate
            self.client.get(
                reverse(
                    "containertemplates:site-duplicate",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            # Create second duplicate
            self.client.get(
                reverse(
                    "containertemplates:site-duplicate",
                    kwargs={
                        "containertemplatesite": self.containertemplatesite1.sodar_uuid
                    },
                )
            )

            self.assertEqual(ContainerTemplateSite.objects.count(), 3)

            dup_obj = ContainerTemplateSite.objects.get(
                title__contains="(Duplicate 2)"
            )
            orig = model_to_dict(
                self.containertemplatesite1,
                exclude=["id", "sodar_uuid", "title"],
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title,
                f"{self.containertemplatesite1.title} (Duplicate 2)",
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:site-duplicate",
                    kwargs={"containertemplatesite": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateProjectListView(TestBase):
    """Tests for ``ContainerTemplateProjectListView``."""

    def test_get_success_list_empty(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["object_list"]), 0)

    def test_get_success_list_one_item(self):
        self.create_one_containertemplateproject()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].id, self.containertemplateproject1.id)

    def test_get_success_list_two_items(self):
        self.create_two_containertemplateprojects()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

            items = list(response.context["object_list"])

            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].id, self.containertemplateproject2.id)
            self.assertEqual(items[1].id, self.containertemplateproject1.id)


class TestContainerTemplateProjectCreateView(TestBase):
    """Tests for ``ContainerTemplateProjectCreateView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-create",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_post_success_min_fields(self):
        post_data = {
            "title": "some other title",
            "project": self.project.pk,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 1)

            containertemplate = ContainerTemplateProject.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-detail",
                    kwargs={
                        "containertemplateproject": containertemplate.sodar_uuid
                    },
                ),
            )

            result = model_to_dict(containertemplate, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_success_all_fields(self):
        post_data = {
            "title": "some other title",
            "project": self.project.pk,
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
                    "containertemplates:project-create",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                post_data,
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 1)

            containertemplate = ContainerTemplateProject.objects.first()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-detail",
                    kwargs={
                        "containertemplateproject": containertemplate.sodar_uuid
                    },
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(containertemplate, fields=post_data.keys())

            # Assert updated properties
            self.assertDictEqual(result, post_data)


class TestContainerTemplateProjectDeleteView(TestBase):
    """Tests for ``ContainerTemplateProjectDeleteView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplateproject()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-delete",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(ContainerTemplateProject.objects.count(), 1)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-delete",
                    kwargs={"containertemplateproject": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplateProject.objects.count(), 1)

    def test_post_success_deleted(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-delete",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 0)

    def test_post_non_existent(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-delete",
                    kwargs={"containertemplateproject": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(ContainerTemplateProject.objects.count(), 1)


class TestContainerTemplateProjectUpdateView(TestBase):
    """Tests for ``ContainerTemplateProjectUpdateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplateproject()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-update",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-update",
                    kwargs={"containertemplateproject": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)

    def test_post_success_min_fields(self):
        post_data = {
            "title": "updated title",
            "project": self.project.pk,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-update",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplateproject1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-detail",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                ),
            )

            result = model_to_dict(
                self.containertemplateproject1, fields=post_data.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_success_all_fields(self):
        post_data = {
            "title": "updated title",
            "project": self.project.pk,
            "description": "updated description",
            "environment": '{"updated": 1234}',
            "repository": "another_repository",
            "tag": "another_tag",
            "container_port": self.containertemplateproject1.container_port
            + 100,
            "timeout": self.containertemplateproject1.timeout + 60,
            "container_path": "updated/path",
            "heartbeat_url": "https://updated.url",
            "environment_secret_keys": "updated",
            "command": "updated command",
            "max_retries": 13,
        }

        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-update",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                ),
                post_data,
            )

            # Get updated object
            self.containertemplateproject1.refresh_from_db()

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-detail",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                ),
            )

            post_data["environment"] = json.loads(post_data["environment"])
            result = model_to_dict(
                self.containertemplateproject1, fields=post_data.keys()
            )

            # Assert updated properties
            self.assertDictEqual(result, post_data)

    def test_post_non_existent(self):
        post_data = {
            "title": "some other title",
            "project": self.project.pk,
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
                    "containertemplates:project-update",
                    kwargs={"containertemplateproject": self.fake_uuid},
                ),
                post_data,
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateProjectDetailView(TestBase):
    """Tests for ``ContainerTemplateProjectDetailView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplateproject()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-detail",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.context["object"], self.containertemplateproject1
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-detail",
                    kwargs={"containertemplateproject": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateProjectDuplicateView(TestBase):
    """Tests for ``ContainerTemplateProjectDuplicateView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplateproject()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-duplicate",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )
            self.assertEqual(ContainerTemplateProject.objects.count(), 2)
            dup_obj = ContainerTemplateProject.objects.get(
                title__contains="(Duplicate)"
            )
            orig = model_to_dict(
                self.containertemplateproject1,
                exclude=["id", "sodar_uuid", "title"],
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title,
                f"{self.containertemplateproject1.title} (Duplicate)",
            )

    def test_get_success_with_existing_duplicate(self):
        with self.login(self.superuser):
            # Create first duplicate
            self.client.get(
                reverse(
                    "containertemplates:project-duplicate",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            # Create second duplicate
            self.client.get(
                reverse(
                    "containertemplates:project-duplicate",
                    kwargs={
                        "containertemplateproject": self.containertemplateproject1.sodar_uuid
                    },
                )
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 3)

            dup_obj = ContainerTemplateProject.objects.get(
                title__contains="(Duplicate 2)"
            )
            orig = model_to_dict(
                self.containertemplateproject1,
                exclude=["id", "sodar_uuid", "title"],
            )
            dup = model_to_dict(dup_obj, exclude=["id", "sodar_uuid", "title"])
            self.assertEqual(orig, dup)
            self.assertEqual(
                dup_obj.title,
                f"{self.containertemplateproject1.title} (Duplicate 2)",
            )

    def test_get_non_existent(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-duplicate",
                    kwargs={"containertemplateproject": self.fake_uuid},
                )
            )

            self.assertEqual(response.status_code, 404)


class TestContainerTemplateProjectCopyView(TestBase):
    """Tests for ``ContainerTemplateProjectCopyView``."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.create_four_containertemplates_in_two_projects()
        self.create_fake_uuid()

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(
                response.context.get("site_to_project_copy_form"),
                ContainerTemplateSiteToProjectCopyForm,
            )
            self.assertIsInstance(
                response.context.get("project_to_project_copy_form"),
                ContainerTemplateProjectToProjectCopyForm,
            )

    def test_post_success_site_wide(self):
        with self.login(self.superuser):
            # Create first duplicate
            self.client.post(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                {
                    "source": self.containertemplatesite1.pk,
                    "site_or_project": "site",
                },
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 5)

            copy_obj = ContainerTemplateProject.objects.get(
                title__contains="(Copy)"
            )
            orig = model_to_dict(
                self.containertemplatesite1,
                exclude=["id", "sodar_uuid", "title"],
            )
            copy = model_to_dict(
                copy_obj,
                exclude=[
                    "id",
                    "sodar_uuid",
                    "title",
                    "project",
                    "containertemplatesite",
                ],
            )
            self.assertEqual(orig, copy)
            self.assertEqual(
                copy_obj.title,
                f"{self.containertemplatesite1.title} (Copy)",
            )
            self.assertEqual(
                copy_obj.containertemplatesite,
                self.containertemplatesite1,
            )
            self.assertEqual(
                copy_obj.project,
                self.project,
            )

    def test_post_success_project_wide(self):
        with self.login(self.superuser):
            # Create first duplicate
            self.client.post(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                {
                    "source": self.containertemplateproject1_project2.pk,
                    "site_or_project": "project",
                },
            )

            self.assertEqual(ContainerTemplateProject.objects.count(), 5)

            copy_obj = ContainerTemplateProject.objects.get(
                title__contains="(Copy)"
            )
            orig = model_to_dict(
                self.containertemplateproject1_project2,
                exclude=["id", "sodar_uuid", "title", "project"],
            )
            copy = model_to_dict(
                copy_obj, exclude=["id", "sodar_uuid", "title", "project"]
            )
            self.assertEqual(orig, copy)
            self.assertEqual(
                copy_obj.title,
                f"{self.containertemplateproject1_project2.title} (Copy)",
            )
            self.assertEqual(
                copy_obj.project,
                self.project,
            )

    def test_post_non_existent_mode(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                {
                    "source": 0,
                    "site_or_project": "non_existent",
                },
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )
            self.assertEqual(
                str(list(get_messages(response.wsgi_request))[0]),
                "Can't determine model of container template source!",
            )

    def test_post_non_existent_site_wide(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                {
                    "source": 999,
                    "site_or_project": "site",
                },
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )
            self.assertEqual(
                str(list(get_messages(response.wsgi_request))[0]),
                "Source template not found!",
            )

    def test_post_non_existent_project_wide(self):
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    "containertemplates:project-copy",
                    kwargs={"project": self.project.sodar_uuid},
                ),
                {
                    "source": 999,
                    "site_or_project": "project",
                },
            )

            self.assertRedirects(
                response,
                reverse(
                    "containertemplates:project-list",
                    kwargs={"project": self.project.sodar_uuid},
                ),
            )
            self.assertEqual(
                str(list(get_messages(response.wsgi_request))[0]),
                "Source template not found!",
            )
