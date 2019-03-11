from django import template

from ..models import DockerApp

register = template.Library()


@register.simple_tag
def get_details_dockerapps(project):
    """Return docker apps for the project details page"""
    return DockerApp.objects.filter(project=project)[:5]
