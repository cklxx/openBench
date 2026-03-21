# Experiment Report: Tool Distractor Resilience

**Date:** 2026-03-20
**Experiment:** `tool_distractor_resilience` (8-way tournament, 3 tasks × n=3)
**Total trials:** 504 (8 configs × 3 tasks × 3 samples × 7 pairs)

---

## Research Question

Published: "Tool preferences in agentic LLMs are unreliable" (2025). Models
have a "Chekhov's gun" effect — they use all provided tools. But what's the
actual degradation curve as distractor tools increase?

## Setup

Same 3 tasks with 1/5/10/20 available tools. Only Bash (and Read for T3)
are needed. Other tools are distractors.

---

## Results (corrected: T2 Fibonacci had wrong expected answer)

| Config | T1 (primes) | T3 (CSV count) | Avg Tools Used |
|--------|-------------|---------------|----------------|
| haiku_1tool | 21/21 (100%) | 21/21 (100%) | 2.0 |
| haiku_5tools | 21/21 (100%) | 21/21 (100%) | 2.2 |
| haiku_10tools | 21/21 (100%) | 21/21 (100%) | 1.8 |
| haiku_20tools | 21/21 (100%) | **18/21 (86%)** | 2.3 |
| sonnet_1tool | 21/21 (100%) | 21/21 (100%) | 1.7 |
| sonnet_5tools | 21/21 (100%) | 21/21 (100%) | 1.3 |
| sonnet_10tools | 21/21 (100%) | 21/21 (100%) | 1.3 |
| sonnet_20tools | 21/21 (100%) | 21/21 (100%) | 1.3 |

(T2 excluded — expected answer was wrong in experiment definition)

---

## Key Findings

### 1. Both models are highly resilient to distractor tools
Neither model wastes tool calls on distractors. Average tool usage stays
at 1.3-2.3 regardless of whether 1 or 20 tools are available.

### 2. Haiku shows slight degradation at 20 tools
haiku_20tools dropped to 86% on T3 (CSV line counting) — it counted the
header row, resulting in 11 instead of 10. This happened in 3/21 trials.
Sonnet was unaffected at 20 tools.

### 3. No "Chekhov's gun" effect observed
Contrary to the published finding, neither model compulsively uses available
tools. This may be because Claude's tool-use training specifically addresses
this failure mode, or because our tasks are simple enough that the correct
tool choice is obvious.

---

## Limitation

Tasks were simple (single Bash command). The distractor effect might be
stronger on ambiguous tasks where multiple tools could plausibly apply.
