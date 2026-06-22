import json
from typing import Optional

from django import template
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q

from containers.models import (
    Container,
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

from timeline.models import TimelineEvent, TL_STATUS_FAILED, TL_STATUS_OK


register = template.Library()
User = get_user_model()


@register.filter
def colorize_state(state):
    colormap = {
        STATE_INITIAL: 'text-primary',
        STATE_RUNNING: 'text-success',
        STATE_FAILED: 'text-danger',
        STATE_EXITED: 'text-secondary',
    }
    return colormap.get(state, 'text-dark')


@register.simple_tag
def state_bell(state, last_action):
    if last_action is None:
        return ''

    if state in (STATE_RUNNING, STATE_PULLING):
        if last_action not in (ACTION_START, ACTION_UNPAUSE, ACTION_RESTART):
            return 'Should be running or pulling'

    elif state is STATE_EXITED:
        if last_action is not ACTION_STOP:
            return 'Should be exited'

    return ''


@register.simple_tag
def get_container_events(container: Container) -> QuerySet:
    """Return recent events for card on project details page"""
    return TimelineEvent.objects.get_object_events(
        project=container.project,
        object_model='Container',
        object_uuid=container.sodar_uuid,
    )


@register.simple_tag
def get_container_last_errors(
    container: Container, user: Optional[User] = None, limit: int = 1
) -> list[str]:
    """Return the last errors for the project details page"""
    events = get_container_events(container)
    if user and user.is_superuser:
        pass
    elif user:
        events = events.filter(Q(user=None) | Q(user=user))
    else:
        events = events.filter(Q(user=None))
    # We don't want duplicates, but we want to preserve insertion order,
    # so we use a dict
    failures = {}
    for event in events:
        if len(failures) >= limit:
            break
        event_status = event.status_changes.last().status_type
        if event_status == TL_STATUS_OK:
            break
        if event_status == TL_STATUS_FAILED:
            description = event.status_changes.last().description
            if not description:
                description = event.description
            failures[description] = None
    return list(failures)


@register.filter
def get_class(item):
    return item.__class__.__name__


@register.filter
def pretty_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)


@register.inclusion_tag('containers/_container_controls.html')
def container_controls(container, user, display=False):
    return {'container': container, 'user': user, 'display': display}
