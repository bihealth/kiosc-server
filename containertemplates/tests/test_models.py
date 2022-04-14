"""Tests for the container models"""

from django.forms import model_to_dict
from django.urls import reverse
from django.utils.timezone import localtime

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)
from containertemplates.tests.helpers import TestBase


class TestContainerTemplateSiteModel(TestBase):
    """Tests for the ``ContainerTemplateSite`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplatesite()
        self.data = {
            "title": "some title",
        }

    def test_initialization(self):
        containertemplate = ContainerTemplateSite.objects.create(**self.data)
        expected = {
            **self.data,
            "repository": None,
            "tag": None,
            "description": None,
            "command": None,
            "container_port": ContainerTemplateSite.container_port.field.default,
            "timeout": ContainerTemplateSite.timeout.field.default,
            "environment": None,
            "container_path": "",
            "heartbeat_url": None,
            "id": containertemplate.id,
            "sodar_uuid": containertemplate.sodar_uuid,
            "max_retries": containertemplate.max_retries,
            "inactivity_threshold": containertemplate.inactivity_threshold,
        }
        self.assertEqual(model_to_dict(containertemplate), expected)

    def test___str__(self):
        self.assertEqual(
            str(self.containertemplatesite1),
            self.containertemplatesite1.title,
        )

    def test___repr__(self):
        self.assertEqual(
            repr(self.containertemplatesite1),
            "ContainerTemplateSite({}, {})".format(
                self.containertemplatesite1.title,
                self.containertemplatesite1.get_repos_full(),
            ),
        )

    def test_get_repos_full(self):
        self.assertEqual(
            self.containertemplatesite1.get_repos_full(),
            "{}:{}".format(
                self.containertemplatesite1.repository,
                self.containertemplatesite1.tag,
            ),
        )

    def test_get_repos_full_no_repository(self):
        self.containertemplatesite1.repository = ""
        self.containertemplatesite1.save()
        self.assertEqual(
            self.containertemplatesite1.get_repos_full(),
            f"<no_repository>:{self.containertemplatesite1.tag}",
        )

    def test_get_repos_full_no_tag(self):
        self.containertemplatesite1.tag = ""
        self.containertemplatesite1.save()
        self.assertEqual(
            self.containertemplatesite1.get_repos_full(),
            self.containertemplatesite1.repository,
        )

    def test_get_repos_full_no_repository_no_tag(self):
        self.containertemplatesite1.tag = ""
        self.containertemplatesite1.repository = ""
        self.containertemplatesite1.save()
        self.assertEqual(
            self.containertemplatesite1.get_repos_full(),
            "<no_repository>",
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.containertemplatesite1.get_display_name(),
            "{} ({})".format(
                self.containertemplatesite1.title,
                self.containertemplatesite1.get_repos_full(),
            ),
        )

    def test_get_date_created(self):
        self.assertEqual(
            self.containertemplatesite1.get_date_created(),
            localtime(self.containertemplatesite1.date_created).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_date_modified(self):
        self.assertEqual(
            self.containertemplatesite1.get_date_modified(),
            localtime(self.containertemplatesite1.date_modified).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.containertemplatesite1.get_absolute_url(),
            reverse(
                "containertemplates:site-detail",
                kwargs={
                    "containertemplatesite": self.containertemplatesite1.sodar_uuid
                },
            ),
        )


class TestContainerTemplateProjectModel(TestBase):
    """Tests for the ``ContainerTemplateProject`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplateproject()
        self.data = {
            "title": "some title",
            "project": self.project,
        }

    def test_initialization(self):
        containertemplate = ContainerTemplateProject.objects.create(**self.data)
        expected = {
            **self.data,
            "containertemplatesite": None,
            "repository": None,
            "tag": None,
            "description": None,
            "command": None,
            "container_port": ContainerTemplateProject.container_port.field.default,
            "timeout": ContainerTemplateProject.timeout.field.default,
            "environment": None,
            "container_path": "",
            "heartbeat_url": None,
            "id": containertemplate.id,
            "sodar_uuid": containertemplate.sodar_uuid,
            "max_retries": containertemplate.max_retries,
            "project": self.project.pk,
            "inactivity_threshold": containertemplate.inactivity_threshold,
        }
        self.assertEqual(model_to_dict(containertemplate), expected)

    def test___str__(self):
        self.assertEqual(
            str(self.containertemplateproject1),
            self.containertemplateproject1.title,
        )

    def test___repr__(self):
        self.assertEqual(
            repr(self.containertemplateproject1),
            "ContainerTemplateProject({}, {}, {})".format(
                self.containertemplateproject1.project,
                self.containertemplateproject1.title,
                self.containertemplateproject1.get_repos_full(),
            ),
        )

    def test_get_repos_full(self):
        self.assertEqual(
            self.containertemplateproject1.get_repos_full(),
            "{}:{}".format(
                self.containertemplateproject1.repository,
                self.containertemplateproject1.tag,
            ),
        )

    def test_get_repos_full_no_repository(self):
        self.containertemplateproject1.repository = ""
        self.containertemplateproject1.save()
        self.assertEqual(
            self.containertemplateproject1.get_repos_full(),
            f"<no_repository>:{self.containertemplateproject1.tag}",
        )

    def test_get_repos_full_no_tag(self):
        self.containertemplateproject1.tag = ""
        self.containertemplateproject1.save()
        self.assertEqual(
            self.containertemplateproject1.get_repos_full(),
            self.containertemplateproject1.repository,
        )

    def test_get_repos_full_no_repository_no_tag(self):
        self.containertemplateproject1.tag = ""
        self.containertemplateproject1.repository = ""
        self.containertemplateproject1.save()
        self.assertEqual(
            self.containertemplateproject1.get_repos_full(),
            "<no_repository>",
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.containertemplateproject1.get_display_name(),
            "{} / {} ({})".format(
                self.containertemplateproject1.project,
                self.containertemplateproject1.title,
                self.containertemplateproject1.get_repos_full(),
            ),
        )

    def test_get_date_created(self):
        self.assertEqual(
            self.containertemplateproject1.get_date_created(),
            localtime(self.containertemplateproject1.date_created).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_date_modified(self):
        self.assertEqual(
            self.containertemplateproject1.get_date_modified(),
            localtime(self.containertemplateproject1.date_modified).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.containertemplateproject1.get_absolute_url(),
            reverse(
                "containertemplates:project-detail",
                kwargs={
                    "containertemplateproject": self.containertemplateproject1.sodar_uuid
                },
            ),
        )
