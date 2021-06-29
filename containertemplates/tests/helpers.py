"""Helpers for the container tests."""
import uuid

from test_plus.test import TestCase

from containertemplates.models import ContainerTemplate
from containertemplates.tests.factories import ContainerTemplateFactory


class TestBase(TestCase):
    """Test base class providing one project and a superuser."""

    def setUp(self):
        super().setUp()

        # Show full diff
        self.maxDiff = None

        # Setup superuser
        self.superuser = self.make_user("superuser")
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

    def create_one_containertemplate(self):
        """Create one containertemplate."""
        self.containertemplate1 = ContainerTemplateFactory()
        self.assertEqual(ContainerTemplate.objects.count(), 1)

    def create_two_containertemplates(self):
        """Create two containertemplates."""
        self.create_one_containertemplate()
        self.containertemplate2 = ContainerTemplateFactory()
        self.assertEqual(ContainerTemplate.objects.count(), 2)

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()
