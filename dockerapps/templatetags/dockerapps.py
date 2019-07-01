from django import template

from ..models import DockerImage

register = template.Library()


@register.simple_tag
def get_details_dockerimages(project):
    """Return docker apps for the project details page"""
    return DockerImage.objects.filter(project=project)[:5]
