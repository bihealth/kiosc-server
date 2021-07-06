"""Tests for the ``forms`` module."""

from containertemplates.forms import (
    ContainerTemplateSiteForm,
    ContainerTemplateProjectForm,
    ContainerTemplateProjectToProjectCopyForm,
    ContainerTemplateSiteToProjectCopyForm,
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


class TestContainerTemplateSiteToProjectCopyForm(TestBase):
    """Tests for ``ContainerTemplateSiteToProjectCopyForm``."""

    def setUp(self):
        super().setUp()

        self.create_two_containertemplatesites()
        self.form_data = {
            "source": self.containertemplatesite1.id,
            "site_or_project": "site",
        }

    def test_form_valid(self):
        form = ContainerTemplateSiteToProjectCopyForm(self.form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            list(form.fields["source"].queryset),
            [
                self.containertemplatesite2,
                self.containertemplatesite1,
            ],
        )


class TestContainerTemplateProjectToProjectCopyForm(TestBase):
    """Tests for ``ContainerTemplateProjectToProjectCopyForm``."""

    def setUp(self):
        super().setUp()

        self.create_four_containertemplates_in_two_projects()
        self.assign_user_to_project("contributor", self.project2)
        self.form_data = {
            "source": self.containertemplateproject2_project2.id,
            "site_or_project": "project",
        }

    def test_form_valid_as_contributor(self):
        form = ContainerTemplateProjectToProjectCopyForm(
            self.form_data, user=self.user_contributor
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            list(form.fields["source"].queryset),
            [
                self.containertemplateproject2_project2,
                self.containertemplateproject1_project2,
            ],
        )

    def test_form_valid_as_superuser(self):
        form = ContainerTemplateProjectToProjectCopyForm(
            self.form_data, user=self.superuser
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            list(form.fields["source"].queryset),
            [
                self.containertemplateproject2_project2,
                self.containertemplateproject1_project2,
                self.containertemplateproject2,
                self.containertemplateproject1,
            ],
        )
