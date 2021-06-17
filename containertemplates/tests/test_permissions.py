"""Permission tests."""

from django.urls import reverse
from projectroles.tests.test_permissions import TestProjectPermissionBase

from containertemplates.tests.factories import ContainerTemplateFactory


class TestContainerTemplatePermissions(TestProjectPermissionBase):
    """Test permissions for containertemplates app."""

    def setUp(self):
        super().setUp()
        self.containertemplate = ContainerTemplateFactory(project=self.project)

    def test_containertemplate_list(self):
        """Test permissions for the ``containertemplates:list`` view."""
        url = reverse(
            "containertemplates:list",
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

    def test_containertemplate_create(self):
        """Test permissions for the ``containertemplates:create`` view."""
        url = reverse(
            "containertemplates:create",
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

    def test_containertemplate_update(self):
        """Test permissions for the ``containertemplates:update`` view."""
        url = reverse(
            "containertemplates:update",
            kwargs={"containertemplate": self.containertemplate.sodar_uuid},
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

    def test_containertemplate_detail(self):
        """Test permissions for the ``containertemplates:detail`` view."""
        url = reverse(
            "containertemplates:detail",
            kwargs={"containertemplate": self.containertemplate.sodar_uuid},
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

    def test_containertemplate_delete(self):
        """Test permissions for the ``containertemplates:delete`` view."""
        url = reverse(
            "containertemplates:delete",
            kwargs={"containertemplate": self.containertemplate.sodar_uuid},
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
