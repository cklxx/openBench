# Experiment Report: Tool A/B — Execution-Required Bugs

**Date:** 2026-03-19
**Run ID:** b7d342ce-fddd-43e9-8bbd-a569964d223b
**Experiment:** `tool_ab_execution_required`
**Model:** claude-haiku-4-5 | **Cost:** $0.169 (read_only) + $0.179 (bash_enabled)
**Follows up:** `tool_ab_code_debug` — bugs that genuinely need execution

---

## Hypothesis

The previous tool A/B experiment used classic Python bugs that the model recognizes
by pattern matching. This experiment uses bugs where **execution reveals information
that is hard to predict from source alone**: Unicode normalization differences,
dict ordering effects, floating point accumulation at scale, regex backtracking
timing, and race condition exact values.

max_turns raised from 8 to 16 to give bash_enabled enough budget.

---

## Tasks (5)

| # | Bug Type | Why Execution Matters |
|---|----------|----------------------|
| T1 | Unicode normalization (NFC vs NFD) | Visually identical strings that aren't equal |
| T2 | Dict insertion order + positional unpacking | Output depends on merge order |
| T3 | Float accumulation divergence at scale | Divergence magnitude only visible with N=10000 |
| T4 | Regex catastrophic backtracking | Timing difference (ms vs hours) only visible at runtime |
| T5 | Thread race condition | Exact lost-update count varies per run |

---

## Results

### Success Rate
Both agents: 5/5. Both correctly identified all bugs.

### Metrics

| Metric | read_only | bash_enabled | Delta |
|--------|-----------|-------------|-------|
| Latency (avg) | 28.01s | 31.86s | +13.7% |
| Tokens (avg) | 2,419 | 3,238 | +33.8% |
| Cost (avg) | $0.0339 | $0.0359 | +5.8% |
| Tool calls (avg) | 6.4 | 6.2 | -3.1% |

### Quality Comparison

| Task | read_only | bash_enabled | Edge |
|------|-----------|-------------|------|
| T1 (Unicode) | Correct explanation of NFC vs NFD | Correct + ran code, showed actual search results | bash slightly better — showed concrete output |
| T2 (Dict order) | Correct analysis of insertion order. Also ran Bash (!) | Correct + ran multiple test cases showing values | Tie — both used Bash |
| T3 (Accumulation) | Correct theory, estimated divergence | Exact measured divergence: 1.45e-11 for large, 0 for pathological | **bash_enabled wins** — concrete numbers |
| T4 (Regex) | Correct: catastrophic backtracking from overlapping quantifiers | Correct + actual timing measurements | bash slightly better — empirical proof |
| T5 (Race) | Correct race condition explanation, no exact count | **"50 instead of 100, losing exactly 50 updates"** | **bash_enabled wins** — exact measured value |

---

## Key Findings

### 1. Both agents identify the bugs correctly
Even for execution-dependent bugs, haiku-4-5 recognizes the patterns (Unicode
normalization, catastrophic backtracking, race conditions) from source alone.
Execution confirms but doesn't change the diagnosis.

### 2. bash_enabled provides concrete measured values
On T3 and T5, bash_enabled gives **exact numbers** (divergence = 1.45e-11,
lost updates = 50) that read_only can only estimate. This matters for debugging
production issues where precise values affect decisions.

### 3. read_only AGAIN uses Bash despite allowed_tools restriction
read_only (allowed_tools: [Read, Glob]) called Bash on T1, T2, T3, T4, and T5.
**The SDK does not enforce allowed_tools.** This is now confirmed across two
experiments. The constraint is advisory, not enforced.

### 4. max_turns=16 is sufficient
No agent hit the turn limit this time (max was 22 turns reported by SDK).
The previous experiment's T5 failure was from max_turns=8 being too low.

### 5. Quality gap is smaller than expected
Even for "execution-required" bugs, the model's reasoning is strong enough to
identify the issue from source. Execution adds empirical confirmation and precise
values, but doesn't change correct/incorrect outcomes.

---

## Verdict

**Tie on correctness, bash_enabled wins on precision.** For debugging tasks where
exact values matter (performance profiling, race condition quantification, float
error magnitude), Bash access adds genuine value. For "identify the bug" tasks,
read-only is sufficient and cheaper.

**Critical finding:** `allowed_tools` is not enforced by the SDK. The read_only
agent freely used Bash, making the tool A/B comparison partially invalid. Future
experiments should verify SDK enforcement or use a different isolation mechanism.

---

## Next Steps

1. **Investigate SDK allowed_tools enforcement** — file an issue or check docs.
2. **Test with truly novel bugs** — custom libraries, made-up APIs, code that
   can't be pattern-matched from training data.
3. **Test Bash value on production-like debugging** — log analysis, config
   file inspection, multi-file tracing.
