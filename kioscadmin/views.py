from django.views.generic import ListView

from containers.models import Container
from containers.statemachines import connect_docker
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
)


APP_NAME = "kioscadmin"


class KioscAdminView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ListView,
):
    """View for Kiosc admin."""

    permission_required = "kioscadmin.admin"
    template_name = "kioscadmin/kioscadmin.html"
    model = Container

    def _get_not_in_kiosc(self, cli):
        not_in_kiosc = []

        for container in cli.containers():
            container_id = container.get("Id")

            if container_id:
                try:
                    Container.objects.get(container_id=container_id)

                except Container.DoesNotExist:
                    not_in_kiosc.append(
                        {
                            "id": container_id,
                            "name": container.get("Names", [""])[0].lstrip("/"),
                            "image": container.get("Image"),
                        }
                    )

        return not_in_kiosc

    def _get_networks(self, cli):
        networks = []

        for network in cli.networks():
            net_id = network.get("Id", "")

            if net_id:
                net_info = cli.inspect_network(net_id)

            else:
                net_info = network

            netconf = net_info.get("IPAM", {}).get("Config")
            containers = []

            for container_id, container_info in net_info.get(
                "Containers", {}
            ).items():
                container_name = container_info.get("Name")
                container_ip = container_info.get("IPv4Address")
                containers.append(
                    {
                        "name": container_name,
                        "id": container_id,
                        "ip": container_ip,
                    }
                )

            networks.append(
                {
                    "name": net_info.get("Name", ""),
                    "id": net_id,
                    "driver": net_info.get("Driver", ""),
                    "containers": containers,
                    "subnet": netconf[0].get("Subnet", "") if netconf else "",
                    "gateway": netconf[0].get("Gateway", "") if netconf else "",
                }
            )

        return networks

    def _get_images(self, cli):
        images = []

        for image in cli.images():
            repotags = image.get("RepoTags")
            images.append(
                {
                    "id": image.get("Id"),
                    "repos": repotags[0] if repotags else "",
                }
            )

        return images

    def _get_volumes(self, cli):
        volumes = []

        for volume in cli.volumes().get("Volumes", []):
            volumes.append(
                {
                    "name": volume.get("Name"),
                    "mountpoint": volume.get("Mountpoint"),
                }
            )

        return volumes

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        cli = connect_docker()

        context["not_in_kiosc"] = self._get_not_in_kiosc(cli)
        context["networks"] = self._get_networks(cli)
        context["images"] = self._get_images(cli)
        context["volumes"] = self._get_volumes(cli)

        return context
