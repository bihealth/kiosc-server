"""Tests for the ``templatetags`` module."""

import json

from test_plus.test import TestCase

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
)


class TestContainerTags(TestCase):
    """Tests for ``container_tags``."""

    def test_colorize_state_initial(self):
        self.assertEqual(colorize_state(STATE_INITIAL), "text-primary")

    def test_colorize_state_running(self):
        self.assertEqual(colorize_state(STATE_RUNNING), "text-success")

    def test_colorize_state_failed(self):
        self.assertEqual(colorize_state(STATE_FAILED), "text-danger")

    def test_colorize_state_exited(self):
        self.assertEqual(colorize_state(STATE_EXITED), "text-secondary")

    def test_colorize_state_unknown(self):
        self.assertEqual(colorize_state("unknown"), "text-dark")

    def test_pretty_json_empty(self):
        data = "{}"
        expected = "{}"
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
        self.assertEqual(state_bell(STATE_FAILED, None), "")

    def test_state_bell_state_running_action_consistent(self):
        self.assertEqual(state_bell(STATE_RUNNING, ACTION_START), "")

    def test_state_bell_state_running_action_stop(self):
        self.assertEqual(
            state_bell(STATE_RUNNING, ACTION_STOP),
            "Should be running or pulling",
        )

    def test_state_bell_state_running_action_pause(self):
        self.assertEqual(
            state_bell(STATE_RUNNING, ACTION_PAUSE),
            "Should be running or pulling",
        )

    def test_state_bell_state_pulling_action_stop(self):
        self.assertEqual(
            state_bell(STATE_PULLING, ACTION_STOP),
            "Should be running or pulling",
        )

    def test_state_bell_state_pulling_action_pause(self):
        self.assertEqual(
            state_bell(STATE_PULLING, ACTION_PAUSE),
            "Should be running or pulling",
        )

    def test_state_bell_state_exited_action_consistent(self):
        self.assertEqual(state_bell(STATE_EXITED, ACTION_STOP), "")

    def test_state_bell_state_exited_action_start(self):
        self.assertEqual(
            state_bell(STATE_EXITED, ACTION_START),
            "Should be exited",
        )
