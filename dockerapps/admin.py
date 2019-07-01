from django.contrib import admin

from .models import DockerImage, DockerProcess

# Register your models here.
admin.site.register(DockerImage)
admin.site.register(DockerProcess)
