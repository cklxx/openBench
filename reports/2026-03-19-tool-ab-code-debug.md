# Experiment Report: Tool A/B — Bash Execution vs Read-Only for Code Debugging

**Date:** 2026-03-19
**Run ID:** 1b02ed9a-f13a-40ac-8051-47d4be0e03bc
**Experiment:** `tool_ab_code_debug`
**Model:** claude-haiku-4-5 | **Cost:** $0.086 (read_only) + $0.118 (bash_enabled)

---

## Hypothesis

An agent with Bash execution access will outperform a Read-only agent on code
debugging tasks, because running code reveals bugs that are hard to spot by reading.

---

## Setup

| Agent | Tools | Strategy |
|-------|-------|----------|
| read_only | Read, Glob | Must reason from source code |
| bash_enabled | Read, Glob, Bash | Can execute code to observe behavior |

Both agents got the same system prompt (adapted per strategy) and max_turns=8.

### Tasks (5 Python bugs via setup_files)

| # | Bug Type | File |
|---|----------|------|
| T1 | Floating point representation | bug1_float.py |
| T2 | Closure late binding | bug2_scope.py |
| T3 | Mutable default argument | bug3_mutation.py |
| T4 | Generator exhaustion | bug4_generator.py |
| T5 | Heap comparison with equal priorities | bug5_comparison.py |

---

## Results

### Correctness

| Task | read_only | bash_enabled |
|------|-----------|-------------|
| T1 (float) | Correct | Correct |
| T2 (closure) | Correct | Correct |
| T3 (mutable default) | Correct | Correct |
| T4 (generator) | Correct | Correct |
| T5 (heap comparison) | Correct | **FAILED** (empty output, hit max_turns) |

**read_only: 5/5 | bash_enabled: 4/5**

### Metrics

| Metric | read_only | bash_enabled | Delta |
|--------|-----------|-------------|-------|
| Latency (avg) | 15.22s | 17.22s | +13.1% |
| Tokens (avg) | 1,623 | 1,872 | +15.3% |
| Cost (avg) | $0.01717 | $0.02359 | +37.4% |
| Tool calls (avg) | 2.6 | 5.6 | +115% |
| Successes | 5/5 | 4/5 (T5 failed) | -20% |

---

## Key Findings

### 1. Read-only agent OUTPERFORMED bash_enabled
The read_only agent correctly identified all 5 bugs by reasoning from source code.
The bash_enabled agent failed on T5 — it spent all its turns executing variations
of the buggy code and hit the max_turns limit (stop_reason: tool_use) without
producing a final explanation.

### 2. Bash execution is a distraction for well-known bugs
All 5 bugs (float precision, closure scope, mutable default, generator exhaustion,
heap comparison) are classic Python gotchas. The model recognizes them by pattern
matching on the source code. Executing the code confirms what the model already
knows, wasting turns and tokens.

### 3. bash_enabled used 2x more tool calls but got worse results
The bash_enabled agent averaged 5.6 tool calls vs 2.6 for read_only. On T5, it
made 9 tool calls (mostly Bash executions) trying to reproduce the error, ran out
of turns, and produced empty output.

### 4. Anomaly: read_only agent used Bash on T5
The read_only agent (allowed_tools: [Read, Glob]) appears to have called Bash on
Task 5 (tool list shows: Read, Bash, Glob, Read). **This suggests the SDK may not
strictly enforce allowed_tools** — needs investigation. Despite this, the agent
still produced a correct explanation.

### 5. max_turns=8 is too low for bash_enabled
The bash_enabled agent's turn count was much higher (14, 13, 12, 10, 21 turns
reported by SDK vs 7, 8, 6, 7, 10 for read_only). The 8-turn limit was hit on T5.
Note: SDK reports "turns" differently from max_turns — each tool call + response
counts. With max_turns=8, the effective tool budget is ~4 round trips.

---

## Verdict

**read_only wins** — 5/5 vs 4/5, faster, cheaper. For well-known Python bugs,
Bash execution adds overhead without improving accuracy. The model already knows
these patterns.

---

## Anomalies to Investigate

1. **allowed_tools enforcement**: read_only agent called Bash despite not having it
   in allowed_tools. Check if `claude_agent_sdk` actually enforces this constraint
   or just treats it as a suggestion.

2. **max_turns vs SDK turn counting**: The SDK reports more turns than max_turns
   allows. Clarify whether max_turns limits agent decision points or total messages.

---

## Next Experiments

1. **Bugs that REQUIRE execution**: Design tasks with environment-dependent bugs
   (missing imports, wrong Python version, race conditions, file I/O issues) where
   reading source alone is genuinely insufficient.

2. **Higher max_turns for bash_enabled**: Re-run with max_turns=16 to give the
   execution-based agent enough budget to explore + explain.

3. **Sonnet vs Haiku on code debugging**: Test whether a stronger model benefits
   more from tool access (haiku might be too good at pattern-matching already).
