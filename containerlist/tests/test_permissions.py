"""Permission tests for the containerlist app."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.base import ProjectPermissionTestBase
from urllib3_mock import Responses

from containers.models import STATE_RUNNING
from containers.tests.factories import ContainerFactory


responses = Responses('requests.packages.urllib3')
User = get_user_model()


PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestContainerSiteListPermissions(ProjectPermissionTestBase):
    """Test permissions for container app."""

    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(project=self.project)
        self.user_owner2 = self.make_user('user_owner2')
        self.project2 = self.make_project('project2', PROJECT_TYPE_PROJECT, self.category)
        self.owner_as2 = self.make_assignment(self.project2, self.user_owner2, self.role_owner)
        self.container2 = ContainerFactory(project=self.project2)
        self.url = reverse('containerlist:overview')

    def _check_container_list_items(self, user: User, expected_items: list | set):
        with self.login(user):
            response = self.send_request(self.url, 'GET', {})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.context['object_list']), set(expected_items))

    def test_container_list_access(self):
        """Test access permissions for the ``list`` view."""
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.user_finder_cat,
        ]
        bad_users = [self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    def test_container_list_users(self):
        """Test individual container permissions for the ``list`` view."""
        self._check_container_list_items(self.superuser, [self.container, self.container2])
        self._check_container_list_items(self.user_owner, [self.container])
        self._check_container_list_items(self.user_owner, [self.container])
        self._check_container_list_items(self.user_owner2, [self.container2])

    def test_container_list_users_read_only(self):
        """Test individual container permissions for the ``list`` view in RO mode."""
        self.set_site_read_only()
        self._check_container_list_items(self.superuser, [self.container, self.container2])
        self._check_container_list_items(self.user_owner, [self.container])
        self._check_container_list_items(self.user_owner, [self.container])
        self._check_container_list_items(self.user_owner2, [self.container2])
        self.assert_response(self.url, self.anonymous, 302)
