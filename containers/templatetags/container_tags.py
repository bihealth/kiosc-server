import json

from django import template

from containers.models import (
    STATE_FAILED,
    STATE_RUNNING,
    STATE_EXITED,
    STATE_INITIAL,
    STATE_PULLING,
    ACTION_STOP,
    ACTION_START,
    ACTION_UNPAUSE,
    ACTION_RESTART,
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


@register.simple_tag
def state_bell(state, last_action):
    if last_action is None:
        return ""

    if state in (STATE_RUNNING, STATE_PULLING):
        if last_action not in (ACTION_START, ACTION_UNPAUSE, ACTION_RESTART):
            return "Should be running or pulling"

    elif state is STATE_EXITED:
        if last_action is not ACTION_STOP:
            return "Should be exited"

    return ""


@register.filter
def pretty_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)
