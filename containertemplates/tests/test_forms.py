"""Tests for the ``forms`` module."""

from containertemplates.forms import ContainerTemplateForm
from containertemplates.tests.helpers import TestBase


class TestContainerTemplateForm(TestBase):
    """Tests for ``ContainerTemplateForm``."""

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
        form = ContainerTemplateForm(self.form_data_min)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        form = ContainerTemplateForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    def test_missing_field_title(self):
        key = "title"
        self.form_data_min.pop(key)
        form = ContainerTemplateForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])
