from projectroles.serializers import SODARProjectModelSerializer

from containers.models import Container


class ContainerSerializer(SODARProjectModelSerializer):
    class Meta:
        model = Container
        fields = (
            'sodar_uuid',
            'date_created',
            'date_modified',
            'project',
            'date_last_access',
            'repository',
            'registry_user',
            'registry_password',
            'tag',
            'image_id',
            'container_id',
            'container_ip',
            'container_port',
            'container_path',
            'heartbeat_url',
            'host_port',
            'timeout',
            'state',
            'environment',
            'environment_secret_keys',
            'command',
            'containertemplatesite',
            'containertemplateproject',
            'title',
            'description',
            'inactivity_threshold',
            'max_retries',
        )
        read_only_fields = (
            'sodar_uuid',
            'date_created',
            'date_modified',
            'project',
        )
