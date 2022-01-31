import sys

import docker.errors

from django.apps import AppConfig
from django.conf import settings


class ContainersConfig(AppConfig):
    name = "containers"

    def ready(self):
        if (
            sys.argv[0].endswith(("daphne", "gunicorn", "uvicorn"))
            and settings.KIOSC_NETWORK_MODE == "docker-shared"
        ):
            from containers.statemachines import connect_docker

            cli = connect_docker()

            try:
                network = cli.create_network(
                    settings.KIOSC_DOCKER_NETWORK,
                    driver="bridge",
                    check_duplicate=True,
                )

            except docker.errors.APIError as e:
                if e.response.status_code == 409:
                    networks = cli.networks(
                        filters={"name": settings.KIOSC_DOCKER_NETWORK}
                    )

                    if len(networks) == 0:
                        raise Exception("No networks found")

                    elif len(networks) > 1:
                        raise Exception(
                            f"Multiple networks found ({len(networks)})"
                        )

                    network = networks[0]

                else:
                    raise e

            network_id = network.get("Id")

            if not network_id:
                raise Exception("Network found, but has no ID")

            containers = cli.containers(
                filters={"name": settings.KIOSC_DOCKER_WEB_SERVER}
            )

            if len(containers) == 0:
                raise Exception("No web server container found")

            elif len(containers) > 1:
                raise Exception(
                    f"Multiple web server container found ({len(containers)})"
                )

            container_id = containers[0].get("Id")

            if not container_id:
                raise Exception("Container found, but has no ID")

            try:
                cli.connect_container_to_network(
                    container_id,
                    network_id,
                    aliases=[settings.KIOSC_DOCKER_WEB_SERVER],
                )

            except docker.errors.APIError as e:
                if e.response.status_code == 403:
                    # Container is already in network
                    pass
