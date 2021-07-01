"""Helpers for the container tests."""
import uuid

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


class TestBase(TestCase):
    """Test base class providing one project and a superuser."""

    def setUp(self):
        super().setUp()

        # Show full diff
        self.maxDiff = None

        # Setup project
        self.project = ProjectFactory()

        # Setup superuser
        self.superuser = self.make_user("superuser")
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

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

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()
