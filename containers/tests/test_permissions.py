"""Permission tests."""

from unittest.mock import patch

from django.urls import reverse
from projectroles.tests.base import ProjectPermissionTestBase
from urllib3_mock import Responses

from containers.models import STATE_RUNNING
from containers.tests.factories import ContainerFactory


responses = Responses("requests.packages.urllib3")


class TestContainerPermissions(ProjectPermissionTestBase):
    """Test permissions for container app."""

    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(project=self.project)

    def test_container_list(self):
        """Test permissions for the ``list`` view."""
        url = reverse(
            "containers:list",
            kwargs={"project": self.project.sodar_uuid},
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
            "containers:create",
            kwargs={"project": self.project.sodar_uuid},
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
            "containers:update",
            kwargs={"container": self.container.sodar_uuid},
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
            "containers:detail",
            kwargs={"container": self.container.sodar_uuid},
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
            "containers:delete",
            kwargs={"container": self.container.sodar_uuid},
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

    @patch("containers.tasks.container_task.apply_async")
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view."""
        url = reverse(
            "containers:start",
            kwargs={"container": self.container.sodar_uuid},
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
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view."""
        url = reverse(
            "containers:stop",
            kwargs={"container": self.container.sodar_uuid},
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
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_restart(self, mock):
        """Test permissions for the ``restart`` view."""
        url = reverse(
            "containers:restart",
            kwargs={"container": self.container.sodar_uuid},
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
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_pause(self, mock):
        """Test permissions for the ``pause`` view."""
        url = reverse(
            "containers:pause",
            kwargs={"container": self.container.sodar_uuid},
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
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_unpause(self, mock):
        """Test permissions for the ``unpause`` view."""
        url = reverse(
            "containers:unpause",
            kwargs={"container": self.container.sodar_uuid},
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
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
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
            return 200, {}, "abc".encode("utf-8")

        responses.add_callback(
            "GET",
            f"/{self.container.container_path}",
            callback=request_callback,
        )
        url = reverse(
            "containers:proxy",
            kwargs={
                "container": self.container.sodar_uuid,
                "path": self.container.container_path,
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

    def test_proxy_lobby(self):
        """Test permissions for the ``proxy-lobby`` view."""

        self.container.state = STATE_RUNNING
        self.container.save()

        def request_callback(request):
            return 200, {}, "abc".encode("utf-8")

        responses.add_callback(
            "GET",
            f"/{self.container.container_path}",
            callback=request_callback,
        )
        url = reverse(
            "containers:proxy-lobby",
            kwargs={
                "container": self.container.sodar_uuid,
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
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:proxy",
                kwargs={
                    "container": self.container.sodar_uuid,
                    "path": self.container.container_path,
                },
            ),
        )
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
            "containers:list",
            kwargs={"project": self.project.sodar_uuid},
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
            "containers:create",
            kwargs={"project": self.project.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_container_update(self):
        """Test permissions for the ``update`` view in read-only mode."""
        url = reverse(
            "containers:update",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_container_detail(self):
        """Test permissions for the ``detail`` view in read-only mode."""
        url = reverse(
            "containers:detail",
            kwargs={"container": self.container.sodar_uuid},
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
            "containers:delete",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    @patch("containers.tasks.container_task.apply_async")
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view in read-only mode."""
        url = reverse(
            "containers:start",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view in read-only mode."""
        url = reverse(
            "containers:stop",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_restart(self, mock):
        """Test permissions for the ``restart`` view in read-only mode."""
        url = reverse(
            "containers:restart",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_pause(self, mock):
        """Test permissions for the ``pause`` view in read-only mode."""
        url = reverse(
            "containers:pause",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
        )
        self.assert_response(url, self.bad_users, 302)
        mock.assert_called()

    @patch("containers.tasks.container_task.apply_async")
    def test_container_unpause(self, mock):
        """Test permissions for the ``unpause`` view in read-only mode."""
        url = reverse(
            "containers:unpause",
            kwargs={"container": self.container.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containers:detail",
                kwargs={"container": self.container.sodar_uuid},
            ),
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
            return 200, {}, "abc".encode("utf-8")

        responses.add_callback(
            "GET",
            f"/{self.container.container_path}",
            callback=request_callback,
        )
        url = reverse(
            "containers:proxy",
            kwargs={
                "container": self.container.sodar_uuid,
                "path": self.container.container_path,
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

    def test_proxy_lobby(self):
        """Test permissions for the ``proxy-lobby`` view in read-only mode."""

        self.container.state = STATE_RUNNING
        self.container.save()

        def request_callback(request):
            return 200, {}, "abc".encode("utf-8")

        responses.add_callback(
            "GET",
            f"/{self.container.container_path}",
            callback=request_callback,
        )
        url = reverse(
            "containers:proxy-lobby",
            kwargs={
                "container": self.container.sodar_uuid,
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
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containers:proxy",
                kwargs={
                    "container": self.container.sodar_uuid,
                    "path": self.container.container_path,
                },
            ),
        )
        self.assert_response(url, bad_users, 302)
