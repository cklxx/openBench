"""Shared internal utilities."""
from __future__ import annotations

import json
import re
from typing import Any


def _resolve_system_prompt(sp: Any) -> str | None:
    """Resolve SkillConfig or str to a plain string for SDK consumption."""
    if sp is None or isinstance(sp, str):
        return sp
    # SkillConfig: has a system_prompt attribute
    return sp.system_prompt


def _parse_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    raise ValueError(f"Cannot parse JSON from: {text[:300]}")
