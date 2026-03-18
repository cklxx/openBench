# OpenBench — Claude Code Config

You are assisting **ckl** with OpenBench, an A/B testing platform for Claude agents.

Agent contract: **AGENTS.md** (coding standards, workflow, progressive disclosure).

---

## Memory Loading

**Always-load** (every conversation start):
1. `docs/memory/long-term.md`
2. `docs/guides/engineering-workflow.md`
3. Latest 3 from `docs/error-experience/summary/entries/` (date DESC)
4. Latest 3 from `docs/good-experience/summary/entries/` (date DESC)

**On-demand**: see `docs/guides/memory-management.md`.

---

## Key References

[Engineering Workflow](docs/guides/engineering-workflow.md) · [Memory Management](docs/guides/memory-management.md) · [Code Review](docs/guides/code-review-guide.md) · [Code Simplification](docs/guides/code-simplification.md)

---

## Behavior Rules

- **Self-correction:** On ANY user correction, codify a preventive rule before resuming.
- **Auto-continue:** Check `docs/memory/user-patterns.md`; if same decision ≥2 times, proceed with inline note. Ask when ambiguous, irreversible, or no match.
- **One diff at a time:** Experiments must change exactly ONE variable between agent_a and agent_b.
- **Experiment reports:** Every completed experiment gets a markdown report in `reports/` committed to git.
