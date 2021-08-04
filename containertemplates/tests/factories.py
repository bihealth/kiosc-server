"""Factories for container tests."""

import factory
from projectroles.constants import SODAR_CONSTANTS
from projectroles.models import Project

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)


class ProjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating ``projectroles`` ``Project`` objects."""

    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %03d" % n)
    type = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]
    parent = None
    description = factory.Sequence(lambda n: "This is project %03d" % n)


class ContainerTemplateFactoryBase(factory.django.DjangoModelFactory):
    """Base factory for ``ContainerTemplate`` model."""

    title = factory.Sequence(lambda n: f"Container Template {n}")
    description = "Some description"
    repository = factory.Sequence(lambda n: f"repository{n}")
    tag = "latest"
    container_port = 80
    container_path = ""
    heartbeat_url = ""
    timeout = 60
    environment = "{}"
    environment_secret_keys = ""
    command = ""
    inactivity_threshold = 7
    max_retries = 5


class ContainerTemplateSiteFactory(ContainerTemplateFactoryBase):
    """Factory for ``ContainerTemplateSite`` model."""

    class Meta:
        model = ContainerTemplateSite


class ContainerTemplateProjectFactory(ContainerTemplateFactoryBase):
    """Factory for ``ContainerTemplateProject`` model."""

    class Meta:
        model = ContainerTemplateProject

    project = factory.SubFactory(ProjectFactory)
