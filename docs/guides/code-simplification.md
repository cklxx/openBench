# Code Simplification

Updated: 2026-03-18

Rules for keeping the OpenBench codebase clean and minimal.

---

## 1. Use Shared Utilities — Never Hand-Roll Primitives

Before writing any helper, check `src/openbench/_utils.py` first. If a utility exists, use it.

**Current shared utilities:**

| Utility | Location | Use |
|---------|----------|-----|
| `_parse_json(text)` | `_utils.py` | Extract JSON from LLM responses, handles markdown code blocks |

If a helper is used in 2+ modules, move it to `_utils.py`. If used in only one place, keep it local.

---

## 2. No Duplicate Logic Across Modules

The `_parse_json` function was previously duplicated in `planner.py` and `evaluator.py`. Extract shared logic immediately when duplication is found.

---

## 3. Return Named Results, Not Long Tuples

Tuples with 4+ elements are fragile. Use a dataclass or `typing.NamedTuple` instead.

```python
# BAD: 9-element tuple — positional errors are silent
return (output, tool_call_names, num_turns, input_tokens, ...)

# GOOD: named fields
@dataclass
class AgentRunResult:
    output: str
    tool_call_names: list[str]
    num_turns: int
    ...
```

---

## 4. Hoist Invariants Out of Loops

If a value doesn't change between loop iterations, compute it once before the loop.

```python
# BAD: repeated dict lookup every iteration
for line in fh:
    agent_a_name = meta["experiment"]["agent_a"]["name"]  # never changes

# GOOD
agent_a_name = meta["experiment"]["agent_a"]["name"]
for line in fh:
    ...
```

---

## 5. No Dead Assignments

Do not assign a variable only to immediately overwrite it.

```python
# BAD: first assignment is never observable
agent_a = baseline if baseline is not None else make_config(...)
if baseline is not None:
    agent_a = AgentConfig(...)  # overwrites unconditionally

# GOOD
if baseline is not None:
    agent_a = AgentConfig(...)
else:
    agent_a = make_config(...)
```

---

## 6. Extract Repeated Ternary Expressions

If the same conditional appears 3+ times in a block, name it once.

```python
# BAD
f"{'Agent B' if evaluation.winner == 'b' else 'Agent A'}"
f"[{'blue' if evaluation.winner == 'b' else 'green'}]"

# GOOD
is_b_winner = evaluation.winner == "b"
winner_label = "Agent B" if is_b_winner else "Agent A"
winner_color = "blue" if is_b_winner else "green"
```

---

## 7. Sort by Meaningful Keys

Do not sort by filename when chronological order is needed. UUID filenames have no time ordering.

```python
# BAD: sorts by random UUID filenames
for meta_path in sorted(exp_dir.glob("*_meta.json")):
    ...

# GOOD: sort by actual timestamp after loading
results.sort(key=lambda r: r.started_at)
```

---

## 8. Parallelize Independent I/O

When multiple operations have no data dependency, run them concurrently.

```python
# GOOD: agent_a and agent_b trials are independent per task
async with anyio.create_task_group() as tg:
    tg.start_soon(run_trial, agent_a, task, trials_a)
    tg.start_soon(run_trial, agent_b, task, trials_b)
```

---

## Quick Reference: Smell → Rule

| Code Smell | Rule |
|-----------|------|
| `_parse_json` in multiple modules | Move to `_utils.py` (Rule 1) |
| Return tuple with 5+ elements | Use a dataclass (Rule 3) |
| Dict/attr lookup inside `for` loop | Hoist above the loop (Rule 4) |
| Assign then immediately overwrite | Collapse to `if/else` (Rule 5) |
| Same ternary repeated 3× | Name the condition once (Rule 6) |
| `sorted(glob(...))` for time order | Sort by `started_at` field (Rule 7) |
| Sequential independent LLM calls | Use `anyio.create_task_group` (Rule 8) |
