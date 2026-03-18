"""Tests for _tui.make_trial_callback."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from openbench._tui import make_trial_callback


class TestMakeTrialCallback:
    def test_returns_callable(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "a", "b", "AgentA", "AgentB", 3)
        assert callable(cb)

    def test_agent_a_advances_task_a(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "task_a_id", "task_b_id", "AgentA", "AgentB", 3)
        cb("AgentA", 0, True, 0.001)
        progress.advance.assert_called_with("task_a_id")

    def test_agent_b_advances_task_b(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "task_a_id", "task_b_id", "AgentA", "AgentB", 3)
        cb("AgentB", 0, True, 0.001)
        progress.advance.assert_called_with("task_b_id")

    def test_unknown_agent_falls_to_b_branch(self) -> None:
        """Any name that is not agent_a_name routes to the B bar."""
        progress = MagicMock()
        cb = make_trial_callback(progress, "a_id", "b_id", "AgentA", "AgentB", 3)
        cb("SomethingElse", 0, True, 0.0)
        progress.advance.assert_called_with("b_id")

    def test_cost_accumulator_sums_across_calls(self) -> None:
        progress = MagicMock()
        cost_acc = [0.0]
        cb = make_trial_callback(progress, "a", "b", "A", "B", 3, cost_accumulator=cost_acc)
        cb("A", 0, True, 0.003)
        cb("B", 0, True, 0.002)
        assert abs(cost_acc[0] - 0.005) < 1e-9

    def test_no_cost_accumulator_no_crash(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "a", "b", "A", "B", 3)
        cb("A", 0, True, 0.001)  # must not raise

    def test_error_icon_included_on_failure(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "a", "b", "A", "B", 3)
        cb("A", 0, False, 0.001)
        call_kwargs = progress.update.call_args[1]
        assert "✗" in call_kwargs["description"]

    def test_no_error_icon_on_success(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "a", "b", "A", "B", 3)
        cb("A", 0, True, 0.001)
        call_kwargs = progress.update.call_args[1]
        assert "✗" not in call_kwargs["description"]

    def test_task_index_shown_in_description(self) -> None:
        progress = MagicMock()
        cb = make_trial_callback(progress, "a", "b", "A", "B", 5)
        cb("A", 2, True, 0.0)
        desc = progress.update.call_args[1]["description"]
        assert "T3/5" in desc  # task_index=2 → "T3/5"

    def test_cost_shown_in_description_when_accumulator_set(self) -> None:
        progress = MagicMock()
        cost_acc = [0.0]
        cb = make_trial_callback(progress, "a", "b", "A", "B", 3, cost_accumulator=cost_acc)
        cb("A", 0, True, 0.0042)
        desc = progress.update.call_args[1]["description"]
        assert "$0.0042" in desc
