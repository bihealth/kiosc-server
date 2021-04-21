"""Tests for the container models"""
import json

from django.forms import model_to_dict
from django.urls import reverse
from django.utils.timezone import localtime

from containers.models import Container, STATE_INITIAL
from containers.tests.helpers import TestBase


class TestContainerModel(TestBase):
    """Tests for the ``Container`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.data = {
            "repository": "repository",
            "tag": "tag",
            "project": self.project,
            "container_port": 80,
            "host_port": 8080,
            "timeout": 60,
            "state": STATE_INITIAL,
            "environment": json.loads('{"test": 1}'),
        }

    def test_initialization(self):
        container = Container.objects.create(**self.data)
        expected = {
            **self.data,
            "command": None,
            "container_id": None,
            "container_path": None,
            "heartbeat_url": None,
            "environment_secret_keys": None,
            "image_id": None,
            "timeout_exceeded": False,
            "project": self.project.pk,
            "id": container.id,
            "sodar_uuid": container.sodar_uuid,
        }
        self.assertEqual(model_to_dict(container), expected)

    def test___str__(self):
        self.assertEqual(
            str(self.container1),
            "Container: {}:{} [{}]".format(
                self.container1.repository,
                self.container1.tag,
                self.container1.state.upper(),
            ),
        )

    def test___repr__(self):
        self.assertEqual(
            repr(self.container1),
            "Container({}:{}/{})".format(
                self.container1.repository,
                self.container1.tag,
                self.container1.get_date_created(),
            ),
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.container1.get_display_name(),
            "{}:{} / {}".format(
                self.container1.repository,
                self.container1.tag,
                self.container1.get_date_created(),
            ),
        )

    def test_get_display_name_no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            self.container1.get_display_name(),
            "{} / {}".format(
                self.container1.repository,
                self.container1.get_date_created(),
            ),
        )

    def test_get_date_created(self):
        self.assertEqual(
            self.container1.get_date_created(),
            localtime(self.container1.date_created).strftime("%Y-%m-%d %H:%M"),
        )

    def test_get_date_modified(self):
        self.assertEqual(
            self.container1.get_date_modified(),
            localtime(self.container1.date_modified).strftime("%Y-%m-%d %H:%M"),
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.container1.get_absolute_url(),
            reverse(
                "containers:container-detail",
                kwargs={"container": self.container1.sodar_uuid},
            ),
        )
