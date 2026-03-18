# OpenBench — Agent Contract

Minimize mandatory reading. Expand context only when triggered.

## 0. Read Policy

1. Read **§1** on every task.
2. Read **§2** only when a trigger matches.
3. No trigger? Follow **§3** and stop expanding context.

---

## 1. Mandatory Core

### 1.1 Identity and priority

- Greet **ckl** at conversation start.
- Priority: **safety > correctness > maintainability > speed**.
- User: senior engineer; values clean architecture, minimal complexity, direct answers.

### 1.2 Code style (non-negotiable)

- Max function body: **20 lines**. Extract if exceeded.
- No comments that restate code. Only "why" comments for non-obvious decisions.
- Every abstraction must justify itself: if used <2 places, inline it.
- Delete dead code immediately. No TODOs in committed code.
- Type annotations are documentation. Verbose names > comments.
- Between two correct approaches, pick the one with fewer moving parts.
- Trust caller and type invariants; no unnecessary defensive code.
- No compatibility shims when requirements change; redesign cleanly.
- Modify only files relevant to the task.

### 1.3 Experiment discipline

- **One diff**: experiments must test exactly ONE variable between agent_a and agent_b.
- **SDK first**: prefer SDK-reported metrics over estimates; fall back only when SDK returns zero.
- **Isolation**: every trial runs in its own `tempfile.TemporaryDirectory`.
- **Reports**: every completed experiment gets a `reports/YYYY-MM-DD-<slug>.md` committed to git.

### 1.4 Delivery

- Run lint before delivery: `ruff check src/`.
- Small, scoped commits. Warn before destructive operations.
- Follow [Code Review Guide](docs/guides/code-review-guide.md); fix P0/P1 before commit.

---

## 2. Progressive Disclosure (trigger-gated)

| Trigger | Load |
|---|---|
| Non-trivial multi-step task | `docs/guides/engineering-workflow.md`; create `docs/plans/YYYY-MM-DD-slug.md` |
| Memory / history retrieval | `docs/guides/memory-management.md`; summaries first |
| Code quality / simplification question | `docs/guides/code-simplification.md` |
| Architecture or module boundary question | §5 Project Snapshot below |
| User correction | Codify preventive rule in `docs/memory/user-patterns.md` before resuming |
| Error or regression | Write entry to `docs/error-experience/entries/` |
| Notable win or insight | Write entry to `docs/good-experience/entries/` |

No trigger → do not load.

---

## 3. Default Route

1. Read §1 only.
2. Inspect target files and neighboring patterns.
3. Implement minimal correct change.
4. Proportionate verification.
5. Commit and report.

---

## 4. Experience Records

| Type | Entry path | Summary path |
|------|------------|--------------|
| Error | `docs/error-experience/entries/YYYY-MM-DD-slug.md` | `docs/error-experience/summary/entries/YYYY-MM-DD-slug.md` |
| Win | `docs/good-experience/entries/YYYY-MM-DD-slug.md` | `docs/good-experience/summary/entries/YYYY-MM-DD-slug.md` |

Index files stay index-only (no narrative content).

---

## 5. Project Snapshot

- **Purpose**: automated A/B testing loop to optimize Claude agent configurations.
- **Loop**: `ExperimentPlanner` → `ExperimentRunner` → `AutoEvaluator` → `ResultStore` → repeat.
- **Key dirs**: `src/openbench/` (core), `experiments/` (manual experiments), `programs/` (ResearchProgram configs), `results/` (raw JSONL data), `reports/` (human-readable reports).
- **Entry point**: `openbench` CLI (`src/openbench/cli.py`).

---

## 6. Detail Sources (trigger-gated only)

`docs/guides/engineering-workflow.md` · `docs/guides/code-simplification.md` · `docs/guides/code-review-guide.md` · `docs/guides/memory-management.md`
