"""Factories for container tests."""

import factory
from bgjobs.tests.factories import BackgroundJobFactory
from projectroles.constants import SODAR_CONSTANTS
from projectroles.models import Project

from containers.models import (
    Container,
    STATE_INITIAL,
    ContainerBackgroundJob,
    ACTION_START,
    ContainerLogEntry,
    LOG_LEVEL_INFO,
    PROCESS_OBJECT,
)


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
    container_id = "abcdefghijklmnopqrstuvwxyz"
    container_port = 80
    container_path = ""
    heartbeat_url = ""
    host_port = factory.Sequence(lambda n: 8000 + n)
    timeout = 60
    state = STATE_INITIAL
    environment = "{}"
    environment_secret_keys = ""
    command = ""


class ContainerBackgroundJobFactory(factory.django.DjangoModelFactory):
    """Factory for ``ContainerBackgroundJob`` model."""

    class Meta:
        model = ContainerBackgroundJob
        exclude = ["user"]

    # Dummy argument ``user`` to pass to subfactory ``BackgroundJobFactory``
    user = None
    project = factory.SubFactory(ProjectFactory)
    container = factory.SubFactory(
        ContainerFactory, project=factory.SelfAttribute("..project")
    )
    action = ACTION_START
    bg_job = factory.SubFactory(
        BackgroundJobFactory,
        project=factory.SelfAttribute("..project"),
        user=factory.SelfAttribute("..user"),
    )


class ContainerLogEntryFactory(factory.django.DjangoModelFactory):
    """Factory for ``ContainerLogEntry`` model."""

    class Meta:
        model = ContainerLogEntry

    level = LOG_LEVEL_INFO
    text = factory.Sequence(lambda n: "Log entry %d" % n)
    container = factory.SubFactory(ContainerFactory)
    process = PROCESS_OBJECT
    date_docker_log = None
    user = None
