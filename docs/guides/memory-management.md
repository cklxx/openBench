# Memory Management

Updated: 2026-03-18

Load memory in layers. Start small. Expand only when the current task needs it.

## Always-Load Set

Load these at the start of every conversation:

1. `docs/memory/long-term.md`
2. `docs/guides/engineering-workflow.md`
3. Latest 3 error summaries from `docs/error-experience/summary/entries/` (date DESC)
4. Latest 3 good summaries from `docs/good-experience/summary/entries/` (date DESC)

## Load On Demand

| Source | When to load |
|--------|--------------|
| Full error or good entry | The summary is not enough |
| `docs/plans/` | The task is in planning and past design work may matter |
| `docs/memory/user-patterns.md` | Deciding whether to auto-continue a recurring pattern |

## Retrieval Rules

- Read summaries before full entries.
- Prefer the most recent relevant item.
- Stop loading once you have enough context to act.

## Writing Rules

### Long-Term Memory

Use `docs/memory/long-term.md` only for durable rules that will matter across sessions.

- Keep it short.
- Update `Updated:` to day precision: `YYYY-MM-DD`.

### Experience Entries

Every new entry needs this `## Metadata` block:

```yaml
id: <type>-YYYY-MM-DD-<short-slug>
type: error_entry | good_entry | error_summary | good_summary
date: YYYY-MM-DD
tags:
  - <tag>
links:
  related: []
  see_also: []
```

### Index-Only Files

Do not put narrative content in these files:

- `docs/error-experience/README.md`
- `docs/good-experience/README.md`

## Topic Files

| File | Use |
|------|-----|
| `docs/memory/long-term.md` | Stable cross-session rules |
| `docs/memory/user-patterns.md` | Recurring user decision patterns for auto-continue |
