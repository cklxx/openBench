"""Tests for ExperimentPlanner._critique_and_revise."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from openbench.planner import ExperimentPlanner
from openbench.program import ResearchProgram


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _program() -> ResearchProgram:
    return ResearchProgram.from_natural_language(
        "Find the best system prompt",
        domain="general",
        optimization_targets=["quality"],
        constraints={"model": "claude-haiku-4-5", "max_turns": 3, "allowed_tools": []},
    )


def _plan() -> dict:
    return {
        "experiment_name": "test_exp",
        "description": "test",
        "hypothesis": "B is better",
        "diff_field": "system_prompt",
        "diff_description": "none vs with prompt",
        "agent_a": {
            "name": "baseline",
            "system_prompt": None,
            "allowed_tools": [],
            "max_turns": 3,
        },
        "agent_b": {
            "name": "variant",
            "system_prompt": "Be helpful",
            "allowed_tools": [],
            "max_turns": 3,
        },
        "tasks": ["task 1", "task 2", "task 3"],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCritiqueAndRevise:
    def _planner(self) -> ExperimentPlanner:
        return ExperimentPlanner()

    def test_no_revision_returns_original_object(self) -> None:
        planner = self._planner()
        program = _program()
        plan = _plan()
        critique_response = {"issues": [], "needs_revision": False}

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, program)

        assert result is plan  # same object — no copy made

    def test_revision_applies_agent_a_prompt(self) -> None:
        planner = self._planner()
        plan = _plan()
        critique_response = {
            "issues": ["A prompt is empty"],
            "needs_revision": True,
            "revised_agent_a_system_prompt": "Be concise",
            "revised_agent_b_system_prompt": None,
            "revised_tasks": None,
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        assert result["agent_a"]["system_prompt"] == "Be concise"
        assert result["agent_b"]["system_prompt"] == "Be helpful"  # unchanged

    def test_revision_applies_agent_b_prompt(self) -> None:
        planner = self._planner()
        plan = _plan()
        critique_response = {
            "issues": ["B is biased"],
            "needs_revision": True,
            "revised_agent_a_system_prompt": None,
            "revised_agent_b_system_prompt": "Be more neutral",
            "revised_tasks": None,
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        assert result["agent_b"]["system_prompt"] == "Be more neutral"
        assert result["agent_a"]["system_prompt"] is None  # unchanged

    def test_revision_applies_tasks(self) -> None:
        planner = self._planner()
        plan = _plan()
        new_tasks = ["new 1", "new 2", "new 3"]
        critique_response = {
            "issues": ["Tasks are imbalanced"],
            "needs_revision": True,
            "revised_agent_a_system_prompt": None,
            "revised_agent_b_system_prompt": None,
            "revised_tasks": new_tasks,
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        assert result["tasks"] == new_tasks

    def test_null_revised_tasks_not_applied(self) -> None:
        planner = self._planner()
        plan = _plan()
        original_tasks = plan["tasks"][:]
        critique_response = {
            "issues": [],
            "needs_revision": True,
            "revised_agent_a_system_prompt": None,
            "revised_agent_b_system_prompt": "revised",
            "revised_tasks": None,
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        assert result["tasks"] == original_tasks

    def test_empty_revised_tasks_not_applied(self) -> None:
        """An empty list must not silently clear the task list."""
        planner = self._planner()
        plan = _plan()
        original_tasks = plan["tasks"][:]
        critique_response = {
            "issues": [],
            "needs_revision": True,
            "revised_agent_a_system_prompt": None,
            "revised_agent_b_system_prompt": None,
            "revised_tasks": [],
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        assert result["tasks"] == original_tasks

    def test_original_plan_not_mutated(self) -> None:
        """Revision must return a copy, not mutate the original plan dict."""
        planner = self._planner()
        plan = _plan()
        critique_response = {
            "issues": ["A is bad"],
            "needs_revision": True,
            "revised_agent_a_system_prompt": "New prompt",
            "revised_agent_b_system_prompt": None,
            "revised_tasks": None,
        }

        with patch.object(planner, "_call", return_value=critique_response):
            result = planner._critique_and_revise(plan, _program())

        # Original plan's agent_a should be unchanged
        assert plan["agent_a"]["system_prompt"] is None
        assert result["agent_a"]["system_prompt"] == "New prompt"
