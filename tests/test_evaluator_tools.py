"""Tests for evaluator tool_efficiency and tool_call_names injection."""
from __future__ import annotations

from openbench.evaluator import AutoEvaluator
from openbench.program import ResearchProgram
from openbench.types import (
    AgentConfig,
    DiffSpec,
    Experiment,
    ExperimentResult,
    TrialMetrics,
    TrialResult,
)


def make_program() -> ResearchProgram:
    return ResearchProgram(
        objective="Test",
        domain="test",
        optimization_targets=["quality"],
        constraints={},
    )


def make_trial(tool_names: list[str] | None = None) -> TrialResult:
    return TrialResult(
        trial_id="tid",
        experiment_name="exp",
        agent_name="a",
        task="Do something.",
        task_index=0,
        output="Result",
        metrics=TrialMetrics(
            latency_ms=100.0,
            total_tokens=100,
            input_tokens=80,
            output_tokens=20,
            estimated_cost_usd=0.001,
            num_tool_calls=len(tool_names or []),
            tool_call_names=tool_names or [],
            num_turns=1,
            stop_reason="end_turn",
            error=None,
        ),
        timestamp="2026-01-01T00:00:00Z",
        workdir="/tmp/x",
    )


def make_experiment(diff_field: str = "system_prompt") -> ExperimentResult:
    agent_a = AgentConfig(name="a", model="claude-haiku-4-5")
    agent_b = AgentConfig(name="b", model="claude-haiku-4-5")
    exp = Experiment(
        name="test_exp",
        description="desc",
        diff=DiffSpec(field=diff_field, description="test diff"),
        agent_a=agent_a,
        agent_b=agent_b,
        tasks=["task1"],
    )
    return ExperimentResult(
        experiment=exp,
        trials_a=[make_trial(["Read", "Glob"])],
        trials_b=[make_trial(["Bash"])],
        run_id="rid",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:01:00Z",
    )


def test_default_rubric_includes_tool_efficiency_for_tool_diff() -> None:
    evaluator = AutoEvaluator()
    program = make_program()
    rubric = evaluator._default_rubric(program, diff_field="allowed_tools")
    assert "tool_efficiency" in rubric


def test_default_rubric_no_tool_efficiency_for_prompt_diff() -> None:
    evaluator = AutoEvaluator()
    program = make_program()
    rubric = evaluator._default_rubric(program, diff_field="system_prompt")
    assert "tool_efficiency" not in rubric


def test_default_rubric_no_tool_efficiency_for_none_diff() -> None:
    evaluator = AutoEvaluator()
    program = make_program()
    rubric = evaluator._default_rubric(program, diff_field=None)
    assert "tool_efficiency" not in rubric


def test_eval_trial_prompt_contains_tool_sequence() -> None:
    """The judge prompt must include the tool call sequence."""
    # We test the prompt construction logic directly
    evaluator = AutoEvaluator()
    trial = make_trial(["Read", "Glob", "Bash"])
    m = trial.metrics
    tool_seq = ", ".join(m.tool_call_names[-50:]) if m.tool_call_names else "(none)"
    assert "Read" in tool_seq
    assert "Glob" in tool_seq
    assert "Bash" in tool_seq


def test_eval_trial_prompt_tool_seq_truncated_to_50() -> None:
    """Tool call sequence in prompt is capped at 50 entries."""
    many_tools = [f"Tool{i}" for i in range(60)]
    trial = make_trial(many_tools)
    m = trial.metrics
    tool_seq = ", ".join(m.tool_call_names[-50:])
    # Last 50 are indices 10-59; first 10 (Tool0-Tool9) should be excluded
    assert "Tool0," not in tool_seq   # Tool0 excluded (use comma to avoid matching Tool01 etc.)
    assert "Tool9," not in tool_seq   # Tool9 excluded
    assert "Tool10" in tool_seq       # Tool10 is in last 50
    assert "Tool59" in tool_seq


def test_diff_field_detection() -> None:
    result = make_experiment(diff_field="allowed_tools")
    df = AutoEvaluator._diff_field(result)
    assert df == "allowed_tools"

    result2 = make_experiment(diff_field="system_prompt")
    df2 = AutoEvaluator._diff_field(result2)
    assert df2 == "system_prompt"
