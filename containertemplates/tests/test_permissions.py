"""Permission tests."""

from django.urls import reverse
from projectroles.tests.base import ProjectPermissionTestBase

from containertemplates.tests.factories import (
    ContainerTemplateSiteFactory,
    ContainerTemplateProjectFactory,
)


class TestContainerTemplateSitePermissions(ProjectPermissionTestBase):
    """Test permissions for site-wide containertemplates app."""

    def setUp(self):
        super().setUp()
        self.containertemplatesite = ContainerTemplateSiteFactory()

    def test_containertemplatesite_list(self):
        """Test permissions for the ``containertemplates:site-list`` view."""
        url = reverse(
            "containertemplates:site-list",
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_containertemplatesite_create(self):
        """Test permissions for the ``containertemplates:site-create`` view."""
        url = reverse(
            "containertemplates:site-create",
        )
        good_users = [
            self.superuser,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_containertemplatesite_update(self):
        """Test permissions for the ``containertemplates:site-update`` view."""
        url = reverse(
            "containertemplates:site-update",
            kwargs={
                "containertemplatesite": self.containertemplatesite.sodar_uuid
            },
        )
        good_users = [
            self.superuser,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_containertemplatesite_detail(self):
        """Test permissions for the ``containertemplates:site-detail`` view."""
        url = reverse(
            "containertemplates:site-detail",
            kwargs={
                "containertemplatesite": self.containertemplatesite.sodar_uuid
            },
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_containertemplatesite_delete(self):
        """Test permissions for the ``containertemplates:site-delete`` view."""
        url = reverse(
            "containertemplates:site-delete",
            kwargs={
                "containertemplatesite": self.containertemplatesite.sodar_uuid
            },
        )
        good_users = [
            self.superuser,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
            self.user_finder_cat,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_containertemplatesite_duplicate(self):
        """Test permissions for the ``containertemplates:site-duplicate`` view."""
        url = reverse(
            "containertemplates:site-duplicate",
            kwargs={
                "containertemplatesite": self.containertemplatesite.sodar_uuid
            },
        )
        good_users = [
            self.superuser,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
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
                "containertemplates:site-list",
            ),
        )
        self.assert_response(url, bad_users, 302)


class TestContainerTemplateProjectPermissions(ProjectPermissionTestBase):
    """Test permissions for project-wide containertemplates app."""

    def setUp(self):
        super().setUp()
        self.containertemplateproject = ContainerTemplateProjectFactory(
            project=self.project
        )

    def test_containertemplateproject_list(self):
        """Test permissions for the ``containertemplates:project-list`` view."""
        url = reverse(
            "containertemplates:project-list",
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

    def test_containertemplateproject_create(self):
        """Test permissions for the ``containertemplates:project-create`` view."""
        url = reverse(
            "containertemplates:project-create",
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

    def test_containertemplateproject_update(self):
        """Test permissions for the ``containertemplates:project-update`` view."""
        url = reverse(
            "containertemplates:project-update",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
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

    def test_containertemplateproject_detail(self):
        """Test permissions for the ``containertemplates:project-detail`` view."""
        url = reverse(
            "containertemplates:project-detail",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
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

    def test_containertemplateproject_delete(self):
        """Test permissions for the ``containertemplates:project-delete`` view."""
        url = reverse(
            "containertemplates:project-delete",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
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

    def test_containertemplateproject_duplicate(self):
        """Test permissions for the ``containertemplates:project-duplicate`` view."""
        url = reverse(
            "containertemplates:project-duplicate",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
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
                "containertemplates:project-list",
                kwargs={"project": self.project.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)

    def test_containertemplateproject_copy(self):
        """Test permissions for the ``containertemplates:project-copy`` view."""
        url = reverse(
            "containertemplates:project-copy",
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
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user=reverse(
                "containertemplates:project-list",
                kwargs={"project": self.project.sodar_uuid},
            ),
            method="POST",
        )
        self.assert_response(url, bad_users, 302, method="POST")

    def test_containertemplate_ajax_get(self):
        """Test permissions for the ``containertemplates:ajax-get-containertemplate`` view."""
        url = reverse(
            "containertemplates:ajax-get-containertemplate",
        )
        containertemplate = ContainerTemplateSiteFactory()
        data = {
            "containertemplate_id": containertemplate.id,
            "site_or_project": "site",
        }
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
        self.assert_response(url, good_users, 200, method="POST", data=data)
        self.assert_response(url, bad_users, 302, method="POST", data=data)


class TestContainerTemplateProjectPermissionsReadOnly(
    ProjectPermissionTestBase
):
    """Test permissions for project-wide containertemplates app when site is in read-only mode."""

    def setUp(self):
        super().setUp()
        self.containertemplateproject = ContainerTemplateProjectFactory(
            project=self.project
        )
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

    def test_containertemplateproject_list(self):
        """Test permissions for the ``containertemplates:project-list`` view."""
        url = reverse(
            "containertemplates:project-list",
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

    def test_containertemplateproject_create(self):
        """Test permissions for the ``containertemplates:project-create`` view."""
        url = reverse(
            "containertemplates:project-create",
            kwargs={"project": self.project.sodar_uuid},
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_containertemplateproject_update(self):
        """Test permissions for the ``containertemplates:project-update`` view."""
        url = reverse(
            "containertemplates:project-update",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_containertemplateproject_detail(self):
        """Test permissions for the ``containertemplates:project-detail`` view."""
        url = reverse(
            "containertemplates:project-detail",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
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

    def test_containertemplateproject_delete(self):
        """Test permissions for the ``containertemplates:project-delete`` view."""
        url = reverse(
            "containertemplates:project-delete",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
        )
        self.assert_response(url, self.good_users, 200)
        self.assert_response(url, self.bad_users, 302)

    def test_containertemplateproject_duplicate(self):
        """Test permissions for the ``containertemplates:project-duplicate`` view."""
        url = reverse(
            "containertemplates:project-duplicate",
            kwargs={
                "containertemplateproject": self.containertemplateproject.sodar_uuid
            },
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containertemplates:project-list",
                kwargs={"project": self.project.sodar_uuid},
            ),
        )
        self.assert_response(url, self.bad_users, 302)

    def test_containertemplateproject_copy(self):
        """Test permissions for the ``containertemplates:project-copy`` view."""
        url = reverse(
            "containertemplates:project-copy",
            kwargs={"project": self.project.sodar_uuid},
        )
        self.assert_response(
            url,
            self.good_users,
            302,
            redirect_user=reverse(
                "containertemplates:project-list",
                kwargs={"project": self.project.sodar_uuid},
            ),
            method="POST",
        )
        self.assert_response(url, self.bad_users, 302, method="POST")

    def test_containertemplate_ajax_get(self):
        """Test permissions for the ``containertemplates:ajax-get-containertemplate`` view."""
        url = reverse(
            "containertemplates:ajax-get-containertemplate",
        )
        containertemplate = ContainerTemplateSiteFactory()
        data = {
            "containertemplate_id": containertemplate.id,
            "site_or_project": "site",
        }
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
        self.assert_response(url, good_users, 200, method="POST", data=data)
        self.assert_response(url, bad_users, 302, method="POST", data=data)
