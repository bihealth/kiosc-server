"""Permission tests."""
from unittest.mock import patch

from django.urls import reverse
from projectroles.tests.test_permissions import TestProjectPermissionBase
from urllib3_mock import Responses

from containers.tests.factories import ContainerFactory


responses = Responses("requests.packages.urllib3")


class TestContainerPermissions(TestProjectPermissionBase):
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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles, self.anonymous]
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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles, self.anonymous]
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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @patch("containers.tasks.container_task.delay")
    def test_container_start(self, mock):
        """Test permissions for the ``start`` view."""
        url = reverse(
            "containers:start",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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

    @patch("containers.tasks.container_task.delay")
    def test_container_stop(self, mock):
        """Test permissions for the ``stop`` view."""
        url = reverse(
            "containers:stop",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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

    @patch("containers.tasks.container_task.delay")
    def test_container_restart(self, mock):
        """Test permissions for the ``restart`` view."""
        url = reverse(
            "containers:restart",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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

    @patch("containers.tasks.container_task.delay")
    def test_container_pause(self, mock):
        """Test permissions for the ``pause`` view."""
        url = reverse(
            "containers:pause",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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

    @patch("containers.tasks.container_task.delay")
    def test_container_unpause(self, mock):
        """Test permissions for the ``unpause`` view."""
        url = reverse(
            "containers:unpause",
            kwargs={"container": self.container.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
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

    @responses.activate
    def test_proxy(self):
        """Test permissions for the ``proxy`` view."""

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
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @patch("containers.tasks.container_task.delay")
    def test_proxy_lobby(self, mock):
        """Test permissions for the ``proxy-lobby`` view."""

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
                "path": self.container.container_path,
            },
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles, self.anonymous]
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
