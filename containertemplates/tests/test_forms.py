"""Tests for the ``forms`` module."""

from containertemplates.forms import (
    ContainerTemplateSiteForm,
    ContainerTemplateProjectForm,
)
from containertemplates.tests.helpers import TestBase


class TestContainerTemplateSiteForm(TestBase):
    """Tests for ``ContainerTemplateSiteForm``."""

    def setUp(self):
        super().setUp()
        self.form_data_min = {
            "title": "some title",
        }
        self.form_data_all = {
            **self.form_data_min,
            "description": "some description",
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "timeout": 60,
            "max_retries": 10,
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
        }

    def test_min_fields(self):
        form = ContainerTemplateSiteForm(self.form_data_min)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        form = ContainerTemplateSiteForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    def test_missing_field_title(self):
        key = "title"
        self.form_data_min.pop(key)
        form = ContainerTemplateSiteForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])


class TestContainerTemplateProjectForm(TestBase):
    """Tests for ``ContainerTemplatePorjectForm``."""

    def setUp(self):
        super().setUp()
        self.form_data_min = {
            "title": "some title",
            "project": self.project,
        }
        self.form_data_all = {
            **self.form_data_min,
            "description": "some description",
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "timeout": 60,
            "max_retries": 10,
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
        }

    def test_min_fields(self):
        form = ContainerTemplateProjectForm(self.form_data_min)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        form = ContainerTemplateProjectForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    def test_missing_field_title(self):
        key = "title"
        self.form_data_min.pop(key)
        form = ContainerTemplateProjectForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])
