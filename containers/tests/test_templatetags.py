"""Tests for the ``templatetags`` module."""

import json

from containers.tests.helpers import TestBase
from timeline.models import TL_STATUS_OK, TL_STATUS_FAILED


from containers.models import (
    STATE_INITIAL,
    STATE_RUNNING,
    STATE_FAILED,
    STATE_EXITED,
    ACTION_START,
    ACTION_STOP,
    ACTION_PAUSE,
    STATE_PULLING,
)
from containers.templatetags.container_tags import (
    colorize_state,
    pretty_json,
    state_bell,
    get_container_events,
    get_container_last_errors,
)


class TestContainerTags(TestBase):
    """Tests for ``container_tags``."""

    def setUp(self):
        super().setUp()
        self.create_one_container()

    def test_colorize_state_initial(self):
        self.assertEqual(colorize_state(STATE_INITIAL), 'text-primary')

    def test_colorize_state_running(self):
        self.assertEqual(colorize_state(STATE_RUNNING), 'text-success')

    def test_colorize_state_failed(self):
        self.assertEqual(colorize_state(STATE_FAILED), 'text-danger')

    def test_colorize_state_exited(self):
        self.assertEqual(colorize_state(STATE_EXITED), 'text-secondary')

    def test_colorize_state_unknown(self):
        self.assertEqual(colorize_state('unknown'), 'text-dark')

    def test_pretty_json_empty(self):
        data = '{}'
        expected = '{}'
        self.assertEqual(pretty_json(json.loads(data)), expected)

    def test_pretty_json_short(self):
        data = '{"key": "value"}'
        expected = """{
    "key": "value"
}"""
        self.assertEqual(pretty_json(json.loads(data)), expected)

    def test_pretty_json_long(self):
        data = '{"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4"}'
        expected = """{
    "key1": "value1",
    "key2": "value2",
    "key3": "value3",
    "key4": "value4"
}"""
        self.assertEqual(pretty_json(json.loads(data)), expected)

    def test_state_bell_no_action(self):
        self.assertEqual(state_bell(STATE_FAILED, None), '')

    def test_state_bell_state_running_action_consistent(self):
        self.assertEqual(state_bell(STATE_RUNNING, ACTION_START), '')

    def test_state_bell_state_running_action_stop(self):
        self.assertEqual(
            state_bell(STATE_RUNNING, ACTION_STOP),
            'Should be running or pulling',
        )

    def test_state_bell_state_running_action_pause(self):
        self.assertEqual(
            state_bell(STATE_RUNNING, ACTION_PAUSE),
            'Should be running or pulling',
        )

    def test_state_bell_state_pulling_action_stop(self):
        self.assertEqual(
            state_bell(STATE_PULLING, ACTION_STOP),
            'Should be running or pulling',
        )

    def test_state_bell_state_pulling_action_pause(self):
        self.assertEqual(
            state_bell(STATE_PULLING, ACTION_PAUSE),
            'Should be running or pulling',
        )

    def test_state_bell_state_exited_action_consistent(self):
        self.assertEqual(state_bell(STATE_EXITED, ACTION_STOP), '')

    def test_state_bell_state_exited_action_start(self):
        self.assertEqual(
            state_bell(STATE_EXITED, ACTION_START),
            'Should be exited',
        )

    def test_get_container_events_empty(self):
        """Test get_container_events() with no events"""
        q = get_container_events(self.container1)
        self.assertEqual(q.count(), 0)

    def test_get_container_events(self):
        """Test get_container_events() with no one event"""
        self.create_container_event(self.container1)
        q = get_container_events(self.container1)
        self.assertEqual(q.count(), 1)

    def test_get_container_last_errors_empty(self):
        """Test get_container_last_errors() with no errors"""
        self.create_container_event(self.container1, status_type=TL_STATUS_OK, user=None)
        res = get_container_last_errors(self.container1)
        self.assertEqual(len(res), 0)

    def test_get_container_last_errors_superuser(self):
        """Test get_container_last_errors() as superuser"""
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.user, event_name='user_event', status_description='desc1')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=None, event_name='anonymous_event', status_description='desc2')
        # The superuser should be able to see both events
        all_events = get_container_events(self.container1).all()
        self.assertEqual(len(all_events), 2)
        res = get_container_last_errors(self.container1, user=self.superuser, limit = 10)
        # The events should be in reverse chronological order
        self.assertEqual(res, ['desc2', 'desc1'])

    def test_get_container_last_errors_user(self):
        """Test get_container_last_errors() as regular user"""
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.superuser, event_name='superuser_event', status_description='desc1')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.user, event_name='user_event', status_description='desc2')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=None, event_name='anonymous_event', status_description='desc3')
        # The regular user should be able to see two events
        all_events = get_container_events(self.container1).all()
        self.assertEqual(len(all_events), 3)
        res = get_container_last_errors(self.container1, user=self.user, limit = 10)
        # The events should be in reverse chronological order
        self.assertEqual(res, ['desc3', 'desc2'])

    def test_get_container_last_errors_anon(self):
        """Test get_container_last_errors() as anonymous"""
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.superuser, event_name='superuser_event', status_description='desc1')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.user, event_name='user_event', status_description='desc2')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=None, event_name='anonymous_event', status_description='desc3')
        # The regular user should be able to see one event
        all_events = get_container_events(self.container1).all()
        self.assertEqual(len(all_events), 3)
        res = get_container_last_errors(self.container1, user=None, limit = 10)
        self.assertEqual(res, ['desc3'])

    def test_get_container_last_errors_break(self):
        """Test get_container_last_errors() breaking at the first success"""
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.superuser, event_name='superuser_event', status_description='desc1')
        self.create_container_event(self.container1, status_type=TL_STATUS_OK, user=self.superuser, event_name='superuser_event', status_description='desc2')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.user, event_name='user_event', status_description='desc3')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=None, event_name='anonymous_event', status_description='desc4')
        # The regular user should be able to see one event
        all_events = get_container_events(self.container1).all()
        self.assertEqual(len(all_events), 4)
        res = get_container_last_errors(self.container1, user=self.superuser, limit = 10)
        self.assertEqual(res, ['desc4', 'desc3'])

    def test_get_container_last_errors_limit(self):
        """Test get_container_last_errors() limit argument"""
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.superuser, event_name='superuser_event', status_description='desc1')
        self.create_container_event(self.container1, status_type=TL_STATUS_OK, user=self.superuser, event_name='superuser_event', status_description='desc2')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=self.user, event_name='user_event', status_description='desc3')
        self.create_container_event(self.container1, status_type=TL_STATUS_FAILED, user=None, event_name='anonymous_event', status_description='desc4')
        # The regular user should be able to see one event
        all_events = get_container_events(self.container1).all()
        self.assertEqual(len(all_events), 4)
        res = get_container_last_errors(self.container1, user=self.superuser, limit = 1)
        self.assertEqual(res, ['desc4'])
