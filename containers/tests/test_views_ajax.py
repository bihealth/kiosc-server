"""Tests for Ajax API views in the containers app"""

import time


from test_plus.test import TestCase

from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.base import LiveUserMixin
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from containers.models import ACTION_START, STATE_RUNNING, ContainerLogEntry
from containers.statemachines import connect_docker
from containers.tasks import container_task
from containers.tests.helpers import TestSearchMixin, build_testdata_container
from containers.tests.factories import (
    ContainerFactory,
    ContainerBackgroundJobFactory,
    ContainerLogEntryFactory,
)

from containertemplates.tests.factories import (
    ContainerTemplateSiteFactory,
    ContainerTemplateProjectFactory,
)


PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestPluginSearchResultsAjaxView(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    LiveUserMixin,
    TestSearchMixin,
    TestCase,
):
    """Tests for PluginSearchResultsAjaxView view with containers and logs"""

    def setUp(self):
        super().setUp()
        self.init_roles()
        self.superuser = self.make_user('superuser', superuser=True)
        self.user_owner_cat = self.make_user('owner')
        self.user_contributor1 = self.make_user('contributor')
        self.category = self.make_project(
            'Test Category',
            PROJECT_TYPE_CATEGORY,
            None,
            description='category description',
        )
        self.project1 = self.make_project(
            'Project 1',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='description',
        )
        self.project2 = self.make_project(
            'Project 2',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='description',
        )
        self.container1 = ContainerFactory(
            project=self.project1, description='description 1'
        )
        self.container2 = ContainerFactory(
            project=self.project2, description='description 2'
        )
        self.templatesite = ContainerTemplateSiteFactory()
        self.templateproject1 = ContainerTemplateProjectFactory(
            project=self.project1
        )
        self.logs1 = ContainerLogEntryFactory(
            container=self.container1, text='Log entry 0 for test container 0'
        )
        self.logs2 = ContainerLogEntryFactory(
            container=self.container2, text='Log entry 0 for test container 1'
        )
        # Assign roles
        self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.make_assignment(
            self.project1, self.user_contributor1, self.role_contributor
        )

    def test_search(self):
        """Test simple search"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["description 1"]',
                'keywords': '{}',
            },
        )
        self.assertEqual(len(containers), 1)
        self.assertEqual(len(logs), 0)
        self.assertTrue(self.container1.title in containers[0][2]['value'])

    def test_search_type_container(self):
        """Test simple search with container type"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["container"]',
                'keywords': '{"type": "container"}',
            },
        )
        self.assertEqual(len(containers), 2)
        self.assertEqual(len(logs), 0)
        self.assertTrue(self.container1.title in containers[0][2]['value'])
        self.assertTrue(self.container2.title in containers[1][2]['value'])

    def test_search_type_containertemplate(self):
        """Test simple search with containertemplate type"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["container"]',
                'keywords': '{"type": "containertemplate"}',
            },
        )
        self.assertEqual(len(containers), 2)
        self.assertEqual(len(logs), 0)
        self.assertTrue(
            self.templateproject1.title in containers[0][2]['value']
        )
        self.assertTrue(self.templatesite.title in containers[1][2]['value'])

    def test_search_type_logs(self):
        """Test simple search with containerlogentry type"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["container"]',
                'keywords': '{"type": "containerlogentry"}',
            },
        )
        self.assertEqual(len(containers), 0)
        self.assertEqual(len(logs), 2)
        self.assertEqual(
            'Log entry 0 for test container 0', logs[0][3]['value']
        )
        self.assertEqual(
            'Log entry 0 for test container 1', logs[1][3]['value']
        )

    def test_search_in_project2(self):
        """Test search limited to project2"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["container"]',
                'keywords': f'{{"project": "{self.project2.sodar_uuid}"}}',
            },
        )
        self.assertEqual(len(containers), 2)
        self.assertEqual(len(logs), 1)
        self.assertTrue(self.container2.title in containers[0][2]['value'])
        self.assertTrue(self.templatesite.title in containers[1][2]['value'])

    def test_search_multi(self):
        """Test search with multiple terms"""
        containers, logs = self._get_search_results(
            self.user_owner_cat,
            {
                'terms': '["container", "log"]',
                'keywords': '{}',
            },
        )
        self.assertEqual(len(containers), 4)
        self.assertEqual(len(logs), 2)

    def test_search_for_user_contributor(self):
        """Test permissions for search view limited by type."""
        containers, logs = self._get_search_results(
            self.user_contributor1,
            {
                'terms': '["container", "log"]',
                'keywords': '{}',
            },
        )
        self.assertEqual(len(containers), 3)
        self.assertEqual(len(logs), 1)

    def test_search_daemon_logs(self):
        """Test permissions for search view limited by type and project."""
        cli = connect_docker()
        build_testdata_container(cli, 'sample-app-server')
        container = ContainerFactory(
            project=self.project1,
            repository='sample-app-server',
            tag='testing',
            host_port=0,
            container_id=None,
        )
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn('Container started successfully\n', logs)
        # Test from the daemon
        for c in cli.containers():
            if c['Id'] == container.container_id:
                self.assertEqual(c['State'], STATE_RUNNING)
                break
        else:
            raise RuntimeError('Container is not running')
        # Wait for logs to accumulate, then search
        time.sleep(3)
        containers, logs = self._get_search_results(
            self.superuser,
            {
                'terms': '["nginx"]',
                'keywords': '{}',
            },
        )
        self.assertEqual(len(containers), 0)
        self.assertEqual(len(logs), 3)
        self.assertIn(
            'Getting the checksum of /etc/nginx/conf.d/default.conf',
            logs[0][3]['value'],
        )
        # Getting the checksum of /etc/nginx/conf.d/default.conf
        cli.remove_container(container.container_id, force=True, v=True)
