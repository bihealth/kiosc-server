"""Tests for the plugin methods."""

from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from projectroles.plugins import ProjectAppPluginPoint

from containers.models import Container, ContainerBackgroundJob, STATE_RUNNING
from containers.tests.helpers import TestBase
from containers.tests.factories import ContainerFactory


class TestProjectrolesModifyAPI(TestBase):
    """Tests for the methods in ``ProjectModifyPluginMixin``."""

    def setUp(self):
        super().setUp()
        self.create_two_containers()

    @patch('containers.statemachines.ActionSwitch._delete')
    @override_settings(PROJECTROLES_ENABLE_MODIFY_API=True)
    def test_project_delete(self, mock):
        """Test that containers belonging to a project are deleted with it"""
        self.assertEqual(
            Container.objects.filter(project=self.project).count(), 2
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:delete',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                {'delete_host_confirm': 'testserver'},
            )
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            Container.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(
            ContainerBackgroundJob.objects.filter(project=self.project).count(),
            0,
        )
        mock.assert_called()

    @patch('containers.statemachines.ActionSwitch._delete')
    @override_settings(PROJECTROLES_ENABLE_MODIFY_API=False)
    def test_project_delete_disabled(self, mock):
        """Test that containers belonging to a project are NOT deleted"""
        self.assertEqual(
            Container.objects.filter(project=self.project).count(), 2
        )
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    'projectroles:delete',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                {'delete_host_confirm': 'testserver'},
            )
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            Container.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(
            ContainerBackgroundJob.objects.filter(project=self.project).count(),
            0,
        )
        mock.assert_not_called()


class TestPlugin(TestBase):
    def setUp(self):
        super().setUp()
        self.plugin = ProjectAppPluginPoint.get_plugin('containers')
        self.container = ContainerFactory(
            project=self.project,
        )

    def test_project_list_value(self):
        self.container.state = STATE_RUNNING
        self.container.save()
        list_value = self.plugin.get_project_list_value(
            'containers', self.project, self.user
        )
        self.assertEqual(list_value, '1 running')
