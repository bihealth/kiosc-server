"""Factories for container tests."""

import factory

from containertemplates.models import ContainerTemplate


class ContainerTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for ``ContainerTemplate`` model."""

    class Meta:
        model = ContainerTemplate

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
