# Engineering Workflow

Updated: 2026-03-18

Use this flow for every engineering task.

See also: [Code Simplification](code-simplification.md) | [Code Review](code-review-guide.md) | [Memory Management](memory-management.md)

## Core Rules

- Priority: safety > correctness > maintainability > speed.
- Trust caller and type invariants. Do not add defensive code without a real gap.
- Delete dead code. No deprecated branches, `_unused` names, or commented-out code.
- When requirements change, redesign cleanly. Do not add compatibility shims.
- Follow local patterns before introducing a new one.
- Change only files that matter to the task.

## Session Start

1. Greet `ckl`.
2. Load the [always-load set](memory-management.md#always-load-set).

## Planning

- Simple task: inspect the target files and implement directly.
- Non-trivial task: create `docs/plans/YYYY-MM-DD-short-slug.md` and keep it updated.
- Ask for missing information only when it changes correctness.

Decision order:
1. Explicit rules and hard constraints.
2. Reversibility and safe ordering.
3. Missing information that affects correctness.
4. User preference within the rules.

## Implementation Rules

- Keep naming and file structure consistent with nearby code.
- Follow [Code Simplification](code-simplification.md).
- If the user selects multiple options, implement all of them in one delivery.
- Shared helpers go in `src/openbench/_utils.py`; check there before writing a new utility.

## Validation

- Run lint before delivery: `ruff check src/`
- For logic changes, prefer TDD and cover edge cases.
- Use real dependencies in integration tests; mocks only in unit tests.

## Review and Commit

- Follow [Code Review](code-review-guide.md); fix P0 and P1 before commit.
- Small, scoped commits. Warn before destructive operations.
- Commit after the task is complete.

## Experiment Reports

After any experiment runs to completion, write a markdown report:

```
reports/YYYY-MM-DD-<experiment-name>.md
```

Include: hypothesis, winner, scores, key findings, next recommendation. Commit with the results.

## Experience Records

| Type | Entry path | Summary path |
|------|------------|--------------|
| Error | `docs/error-experience/entries/YYYY-MM-DD-slug.md` | `docs/error-experience/summary/entries/YYYY-MM-DD-slug.md` |
| Win | `docs/good-experience/entries/YYYY-MM-DD-slug.md` | `docs/good-experience/summary/entries/YYYY-MM-DD-slug.md` |

Index files stay index-only. See [Memory Management](memory-management.md) for authoring rules.
