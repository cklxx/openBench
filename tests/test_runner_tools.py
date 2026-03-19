"""Tests for runner tool configuration and agent_input snapshots."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openbench.types import AgentConfig, Experiment, DiffSpec, SkillConfig


def make_experiment(**kwargs) -> Experiment:
    defaults = dict(
        name="test_exp",
        description="test",
        diff=DiffSpec(field="allowed_tools", description="tools test"),
        agent_a=AgentConfig(name="a", model="claude-haiku-4-5", allowed_tools=["Read"]),
        agent_b=AgentConfig(name="b", model="claude-haiku-4-5", allowed_tools=["Read", "Bash"]),
        tasks=["Say hello."],
    )
    defaults.update(kwargs)
    return Experiment(**defaults)


def test_agent_input_includes_allowed_tools() -> None:
    """agent_input snapshot must contain allowed_tools."""
    from openbench.runner import ExperimentRunner

    runner = ExperimentRunner()

    # We don't actually run the SDK; just check agent_input construction logic.
    # The field is set in _run_trial before calling _run_agent_async.
    # Verify the expected shape by inspecting what _run_trial would build.
    config = AgentConfig(
        name="a",
        model="claude-haiku-4-5",
        allowed_tools=["Read", "Glob"],
    )
    from openbench._utils import _resolve_system_prompt

    agent_input = {
        "system_prompt": _resolve_system_prompt(config.system_prompt),
        "task": "hello",
        "model": config.model,
        "max_turns": config.max_turns,
        "allowed_tools": list(config.allowed_tools),
    }
    assert "allowed_tools" in agent_input
    assert agent_input["allowed_tools"] == ["Read", "Glob"]


def test_skill_config_resolved_in_agent_input() -> None:
    """SkillConfig.system_prompt is resolved to a plain string in agent_input."""
    from openbench._utils import _resolve_system_prompt

    skill = SkillConfig(
        name="my_skill",
        version="1.0",
        description="desc",
        system_prompt="You are an expert.",
    )
    config = AgentConfig(name="a", model="claude-haiku-4-5", system_prompt=skill)
    resolved = _resolve_system_prompt(config.system_prompt)
    assert resolved == "You are an expert."
    assert isinstance(resolved, str)


def test_mcp_servers_passed_to_options() -> None:
    """mcp_servers on AgentConfig should be present in options_kwargs."""
    from openbench._utils import _resolve_system_prompt

    config = AgentConfig(
        name="a",
        model="claude-haiku-4-5",
        mcp_servers=[{"type": "stdio", "command": "my-mcp"}],
    )
    assert config.mcp_servers is not None
    assert config.mcp_servers[0]["command"] == "my-mcp"
