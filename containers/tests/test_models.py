"""Tests for the container models"""
import json

from django.forms import model_to_dict
from django.urls import reverse
from django.utils.timezone import localtime

from containers.models import (
    Container,
    STATE_INITIAL,
    LOG_LEVEL_INFO,
    ContainerLogEntry,
)
from containers.tests.factories import ContainerLogEntryFactory
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
            "Container: {}:{}:{} [{}]".format(
                self.container1.repository,
                self.container1.tag,
                self.container1.host_port,
                self.container1.state,
            ),
        )

    def test___str___no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            str(self.container1),
            "Container: {}:{} [{}]".format(
                self.container1.repository,
                self.container1.host_port,
                self.container1.state,
            ),
        )

    def test___repr___no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            repr(self.container1),
            "Container({}:{})".format(
                self.container1.repository,
                self.container1.host_port,
            ),
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.container1.get_display_name(),
            "{}:{}:{}".format(
                self.container1.repository,
                self.container1.tag,
                self.container1.host_port,
            ),
        )

    def test_get_display_name_no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            self.container1.get_display_name(),
            "{}:{}".format(
                self.container1.repository,
                self.container1.host_port,
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


class TestContainerLogEntry(TestBase):
    """Tests for the ``ContainerLogEntry`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.log_entry = ContainerLogEntryFactory(
            container=self.container1, user=self.superuser
        )
        self.log_entry_no_user = ContainerLogEntryFactory(
            container=self.container1
        )
        self.data = {
            "level": LOG_LEVEL_INFO,
            "text": "Log entry",
            "user": self.superuser,
            "container": self.container1,
        }

    def test_initialization(self):
        log_entry = ContainerLogEntry.objects.create(**self.data)
        expected = {
            **self.data,
            "user": self.superuser.pk,
            "container": self.container1.pk,
            "id": log_entry.pk,
        }
        self.assertEqual(model_to_dict(log_entry), expected)

    def test_get_date_created(self):
        self.assertEqual(
            self.log_entry.get_date_created(),
            localtime(self.log_entry.date_created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def test___str__(self):
        self.assertEqual(
            str(self.log_entry),
            "[{} {} {}] {}".format(
                self.log_entry.get_date_created(),
                self.log_entry.level.upper(),
                self.log_entry.user.username,
                self.log_entry.text,
            ),
        )

    def test___str___no_user(self):
        self.assertEqual(
            str(self.log_entry_no_user),
            "[{} {} anonymous] {}".format(
                self.log_entry_no_user.get_date_created(),
                self.log_entry_no_user.level.upper(),
                self.log_entry_no_user.text,
            ),
        )
