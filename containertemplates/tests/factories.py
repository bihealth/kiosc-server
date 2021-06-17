"""Factories for container tests."""

import factory
from projectroles.constants import SODAR_CONSTANTS
from projectroles.models import Project

from containertemplates.models import ContainerTemplate


class ProjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating ``projectroles`` ``Project`` objects."""

    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %03d" % n)
    type = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]
    parent = None
    description = factory.Sequence(lambda n: "This is project %03d" % n)


class ContainerTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for ``ContainerTemplate`` model."""

    class Meta:
        model = ContainerTemplate

    title = factory.Sequence(lambda n: f"Container Template {n}")
    description = "Some description"
    repository = factory.Sequence(lambda n: f"repository{n}")
    tag = "latest"
    project = factory.SubFactory(ProjectFactory)
    container_port = 80
    container_path = ""
    heartbeat_url = ""
    timeout = 60
    environment = "{}"
    environment_secret_keys = ""
    command = ""
