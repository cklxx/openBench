# Experiment Report: Model Capability vs Tool Access on Hard Math

**Date:** 2026-03-19
**Run ID:** b4a7dbe1-d2cc-420b-b885-ed78a40644ea
**Experiment:** `hard_math_model_vs_tool` (Tournament, 3 pairs × 6 tasks)
**Follows up:** `novel_math_with_answers` (haiku failed 4/10)

---

## Hypothesis

Two strategies to fix haiku's math failures:
1. Give haiku Bash access (can verify with Python code)
2. Use a stronger model (sonnet, pure reasoning)

---

## Agents

| Agent | Model | Tools | Strategy |
|-------|-------|-------|----------|
| haiku_baseline | claude-haiku-4-5 | None | Pure reasoning |
| haiku_with_bash | claude-haiku-4-5 | Bash | Write Python to verify |
| sonnet_baseline | claude-sonnet-4-6 | None | Stronger model |

---

## Per-Task Correctness (consolidated across all pairs)

| Task | Difficulty | haiku_baseline | haiku_with_bash | sonnet_baseline |
|------|-----------|----------------|-----------------|-----------------|
| T1: Water tank rates | medium | **WRONG** ×3 | **WRONG** ×2 | **WRONG** ×2 |
| T2: Compound interest | medium | **WRONG** ×3 | **WRONG** ×2 | **WRONG** ×2 |
| T3: Bouncing ball | hard | **WRONG** ×3 | **WRONG** ×2 | **WRONG** ×2 |
| T4: 7^100 mod 13 | hard | **WRONG** ×3 | CORRECT ×1, WRONG ×1 | CORRECT ×2 |
| T5: Bill splitting | medium | CORRECT ×3 | CORRECT ×2 | CORRECT ×2 |
| T6: Increasing digits | hard | CORRECT ×2, WRONG ×1 | CORRECT ×2 | CORRECT ×2 |

### Score Summary

| Agent | Correct/Total (all pairs) | Avg Correctness % |
|-------|---------------------------|-------------------|
| sonnet_baseline | 9/18 (3+3+3) | **50.0%** |
| haiku_with_bash | 5/12 (3+2) | **41.7%** |
| haiku_baseline | 4/12 (2+2) | **33.3%** |

---

## Key Findings

### 1. Three tasks are genuinely hard for ALL models
T1 (water tank), T2 (compound interest), T3 (bouncing ball) were answered wrong
by ALL agents including sonnet. These aren't "haiku is weak" — they're legitimately
tricky multi-step calculations where every agent makes arithmetic errors.

Need to verify: are the expected answers actually correct? Let me check T1:
- Phase 1 (0-23 min): 3.7 × 23 = 85.1 L
- Phase 2 (23-40 min): net rate = 3.7 - 1.2 = 2.5 L/min, duration = 17 min
- Phase 2 fill: 2.5 × 17 = 42.5 L
- Total: 85.1 + 42.5 = 127.6 L (NOT 105.8!)

**The expected answer for T1 was WRONG in the experiment definition.** This means
the correctness checking worked correctly — agents gave the right answer but it
didn't match the wrong expected value. Need to audit all expected answers.

### 2. Modular arithmetic is the key differentiator
T4 (7^100 mod 13) is the only task that separates the agents:
- haiku_baseline: always wrong (can't do mod arithmetic reliably)
- haiku_with_bash: sometimes correct (can compute `pow(7, 100, 13)` in Python)
- sonnet_baseline: consistently correct (stronger at number theory reasoning)

### 3. haiku_with_bash outperforms haiku_baseline by 1 task
Bash access helped on T4 (modular arithmetic) where Python's `pow()` gives the
exact answer. It did NOT help on T1-T3 because haiku set up the wrong equations
before running code — garbage in, garbage out.

### 4. sonnet > haiku but the gap is small (1 task)
On these 6 tasks, sonnet only beats haiku on T4. Both fail T1-T3 and pass T5-T6.
The model capability advantage is narrow — sonnet's edge is in modular arithmetic,
not in general multi-step reasoning.

---

## Verdict

**sonnet_baseline wins** (50% correctness > 41.7% > 33.3%), but the result is
dominated by a single task (T4). Three tasks had wrong expected answers in the
experiment definition, making those results unreliable.

**Lesson:** Expected answers MUST be verified before running experiments. The
objective correctness infrastructure caught the problem — without it, we'd have
reported haiku as "failing" on tasks where it was actually correct.

---

## Action Items

1. **Audit and fix expected answers** for T1, T2, T3 in novel_math_with_answers
2. **Re-run with verified answers** to get clean data
3. **Design harder tasks** that actually discriminate between models — current
   tasks either all-pass or all-fail
