"""Tests for the ``forms`` module."""

from containertemplates.forms import (
    ContainerTemplateSiteForm,
    ContainerTemplateProjectForm,
    ContainerTemplateSelectorForm,
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
            "inactivity_threshold": 20,
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
    """Tests for ``ContainerTemplateProjectForm``."""

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
            "inactivity_threshold": 20,
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


class TestContainerTemplateSelectorForm(TestBase):
    """Tests for ``ContainerTemplateSelectorForm``."""

    def setUp(self):
        super().setUp()

        self.create_two_containertemplatesites()
        self.create_four_containertemplates_in_two_projects()
        self.assign_user_to_project("contributor", self.project2)
        self.form_data_site = {
            "source": f"site:{self.containertemplatesite1.id}",
        }
        self.form_data_project = {
            "source": f"project:{self.containertemplateproject2_project2.id}",
        }

    def test_form_valid_site_as_contributor(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_site, user=self.user_contributor
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_project_as_contributor(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_project, user=self.user_contributor
        )
        self.assertTrue(form.is_valid())

    def test_form_choices_as_contributor(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_project, user=self.user_contributor
        )
        self.assertListEqual(
            form.fields["source"].choices,
            [
                (
                    f"site:{self.containertemplatesite2.id}",
                    f"[Site-wide] {self.containertemplatesite2.get_display_name()}",
                ),
                (
                    f"site:{self.containertemplatesite1.id}",
                    f"[Site-wide] {self.containertemplatesite1.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject2_project2.id}",
                    f"[Project-wide] {self.containertemplateproject2_project2.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject1_project2.id}",
                    f"[Project-wide] {self.containertemplateproject1_project2.get_display_name()}",
                ),
            ],
        )

    def test_form_valid_site_as_superuser(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_site, user=self.superuser
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_project_as_superuser(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_project, user=self.superuser
        )
        self.assertTrue(form.is_valid())

    def test_form_choices_as_superuser(self):
        form = ContainerTemplateSelectorForm(
            self.form_data_project, user=self.superuser
        )
        self.assertListEqual(
            form.fields["source"].choices,
            [
                (
                    f"site:{self.containertemplatesite2.id}",
                    f"[Site-wide] {self.containertemplatesite2.get_display_name()}",
                ),
                (
                    f"site:{self.containertemplatesite1.id}",
                    f"[Site-wide] {self.containertemplatesite1.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject2_project2.id}",
                    f"[Project-wide] {self.containertemplateproject2_project2.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject1_project2.id}",
                    f"[Project-wide] {self.containertemplateproject1_project2.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject2.id}",
                    f"[Project-wide] {self.containertemplateproject2.get_display_name()}",
                ),
                (
                    f"project:{self.containertemplateproject1.id}",
                    f"[Project-wide] {self.containertemplateproject1.get_display_name()}",
                ),
            ],
        )
