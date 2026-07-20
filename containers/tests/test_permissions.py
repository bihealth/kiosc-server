"""Permission tests."""

from unittest.mock import patch

from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.base import ProjectPermissionTestBase
from urllib3_mock import Responses

from containers.models import STATE_RUNNING
from containers.tests.factories import (
    ContainerFactory,
    ContainerLogEntryFactory,
)
from containers.tests.helpers import TestSearchMixin


PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


responses = Responses('requests.packages.urllib3')


class TestContainerPermissions(ProjectPermissionTestBase):
    """Test permissions for container app."""

    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(project=self.project)

    def test_container_list(self):
        """Test permissions for the ``list`` view."""
        url = reverse(
            'containers:list',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_create(self):
        """Test permissions for the ``create`` view."""
        url = reverse(
            'containers:create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_update(self):
        """Test permissions for the ``update`` view."""
        url = reverse(
            'containers:update',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_detail(self):
        """Test permissions for the ``detail`` view."""
        url = reverse(
            'containers:detail',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_delete(self):
        """Test permissions for the ``delete`` view."""
        url = reverse(
            'containers:delete',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @patch('containers.tasks.container_task.apply_async')
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view."""
        url = reverse(
            'containers:start',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view."""
        url = reverse(
            'containers:stop',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_restart(self, mock):
        """Test permissions for the ``restart`` view."""
        url = reverse(
            'containers:restart',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_pause(self, mock):
        """Test permissions for the ``pause`` view."""
        url = reverse(
            'containers:pause',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_unpause(self, mock):
        """Test permissions for the ``unpause`` view."""
        url = reverse(
            'containers:unpause',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    # urllib3-mock not working with Python 3.11+ :-/
    @responses.activate
    def test_proxy(self):
        """Test permissions for the ``proxy`` view."""

        self.container.state = STATE_RUNNING
        self.container.save()

        def request_callback(request):
            return 200, {}, 'abc'.encode('utf-8')

        responses.add_callback(
            'GET',
            f'/{self.container.container_path}',
            callback=request_callback,
        )
        url = reverse(
            'containers:proxy',
            kwargs={
                'container': self.container.sodar_uuid,
                'path': self.container.container_path,
            },
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


class TestContainerPermissionReadOnly(ProjectPermissionTestBase):
    """Test permissions for container app when site is in read-only mode"""

    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(project=self.project)
        self.set_site_read_only()
        self.good_users = [self.superuser]
        self.bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]

    def test_container_list(self):
        """Test permissions for the ``list`` view in read-only mode."""
        url = reverse(
            'containers:list',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_create(self):
        """Test permissions for the ``create`` view in read-only mode."""
        url = reverse(
            'containers:create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_container_update(self):
        """Test permissions for the ``update`` view in read-only mode."""
        url = reverse(
            'containers:update',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_container_detail(self):
        """Test permissions for the ``detail`` view in read-only mode."""
        url = reverse(
            'containers:detail',
            kwargs={'container': self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_container_delete(self):
        """Test permissions for the ``delete`` view in read-only mode."""
        url = reverse(
            'containers:delete',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    @patch('containers.tasks.container_task.apply_async')
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view in read-only mode."""
        url = reverse(
            'containers:start',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(
            url, self.good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view in read-only mode."""
        url = reverse(
            'containers:stop',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(
            url, self.good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_restart(self, mock):
        """Test permissions for the ``restart`` view in read-only mode."""
        url = reverse(
            'containers:restart',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(
            url, self.good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_pause(self, mock):
        """Test permissions for the ``pause`` view in read-only mode."""
        url = reverse(
            'containers:pause',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(
            url, self.good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch('containers.tasks.container_task.apply_async')
    def test_container_unpause(self, mock):
        """Test permissions for the ``unpause`` view in read-only mode."""
        url = reverse(
            'containers:unpause',
            kwargs={'container': self.container.sodar_uuid},
        )
        self.assert_response(
            url, self.good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    # urllib3-mock not working with Python 3.11+ :-/
    @responses.activate
    def test_proxy(self):
        """Test permissions for the ``proxy`` view in read-only mode."""

        self.container.state = STATE_RUNNING
        self.container.save()

        def request_callback(request):
            return 200, {}, 'abc'.encode('utf-8')

        responses.add_callback(
            'GET',
            f'/{self.container.container_path}',
            callback=request_callback,
        )
        url = reverse(
            'containers:proxy',
            kwargs={
                'container': self.container.sodar_uuid,
                'path': self.container.container_path,
            },
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.anonymous, self.user_finder_cat]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


class TestSearchPermissions(TestSearchMixin, ProjectPermissionTestBase):
    """Test permissions for searching."""

    def setUp(self):
        super().setUp()
        self.other_project = self.make_project(
            'other_project',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='description',
        )
        self.container = ContainerFactory(project=self.project)
        self.other_container = ContainerFactory(project=self.other_project)
        self.logs = ContainerLogEntryFactory(container=self.container)
        self.other_logs = ContainerLogEntryFactory(
            container=self.other_container
        )
        # Promote user to guest
        self.make_assignment(
            self.other_project, self.user_finder_cat, self.role_guest
        )
        self.url = reverse('projectroles:ajax_search')
        self.good_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        self.bad_users = [self.user_viewer, self.user_no_roles]

    def _get_search_results(self, user, data):
        with self.login(user):
            res = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'containers',
                    'keywords': '{}',
                    **data,
                },
            )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNone(data['error'])
        self.assertEqual(data['results'][0]['category'], 'containers')
        self.assertEqual(data['results'][1]['category'], 'logs')
        return data['results'][0]['rows'], data['results'][1]['rows']

    def test_search_term(self):
        """Test permissions for search view."""
        data = {'terms': '["repository", "log"]'}

        # Superuser sees everything
        containers, logs = self._get_search_results(self.superuser, data)
        self.assertEqual(len(containers), 2)
        self.assertEqual(len(logs), 2)

        # Good users see only the container in their project
        for user in self.good_users:
            containers, logs = self._get_search_results(user, data)
            self.assertEqual(len(containers), 1)
            self.assertEqual(len(logs), 1)
            self.assertEqual(
                containers[0][2]['value'],
                f'{self.container.title} ({self.container.repository}:{self.container.tag})',
            )
            self.assertEqual(
                logs[0][2]['value'],
                f'{self.container.title} ({self.container.repository}:{self.container.tag})',
            )
            self.assertTrue(logs[0][3]['value'].startswith('Log entry '))

        # Bad users should not see any results
        for user in self.bad_users:
            containers, logs = self._get_search_results(user, data)
            self.assertEqual(len(containers), 0)
            self.assertEqual(len(logs), 0)

        # Special users
        containers, logs = self._get_search_results(
            self.user_contributor_cat, data
        )
        self.assertEqual(len(containers), 2)
        self.assertEqual(len(logs), 2)

        containers, logs = self._get_search_results(self.user_finder_cat, data)
        self.assertEqual(len(containers), 1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            containers[0][2]['value'],
            f'{self.other_container.title} ({self.other_container.repository}:{self.other_container.tag})',
        )
        self.assertEqual(
            logs[0][2]['value'],
            f'{self.other_container.title} ({self.other_container.repository}:{self.other_container.tag})',
        )
        self.assertTrue(logs[0][3]['value'].startswith('Log entry '))

        # Anonymous
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 403)
