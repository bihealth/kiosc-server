from django.contrib import admin

from containers.models import (
    Container,
    ContainerBackgroundJob,
    ContainerLogEntry,
)


admin.site.register(Container)
admin.site.register(ContainerBackgroundJob)
admin.site.register(ContainerLogEntry)
