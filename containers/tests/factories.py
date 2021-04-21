"""Factories for container tests."""

import factory
from projectroles.constants import SODAR_CONSTANTS
from projectroles.models import Project

from containers.models import Container, STATE_INITIAL


class ProjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating ``projectroles`` ``Project`` objects."""

    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %03d" % n)
    type = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]
    parent = None
    description = factory.Sequence(lambda n: "This is project %03d" % n)


class ContainerFactory(factory.django.DjangoModelFactory):
    """Factory for ``Container`` model."""

    class Meta:
        model = Container

    repository = "repository1"
    tag = "latest"
    project = factory.SubFactory(ProjectFactory)
    image_id = ""
    container_id = ""
    container_port = 80
    container_path = ""
    heartbeat_url = ""
    host_port = factory.Sequence(lambda n: 8000 + n)
    timeout = 60
    timeout_exceeded = True
    state = STATE_INITIAL
    environment = "{}"
    environment_secret_keys = ""
    command = ""
