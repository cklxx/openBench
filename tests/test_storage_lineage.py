"""Tests for ResultStore lineage write/read and SkillConfig serialization."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from openbench.storage import ResultStore, _to_dict, _agent_config_from_dict
from openbench.types import AgentConfig, SkillConfig, TrialMetrics, TrialResult


def make_skill(name: str = "my_skill", version: str = "1.0") -> SkillConfig:
    return SkillConfig(
        name=name,
        version=version,
        description="Test skill",
        system_prompt="You are a test assistant.",
        required_tools=["Read"],
    )


def make_trial(experiment_name: str = "test_exp") -> TrialResult:
    return TrialResult(
        trial_id="abc123",
        experiment_name=experiment_name,
        agent_name="a",
        task="Do something.",
        task_index=0,
        output="Done.",
        metrics=TrialMetrics(
            latency_ms=100.0,
            total_tokens=50,
            input_tokens=40,
            output_tokens=10,
            estimated_cost_usd=0.0005,
            num_tool_calls=1,
            tool_call_names=["Read"],
            num_turns=1,
            stop_reason="end_turn",
            error=None,
        ),
        timestamp="2026-01-01T00:00:00Z",
        workdir="/tmp/x",
    )


def test_lineage_write_read_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ResultStore(results_root=tmp)
        skill = make_skill()
        trial = make_trial()

        store.save_lineage_entry(skill, trial, score=85.5)

        entries = store.load_lineage("my_skill")
        assert len(entries) == 1
        e = entries[0]
        assert e["skill_name"] == "my_skill"
        assert e["version"] == "1.0"
        assert e["experiment_name"] == "test_exp"
        assert e["trial_id"] == "abc123"
        assert e["score"] == 85.5
        assert e["stop_reason"] == "end_turn"


def test_lineage_multiple_entries() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ResultStore(results_root=tmp)
        skill = make_skill()

        for i in range(5):
            trial = make_trial(f"exp_{i}")
            store.save_lineage_entry(skill, trial, score=float(i * 10))

        entries = store.load_lineage("my_skill")
        assert len(entries) == 5


def test_lineage_no_entries_returns_empty_list() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ResultStore(results_root=tmp)
        entries = store.load_lineage("nonexistent_skill")
        assert entries == []


def test_lineage_path_sanitization_special_chars() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ResultStore(results_root=tmp)
        skill = SkillConfig(
            name="my/skill:v1!",
            version="1.0",
            description="desc",
            system_prompt="prompt",
        )
        trial = make_trial()
        store.save_lineage_entry(skill, trial, score=50.0)

        # Should not raise; file uses sanitized name
        lineage_dir = Path(tmp) / "_lineage"
        files = list(lineage_dir.iterdir())
        assert len(files) == 1
        # Filename should not contain /, :, !
        fname = files[0].name
        assert "/" not in fname
        assert ":" not in fname
        assert "!" not in fname

        # Loading by original skill name should work
        entries = store.load_lineage("my/skill:v1!")
        assert len(entries) == 1


def test_skill_config_serialization_roundtrip() -> None:
    """SkillConfig in AgentConfig should survive _to_dict -> _agent_config_from_dict."""
    skill = make_skill()
    config = AgentConfig(
        name="agent_a",
        model="claude-haiku-4-5",
        system_prompt=skill,
        allowed_tools=["Read"],
    )

    d = _to_dict(config)
    assert isinstance(d["system_prompt"], dict)
    assert d["system_prompt"]["__skill__"] is True
    assert d["system_prompt"]["name"] == "my_skill"

    restored = _agent_config_from_dict(d)
    assert isinstance(restored.system_prompt, SkillConfig)
    assert restored.system_prompt.name == "my_skill"
    assert restored.system_prompt.version == "1.0"
    assert restored.system_prompt.system_prompt == "You are a test assistant."


def test_plain_string_system_prompt_still_works() -> None:
    config = AgentConfig(
        name="b",
        model="claude-haiku-4-5",
        system_prompt="Be helpful.",
    )
    d = _to_dict(config)
    assert d["system_prompt"] == "Be helpful."
    restored = _agent_config_from_dict(d)
    assert restored.system_prompt == "Be helpful."


def test_none_system_prompt_still_works() -> None:
    config = AgentConfig(name="c", model="claude-haiku-4-5")
    d = _to_dict(config)
    assert d["system_prompt"] is None
    restored = _agent_config_from_dict(d)
    assert restored.system_prompt is None


def test_mcp_servers_roundtrip() -> None:
    config = AgentConfig(
        name="d",
        model="claude-haiku-4-5",
        mcp_servers=[{"type": "stdio", "command": "my-mcp"}],
    )
    d = _to_dict(config)
    assert d["mcp_servers"] == [{"type": "stdio", "command": "my-mcp"}]
    restored = _agent_config_from_dict(d)
    assert restored.mcp_servers == [{"type": "stdio", "command": "my-mcp"}]
