"""Tests for the container models"""

from django.forms import model_to_dict
from django.urls import reverse
from django.utils.timezone import localtime

from containertemplates.models import ContainerTemplate
from containertemplates.tests.helpers import TestBase


class TestContainerTemplateModel(TestBase):
    """Tests for the ``ContainerTemplate`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_containertemplate()
        self.data = {
            "title": "some title",
        }

    def test_initialization(self):
        container = ContainerTemplate.objects.create(**self.data)
        expected = {
            **self.data,
            "repository": None,
            "tag": None,
            "description": None,
            "command": None,
            "container_port": ContainerTemplate.container_port.field.default,
            "timeout": ContainerTemplate.timeout.field.default,
            "environment": None,
            "container_path": None,
            "heartbeat_url": None,
            "environment_secret_keys": None,
            "id": container.id,
            "sodar_uuid": container.sodar_uuid,
            "max_retries": container.max_retries,
        }
        self.assertEqual(model_to_dict(container), expected)

    def test___str__(self):
        self.assertEqual(
            str(self.containertemplate1),
            "ContainerTemplate: {} ({})".format(
                self.containertemplate1.title,
                self.containertemplate1.get_repos_full(),
            ),
        )

    def test___repr__(self):
        self.assertEqual(
            repr(self.containertemplate1),
            "ContainerTemplate({}, {})".format(
                self.containertemplate1.title,
                self.containertemplate1.get_repos_full(),
            ),
        )

    def test_get_repos_full(self):
        self.assertEqual(
            self.containertemplate1.get_repos_full(),
            "{}:{}".format(
                self.containertemplate1.repository,
                self.containertemplate1.tag,
            ),
        )

    def test_get_repos_full_no_repository(self):
        self.containertemplate1.repository = ""
        self.containertemplate1.save()
        self.assertEqual(
            self.containertemplate1.get_repos_full(),
            f"<no_repository>:{self.containertemplate1.tag}",
        )

    def test_get_repos_full_no_tag(self):
        self.containertemplate1.tag = ""
        self.containertemplate1.save()
        self.assertEqual(
            self.containertemplate1.get_repos_full(),
            self.containertemplate1.repository,
        )

    def test_get_repos_full_no_repository_no_tag(self):
        self.containertemplate1.tag = ""
        self.containertemplate1.repository = ""
        self.containertemplate1.save()
        self.assertEqual(
            self.containertemplate1.get_repos_full(),
            "<no_repository>",
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.containertemplate1.get_display_name(),
            self.containertemplate1.title,
        )

    def test_get_date_created(self):
        self.assertEqual(
            self.containertemplate1.get_date_created(),
            localtime(self.containertemplate1.date_created).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_date_modified(self):
        self.assertEqual(
            self.containertemplate1.get_date_modified(),
            localtime(self.containertemplate1.date_modified).strftime(
                "%Y-%m-%d %H:%M"
            ),
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.containertemplate1.get_absolute_url(),
            reverse(
                "containertemplates:detail",
                kwargs={
                    "containertemplate": self.containertemplate1.sodar_uuid
                },
            ),
        )
