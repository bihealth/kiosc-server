from django.contrib import admin

from containertemplates.models import (
    ContainerTemplateProject,
    ContainerTemplateSite,
)


admin.site.register(ContainerTemplateProject)
admin.site.register(ContainerTemplateSite)
