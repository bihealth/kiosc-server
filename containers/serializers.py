from django.conf import settings
from projectroles.serializers import SODARProjectModelSerializer

from containers.models import Container


class ContainerSerializer(SODARProjectModelSerializer):
    class Meta:
        model = Container
        fields = (
            "sodar_uuid",
            "date_created",
            "date_modified",
            "project",
            "date_last_status_update",
            "repository",
            "tag",
            "image_id",
            "container_id",
            "container_port",
            "container_path",
            "heartbeat_url",
            "host_port",
            "timeout",
            "state",
            "environment",
            "environment_secret_keys",
            "command",
            "containertemplatesite",
            "containertemplateproject",
            "title",
            "description",
            "inactivity_threshold",
            "max_retries",
        )
        read_only_fields = (
            "sodar_uuid",
            "date_created",
            "date_modified",
            "project",
        )

    def get_extra_kwargs(self):
        # Use this instead of ``extra_kwargs`` because of overriding settings in tests
        extra_kwargs = super().get_extra_kwargs()
        extra_kwargs["host_port"] = {
            "required": settings.KIOSC_NETWORK_MODE == "host"
        }
        return extra_kwargs
