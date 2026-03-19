# Experiment Report: minimal_trap Cross-Domain Generalization

**Date:** 2026-03-19
**Run ID:** f8fad631-49a7-494b-8847-5fb548432471
**Experiment:** `minimal_trap_cross_domain`
**Model:** claude-haiku-4-5 | **Cost:** $0.094 (baseline) + $0.121 (minimal_trap)
**Follows up:** `reasoning_decompose_3way` — does the one-liner generalize beyond math?

---

## Hypothesis

The minimal_trap prompt ("state the most common wrong intuitive answer and explain
why it fails, then solve") generalized across math/cognitive traps. Does it transfer
to non-math domains: logic, causal inference, code debugging, and statistics?

---

## Tasks (10)

| # | Domain | Problem |
|---|--------|---------|
| T1 | Logic | Affirming the consequent — all dogs are pets? |
| T2 | Logic | Denying the antecedent — ground not wet? |
| T3 | Logic | Illicit conversion — flowers vs roses |
| T4 | Causal | Survivorship bias — WWII bomber armor |
| T5 | Causal | Confounding variables — breakfast and test scores |
| T6 | Causal | Regression to the mean — new coach blamed |
| T7 | Code | Duplicate pair detection with sets |
| T8 | Code | Triangle validation — or vs and |
| T9 | Stats | Base rate neglect — disease test |
| T10 | Stats | Simpson's paradox — hiring |

---

## Results

### Correctness
Both agents answered all 10 questions correctly across all four domains.

### Surface Metrics

| Metric | baseline | minimal_trap | Delta |
|--------|----------|-------------|-------|
| Latency (avg) | 11.54s | 13.84s | +19.9% |
| Tokens (avg) | 1,268 | 1,800 | +41.9% |
| Cost (avg) | $0.00939 | $0.01206 | +28.3% |
| Successes | 10/10 | 10/10 | 0 |

### Quality Assessment (manual review of outputs)

Both agents produced high-quality, structurally similar answers:

- **Logic (T1-T3)**: Both correctly identified the fallacies (affirming the consequent,
  denying the antecedent, illicit conversion). Baseline's explanations were equally
  clear and often more concise.

- **Causal (T4-T6)**: Both immediately recognized survivorship bias, confounding
  variables, and regression to the mean. These are well-known patterns — haiku-4-5
  handles them without prompting.

- **Code (T7-T8)**: Both correctly diagnosed the bugs. The minimal_trap prefix
  ("common wrong answer is...") added no value for code debugging — there is no
  "intuitive wrong answer" for code bugs.

- **Statistics (T9-T10)**: Both correctly computed the Bayesian posterior (~1%) and
  explained Simpson's paradox with examples. T10 was the only task where minimal_trap
  used notably more tokens (8,669 vs 3,888) for a more elaborate example, but both
  arrived at the same correct explanation.

---

## Key Findings

### 1. minimal_trap does NOT generalize to non-math domains
The "name the wrong intuition" pattern was effective for cognitive trap math problems
(+15 pts in the decompose tournament). On logic, causal inference, code debugging,
and statistics, it provides **no measurable quality improvement** while adding
+42% token overhead.

### 2. The pattern only helps where there IS a competing intuition
Math traps have a compelling wrong answer (10¢, 24 days, 100 minutes). For logical
syllogisms, survivorship bias, or code bugs, there's no single "intuitive wrong
answer" that the model would fall for — so asking it to name one just generates
filler text.

### 3. haiku-4-5 is strong on well-known reasoning patterns
All tested domains (logical fallacies, survivorship bias, regression to the mean,
base rate neglect, Simpson's paradox, Python closure/mutation bugs) are extensively
covered in training data. The model handles them correctly without any prompting.

### 4. Domain-specific prompting needed for code
The minimal_trap prompt was awkwardly applied to code debugging tasks. A code-specific
prompt (e.g., "trace the execution step by step") would be more natural than
"name the wrong intuition."

---

## Verdict

**baseline wins.** Same quality, 20% faster, 28% cheaper. The minimal_trap
one-liner is domain-specific to cognitive trap problems — it does not generalize
as a universal metacognitive strategy.

---

## Next Experiments

1. **Domain-specific prompts**: Instead of one universal prompt, test domain-tailored
   prompts (e.g., "trace execution" for code, "check the study design" for causal).

2. **Harder tasks**: Find problems where haiku-4-5 actually fails without prompting.
   Current tasks are all in-distribution — the model knows them all.

3. **Tool access for code**: The code bugs were solvable by reading alone. Test with
   bugs that require execution to observe (race conditions, timing issues, environment-
   dependent behavior).
