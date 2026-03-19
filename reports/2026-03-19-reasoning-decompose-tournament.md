# Experiment Report: Decomposing the SkillConfig Reasoning Gain

**Date:** 2026-03-19  
**Experiment:** `reasoning_decompose_3way` (Tournament, 3 pairs × 8 tasks)  
**Model:** claude-haiku-4-5 | **Evaluator:** claude-sonnet-4-6  
**Follows up:** `cognitive_traps_skill_vs_baseline` (Exp 1)

---

## Hypothesis (from Exp 1 judge)

The +4.2 pt reasoning quality gain from the full SkillConfig scaffold may come
entirely from "naming the wrong intuition" — not from the full structured template.
Test three agents to decompose the effect:

| Agent | System Prompt |
|-------|--------------|
| **baseline** | None |
| **minimal_trap** | "Before solving, state the most common wrong intuitive answer and explain in one phrase why it fails. Then solve." |
| **full_scaffold** | Full RESTATE / INTUITION CHECK / WORK / VERIFY / ANSWER template (SkillConfig) |

---

## Tasks (8)

Mix of easy (classic CRT, benchmark-known) and harder novel problems:

| # | Difficulty | Problem | Correct Answer |
|---|-----------|---------|---------------|
| T1 | EASY | Bat & ball | 5¢ |
| T2 | MEDIUM | Harmonic mean / avg speed trap | 40 mph |
| T3 | MEDIUM | Sock drawer pigeonhole | 3 |
| T4 | MEDIUM | Hat removal paradox | 50 |
| T5 | HARD | Marble probability with replacement | 13/25 |
| T6 | HARD | Two-children Tuesday-girl problem | 13/27 |
| T7 | HARD | Stock compound asymmetry (+50%/-50%×2) | 43.75% lower |
| T8 | HARD | QC consensus-required failure rate | 27.10% |

---

## Results

### Correctness
**All three agents: 8/8 correct.** haiku-4-5 is robust on all tasks including
the harder problems (13/27 Tuesday-girl, compound stock asymmetry). Prompting
does not improve correctness here.

### LLM Judge Quality Scores (claude-sonnet-4-6, n=16 per agent)

| Agent | Quality | task_completion | accuracy | conciseness |
|-------|---------|----------------|----------|-------------|
| baseline | 80.5 | 93.2 | 100.0 | 85.0 |
| **minimal_trap** | **96.0** | **99.4** | **100.0** | 86.8 |
| full_scaffold | 94.1 | 97.9 | 100.0 | 79.9 |

### Pair-wise Results

| Pair | Winner | Score delta |
|------|--------|-------------|
| baseline vs minimal_trap | **minimal_trap** | 96.4 vs 80.0 (+16.4) |
| baseline vs full_scaffold | **full_scaffold** | 93.6 vs 81.0 (+12.6) |
| minimal_trap vs full_scaffold | **tie** | 95.6 vs 94.5 (+1.1) |

---

## Key Findings

### 1. The judge's hypothesis was RIGHT
minimal_trap (one-sentence prompt) captures **the same quality gain** as the full
SkillConfig scaffold. The pair minimal_trap vs full_scaffold is a statistical tie
(+1.1 pts, effectively noise). The expensive structured template adds no marginal
reasoning quality over simply naming the wrong intuition.

### 2. Both prompted agents massively outperform baseline (+15 pts)
The gap is driven by `task_completion` (+6 pts) — prompted agents are more
explicit and complete in their explanations. Baseline often reaches the correct
answer with minimal reasoning shown.

### 3. full_scaffold pays a conciseness penalty
full_scaffold: 79.9 conciseness vs minimal_trap: 86.8 (+6.9 pts for minimal).
The RESTATE/INTUITION-CHECK/WORK/VERIFY headers add structure but also verbosity
that the judge penalises. minimal_trap avoids this overhead.

### 4. Correctness is not the discriminating variable
All agents 8/8 correct, including hard novel problems (Tuesday-girl 13/27,
compound stock 43.75%). haiku-4-5 appears to handle these correctly regardless
of prompting. To find correctness differences, tasks would need to be genuinely
out-of-distribution.

---

## Verdict

**minimal_trap dominates on all metrics:**
- Same quality gain as full_scaffold (+15 vs baseline)
- Better conciseness (-6.9 pts penalty avoided)
- Simpler to maintain (1 sentence vs multi-step template)
- Faster and cheaper (less output tokens)

The minimal prompt: *"Before solving, state the most common wrong intuitive answer
and explain in one phrase why it fails. Then solve."*

---

## Next Experiments

Three natural follow-ups:

1. **Correctness gap**: Design genuinely novel problems (not in training data)
   where all agents don't score 8/8. Multi-step algebra with made-up constants,
   novel combinatorics, or problems requiring tool use (code execution).

2. **minimal_trap across domains**: Does the trap-naming pattern generalise beyond
   math? Test on logical syllogisms, causal inference, code debugging.

3. **Tool A/B for code debugging**: Agent with Bash (can execute code) vs
   Read-only (must reason from source). Tasks: finding bugs in setup_files Python.
   This tests a completely different hypothesis where tool access actually changes
   what's computable.
