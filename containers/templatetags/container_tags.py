import json

from django import template

from containers.models import (
    STATE_FAILED,
    STATE_RUNNING,
    STATE_EXITED,
    STATE_INITIAL,
)


register = template.Library()


@register.filter
def colorize_state(state):
    colormap = {
        STATE_INITIAL: "text-primary",
        STATE_RUNNING: "text-success",
        STATE_FAILED: "text-danger",
        STATE_EXITED: "text-secondary",
    }
    return colormap.get(state, "text-dark")


@register.filter
def pretty_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)
