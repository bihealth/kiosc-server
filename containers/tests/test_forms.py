"""Tests for the ``forms`` module."""

from containers.forms import ContainerForm
from containers.tests.helpers import TestBase


class TestContainerForm(TestBase):
    """Tests for ``ContainerForm``."""

    def setUp(self):
        super().setUp()
        self.form_data_min = {
            "host_port": 8080,
            "environment": '{"test": 1}',
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "project": self.project,
            "max_retries": 10,
        }
        self.form_data_all = {
            **self.form_data_min,
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment_secret_keys": "test",
            "command": "some command",
        }

    def test_min_fields(self):
        form = ContainerForm(self.form_data_min)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        form = ContainerForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    def test_missing_field_host_port(self):
        key = "host_port"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_environment(self):
        key = "environment"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_repository(self):
        key = "repository"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_tag(self):
        key = "tag"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_container_port(self):
        key = "container_port"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_timeout(self):
        key = "timeout"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_missing_field_project(self):
        key = "project"
        self.form_data_min.pop(key)
        form = ContainerForm(self.form_data_min)
        self.assertEqual(form.errors[key], ["This field is required."])

    def test_environment_secret_keys_matching(self):
        self.form_data_min.update(
            {
                "environment": '{"test1": 1, "test2": 2, "test3": 3}',
                "environment_secret_keys": "test1,test3",
            }
        )
        form = ContainerForm(self.form_data_min)
        self.assertTrue(form.is_valid())

    def test_environment_secret_keys_mismatching(self):
        self.form_data_min.update(
            {
                "environment": '{"test1": 1, "test2": 2, "test3": 3}',
                "environment_secret_keys": "test1,not_an_env_key",
            }
        )
        form = ContainerForm(self.form_data_min)
        self.assertEqual(
            form.errors["environment_secret_keys"],
            ['Secret key "not_an_env_key" is not in environment!'],
        )
