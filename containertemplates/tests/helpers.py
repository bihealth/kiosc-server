"""Helpers for the container tests."""
import uuid

from projectroles.forms import (
    PROJECT_ROLE_OWNER,
    PROJECT_ROLE_DELEGATE,
    PROJECT_ROLE_CONTRIBUTOR,
    PROJECT_ROLE_GUEST,
)
from projectroles.models import Role
from projectroles.tests.test_models import RoleAssignmentMixin
from test_plus.test import TestCase

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)
from containertemplates.tests.factories import (
    ContainerTemplateSiteFactory,
    ContainerTemplateProjectFactory,
    ProjectFactory,
)


class TestBase(RoleAssignmentMixin, TestCase):
    """Test base class providing one project and a superuser."""

    def setUp(self):
        super().setUp()

        # Show full diff
        self.maxDiff = None

        # Setup projects
        self.project = ProjectFactory()
        self.project2 = ProjectFactory()

        # Setup superuser
        self.superuser = self.make_user("superuser")
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

        # Setup users
        self.user_owner = self.make_user("owner")
        self.user_delegate = self.make_user("delegate")
        self.user_contributor = self.make_user("contributor")
        self.user_guest = self.make_user("guest")

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

    def create_one_containertemplatesite(self):
        """Create one containertemplatesite."""
        self.containertemplatesite1 = ContainerTemplateSiteFactory()
        self.assertEqual(ContainerTemplateSite.objects.count(), 1)

    def create_two_containertemplatesites(self):
        """Create two containertemplatesites."""
        self.create_one_containertemplatesite()
        self.containertemplatesite2 = ContainerTemplateSiteFactory()
        self.assertEqual(ContainerTemplateSite.objects.count(), 2)

    def create_one_containertemplateproject(self):
        """Create one containertemplateproject."""
        self.containertemplateproject1 = ContainerTemplateProjectFactory(
            project=self.project
        )
        self.assertEqual(ContainerTemplateProject.objects.count(), 1)

    def create_two_containertemplateprojects(self):
        """Create two containertemplateprojects."""
        self.create_one_containertemplateproject()
        self.containertemplateproject2 = ContainerTemplateProjectFactory(
            project=self.project
        )
        self.assertEqual(ContainerTemplateProject.objects.count(), 2)

    def create_four_containertemplates_in_two_projects(self):
        """Create four containertemplateproject in two projects."""
        self.create_two_containertemplateprojects()
        self.containertemplateproject1_project2 = (
            ContainerTemplateProjectFactory(project=self.project2)
        )
        self.containertemplateproject2_project2 = (
            ContainerTemplateProjectFactory(project=self.project2)
        )
        self.assertEqual(ContainerTemplateProject.objects.count(), 4)

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()

    def assign_user_to_project(self, username, project):
        """Assign user to project."""
        self._make_assignment(
            project,
            getattr(self, f"user_{username}"),
            getattr(self, f"role_{username}"),
        )
