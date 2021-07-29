"""Tests for the ``forms`` module."""

from containers.forms import ContainerForm
from containers.tests.helpers import TestBase

from django.test import override_settings


class TestContainerForm(TestBase):
    """Tests for ``ContainerForm``."""

    def setUp(self):
        super().setUp()
        self.create_containertemplates()
        self.form_data_min_mode_docker_shared = {
            "title": "Title",
            "repository": "repository",
            "tag": "tag",
            "container_port": 80,
            "timeout": 60,
            "project": self.project,
            "max_retries": 10,
        }
        self.form_data_min_mode_host = {
            **self.form_data_min_mode_docker_shared,
            "host_port": 8000,
        }
        self.form_data_all = {
            **self.form_data_min_mode_host,
            "description": "some description",
            "container_path": "some/path",
            "heartbeat_url": "https://heartbeat.url",
            "environment": '{"test": 1}',
            "environment_secret_keys": "test",
            "command": "some command",
            "containertemplatesite": self.containertemplatesite1,
            "containertemplateproject": None,
        }

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_min_fields_mode_docker_shared(self):
        form = ContainerForm(self.form_data_min_mode_docker_shared)
        self.assertTrue(form.is_valid())

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_min_fields_mode_host(self):
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        form = ContainerForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_repository(self):
        key = "repository"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_tag(self):
        key = "tag"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_container_port(self):
        key = "container_port"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_timeout(self):
        key = "timeout"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_project(self):
        key = "project"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_host_port(self):
        key = "host_port"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_missing_field_title(self):
        key = "title"
        self.form_data_min_mode_host.pop(key)
        form = ContainerForm(self.form_data_min_mode_host)
        self.assertEqual(form.errors[key], ["This field is required."])

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_environment_secret_keys_matching(self):
        self.form_data_all.update(
            {
                "environment": '{"test1": 1, "test2": 2, "test3": 3}',
                "environment_secret_keys": "test1,test3",
            }
        )
        form = ContainerForm(self.form_data_all)
        self.assertTrue(form.is_valid())

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_environment_secret_keys_mismatching(self):
        self.form_data_all.update(
            {
                "environment": '{"test1": 1, "test2": 2, "test3": 3}',
                "environment_secret_keys": "test1,not_an_env_key",
            }
        )
        form = ContainerForm(self.form_data_all)
        self.assertEqual(
            form.errors["environment_secret_keys"],
            ['Secret key "not_an_env_key" is not in environment!'],
        )
