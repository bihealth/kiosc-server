"""Tests for the ``templatetags`` module."""
from test_plus.plugin import TestCase

from containers.models import (
    STATE_INITIAL,
    STATE_RUNNING,
    STATE_FAILED,
    STATE_EXITED,
)
from containers.templatetags.container_tags import colorize_state


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
