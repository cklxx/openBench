# Code Review Guide

Updated: 2026-03-18

Run after lint and tests, before every commit.

## Severity

| Severity | Action |
|----------|--------|
| `P0` | Fix before commit. Security, data loss, or clear correctness failure. |
| `P1` | Fix before commit. Significant architecture, reliability, or maintainability issue. |
| `P2` | Do not block commit; create a follow-up task. |
| `P3` | Optional. |

## Review Checklist

### Architecture

- Responsibilities are not mixed across modules.
- New behavior extends existing design cleanly; no growing switch chains or special cases.
- Shared utilities used; no hand-rolled duplicates of existing helpers.
- Abstractions justify themselves: used in 2+ places or removed.

### Correctness

- Errors are handled; not silently swallowed.
- Edge cases covered: empty inputs, None, zero values, partial failure.
- Concurrency is safe (anyio task groups, no shared mutable state across trials).
- Tests prove changed behavior.

### Security

- No secrets or credentials hardcoded or logged.
- File inputs validated (no path traversal).
- LLM prompt inputs treated as untrusted.

### Performance

- No N+1 I/O patterns (file reads or LLM calls in loops without batching).
- Independent operations parallelized where appropriate (`anyio.create_task_group`).
- No unnecessary recomputation of static values inside loops.

### Experiment Discipline

- Experiments test exactly ONE diff between agent_a and agent_b.
- SDK-reported metrics preferred over estimates.
- Every trial runs in an isolated working directory.
- Results saved to `results/` and report written to `reports/`.

## Workflow

1. Run `ruff check src/`.
2. Review against this checklist.
3. Fix every P0 and P1.
4. Re-run lint after fixes.
5. Commit only when remaining findings are P2 or below.
