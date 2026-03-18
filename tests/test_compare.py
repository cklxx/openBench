"""Tests for ResultComparator._print_winner_banner."""
from __future__ import annotations

import io

import pytest
from rich.console import Console

from openbench.compare import ResultComparator
from openbench.types import (
    AgentConfig,
    DiffSpec,
    Experiment,
    ExperimentResult,
    TrialMetrics,
    TrialResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent(name: str) -> AgentConfig:
    return AgentConfig(
        name=name,
        model="claude-haiku-4-5",
        system_prompt=None,
        allowed_tools=[],
        max_turns=3,
        extra_options={},
    )


def _trial(
    agent_name: str,
    task_index: int = 0,
    latency_ms: float = 1000.0,
    error: str | None = None,
) -> TrialResult:
    return TrialResult(
        trial_id="t1",
        experiment_name="test_exp",
        agent_name=agent_name,
        task="test task",
        task_index=task_index,
        output="output",
        metrics=TrialMetrics(
            latency_ms=latency_ms,
            total_tokens=100,
            input_tokens=80,
            output_tokens=20,
            estimated_cost_usd=0.001,
            num_tool_calls=0,
            tool_call_names=[],
            num_turns=1,
            stop_reason="error" if error else "end_turn",
            error=error,
        ),
        timestamp="2026-01-01T00:00:00+00:00",
        workdir="/tmp",
    )


def _result(trials_a: list[TrialResult], trials_b: list[TrialResult]) -> ExperimentResult:
    exp = Experiment(
        name="test_exp",
        description="test",
        diff=DiffSpec(field="system_prompt", description="none vs prompt"),
        agent_a=_agent("baseline"),
        agent_b=_agent("variant"),
        tasks=["task1"],
        tags=[],
        num_samples=1,
    )
    return ExperimentResult(
        experiment=exp,
        trials_a=trials_a,
        trials_b=trials_b,
        run_id="run1",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
    )


def _capture_banner(result: ExperimentResult) -> str:
    sio = io.StringIO()
    console = Console(file=sio, force_terminal=False, highlight=False)
    ResultComparator(console=console)._print_winner_banner(result)
    return sio.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWinnerBanner:
    def test_a_wins_on_success_rate(self) -> None:
        result = _result(
            trials_a=[_trial("baseline")],
            trials_b=[_trial("variant", error="boom")],
        )
        output = _capture_banner(result)
        assert "Recommended Winner" in output
        assert "baseline" in output
        assert "success rate" in output

    def test_b_wins_on_success_rate(self) -> None:
        result = _result(
            trials_a=[_trial("baseline", error="boom")],
            trials_b=[_trial("variant")],
        )
        output = _capture_banner(result)
        assert "Recommended Winner" in output
        assert "variant" in output
        assert "success rate" in output

    def test_tie_latency_a_wins(self) -> None:
        result = _result(
            trials_a=[_trial("baseline", latency_ms=1000.0)],
            trials_b=[_trial("variant", latency_ms=2000.0)],
        )
        output = _capture_banner(result)
        assert "baseline" in output
        assert "latency" in output

    def test_tie_latency_b_wins(self) -> None:
        result = _result(
            trials_a=[_trial("baseline", latency_ms=2000.0)],
            trials_b=[_trial("variant", latency_ms=1000.0)],
        )
        output = _capture_banner(result)
        assert "variant" in output
        assert "latency" in output

    def test_all_errors_no_clear_winner(self) -> None:
        result = _result(
            trials_a=[_trial("baseline", error="error")],
            trials_b=[_trial("variant", error="error")],
        )
        output = _capture_banner(result)
        assert "No Clear Winner" in output
        assert "All trials errored" in output
        # Must NOT declare a normal winner
        assert "Recommended Winner" not in output

    def test_decision_signal_note_present(self) -> None:
        result = _result(
            trials_a=[_trial("baseline")],
            trials_b=[_trial("variant", error="boom")],
        )
        output = _capture_banner(result)
        assert "Decided by" in output

    def test_per_agent_totals_shown(self) -> None:
        """Each agent's success count uses its own trial count as denominator."""
        result = _result(
            trials_a=[_trial("baseline"), _trial("baseline", task_index=1)],
            trials_b=[_trial("variant")],
        )
        output = _capture_banner(result)
        # A has 2 trials, B has 1 — should not show "2/2 vs 2/1" style
        assert "2/2" in output or "1/1" in output  # per-agent denominators
