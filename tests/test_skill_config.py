"""Tests for SkillConfig and _resolve_system_prompt."""
from __future__ import annotations

import pytest

from openbench._utils import _resolve_system_prompt
from openbench.types import SkillConfig


def make_skill(prompt: str = "Do the thing.") -> SkillConfig:
    return SkillConfig(
        name="test_skill",
        version="1.0",
        description="A test skill",
        system_prompt=prompt,
        required_tools=["Read"],
    )


def test_resolve_str() -> None:
    assert _resolve_system_prompt("hello") == "hello"


def test_resolve_none() -> None:
    assert _resolve_system_prompt(None) is None


def test_resolve_skill_config() -> None:
    skill = make_skill("You are helpful.")
    assert _resolve_system_prompt(skill) == "You are helpful."


def test_resolve_skill_config_empty_prompt() -> None:
    skill = make_skill("")
    assert _resolve_system_prompt(skill) == ""


def test_skill_config_fields() -> None:
    skill = make_skill("Test prompt")
    assert skill.name == "test_skill"
    assert skill.version == "1.0"
    assert skill.description == "A test skill"
    assert skill.required_tools == ["Read"]
