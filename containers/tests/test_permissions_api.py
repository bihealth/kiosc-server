"""Permission tests."""
from unittest.mock import patch

from django.urls import reverse

from containers.models import Container
from projectroles.tests.test_permissions_api import TestProjectAPIPermissionBase
from rest_framework import status
from urllib3_mock import Responses

from containers.tests.factories import ContainerFactory
from django.test import override_settings


responses = Responses("requests.packages.urllib3")


class TestContainerAPIPermissions(TestProjectAPIPermissionBase):
    """Test API permissions for container app."""

    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(project=self.project)

    def test_container_list(self):
        """Test permissions for the ``api-list`` view."""
        url = reverse(
            "containers:api-list",
            kwargs={"project": self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.user_finder_cat]

        self.assert_response_api(url, good_users, status.HTTP_200_OK, knox=True)
        self.assert_response_api(
            url, bad_users, status.HTTP_403_FORBIDDEN, knox=True
        )
        self.assert_response_api(
            url, self.anonymous, status.HTTP_401_UNAUTHORIZED
        )

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_container_create(self):
        """Test permissions for the ``api-create`` view."""

        def _cleanup():
            Container.objects.order_by("-pk").first().delete()

        url = reverse(
            "containers:api-create",
            kwargs={"project": self.project.sodar_uuid},
        )
        data = {
            "title": "title",
            "repository": "repository",
            "tag": "tag",
        }
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [self.user_guest, self.user_no_roles, self.user_finder_cat]

        self.assert_response_api(
            url,
            good_users,
            status.HTTP_201_CREATED,
            method="POST",
            data=data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url,
            bad_users,
            status.HTTP_403_FORBIDDEN,
            method="POST",
            data=data,
            knox=True,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            status.HTTP_401_UNAUTHORIZED,
            method="POST",
            data=data,
        )

    def test_container_detail(self):
        """Test permissions for the ``api-detail`` view."""
        url = reverse(
            "containers:api-detail",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_no_roles, self.user_finder_cat]
        self.assert_response_api(url, good_users, status.HTTP_200_OK, knox=True)
        self.assert_response_api(
            url, bad_users, status.HTTP_403_FORBIDDEN, knox=True
        )
        self.assert_response_api(
            url, self.anonymous, status.HTTP_401_UNAUTHORIZED
        )

    def test_container_delete(self):
        """Test permissions for the ``api-delete`` view."""

        uuid = self.container.sodar_uuid

        def _cleanup():
            self.container = ContainerFactory(
                sodar_uuid=uuid, project=self.project
            )

        url = reverse(
            "containers:api-delete",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [self.user_guest, self.user_no_roles, self.user_finder_cat]

        self.assert_response_api(
            url,
            good_users,
            status.HTTP_204_NO_CONTENT,
            method="DELETE",
            cleanup_method=_cleanup,
            knox=True,
        )
        self.assert_response_api(
            url,
            bad_users,
            status.HTTP_403_FORBIDDEN,
            method="DELETE",
            knox=True,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            status.HTTP_401_UNAUTHORIZED,
            method="DELETE",
        )

    @patch("containers.tasks.container_task.apply_async")
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view."""
        url = reverse(
            "containers:api-start",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [self.user_guest, self.user_no_roles, self.user_finder_cat]
        self.assert_response_api(url, good_users, status.HTTP_200_OK, knox=True)
        self.assert_response_api(
            url, bad_users, status.HTTP_403_FORBIDDEN, knox=True
        )
        self.assert_response_api(
            url, self.anonymous, status.HTTP_401_UNAUTHORIZED
        )
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view."""
        url = reverse(
            "containers:api-stop",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [self.user_guest, self.user_no_roles, self.user_finder_cat]
        self.assert_response_api(url, good_users, status.HTTP_200_OK, knox=True)
        self.assert_response_api(
            url, bad_users, status.HTTP_403_FORBIDDEN, knox=True
        )
        self.assert_response_api(
            url, self.anonymous, status.HTTP_401_UNAUTHORIZED
        )
        mock.assert_called()
