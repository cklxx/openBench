# Long-Term Memory

Updated: 2026-03-18

## Keep Here

Only durable rules that should survive across tasks. Keep it short.

## Active Rules

- Experiments must test exactly ONE diff between agent_a and agent_b (the DiffSpec).
- Prefer SDK-reported token counts and cost over estimates; fall back only when SDK returns zero.
- Every trial runs in an isolated `tempfile.TemporaryDirectory`; never share state between trials.
- After any experiment completes, write a report to `reports/YYYY-MM-DD-<slug>.md` and commit to git.
- Shared helpers (e.g., `_parse_json`) live in `src/openbench/_utils.py`; check there before adding a new utility.
- Sort results by `started_at` ISO timestamp, not by UUID filename (UUIDs have no time ordering).
- Results storage: JSONL trials + JSON metadata under `results/<experiment-name>/`.
- All documentation and memory files in English.
