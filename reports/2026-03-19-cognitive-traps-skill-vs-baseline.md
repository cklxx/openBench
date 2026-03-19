# Experiment Report: Cognitive Traps — SkillConfig Structured Reasoning vs Baseline

**Date:** 2026-03-19  
**Run ID:** b1121445-482f-4684-bdaa-aa8bcf409531  
**Experiment:** `cognitive_traps_skill_vs_baseline`  
**Model:** claude-haiku-4-5 | **Cost:** $0.10 (baseline) + $0.11 (trap_aware)

---

## Hypothesis

A `SkillConfig` enforcing explicit trap-checking (`RESTATE → INTUITION CHECK → WORK → VERIFY → ANSWER`) will outperform no-prompt on tasks where LLM intuition is systematically wrong — classical cognitive reflection test (CRT) and counterintuitive math problems.

---

## Tasks (7)

| # | Problem | Correct Answer | Common Wrong Intuition |
|---|---------|---------------|----------------------|
| T1 | Bat & ball ($1.10 total, bat $1 more) | **5¢** | 10¢ |
| T2 | Lily pads doubling, covers lake day 48 | **47 days** | 24 days |
| T3 | 5 machines, 5 min, 5 widgets → 100 machines, 100 widgets | **5 min** | 100 min |
| T4 | Monty Hall — switch probability | **2/3** | 1/2 |
| T5 | -20% then +20% vs original price | **4% lower** | same price |
| T6 | Extra rope to raise 1m above Earth equator | **6.28 m (2π)** | thousands of km |
| T7 | Simpson's paradox — hospital overall survival | **Hospital A (60% vs 42.7%)** | Hospital B (better per-category) |

---

## Results

### Correctness
Both agents answered all 7 questions correctly. **haiku-4-5 is already robust on classic CRT problems** — these are in training data.

### Reasoning Quality (LLM Judge: claude-sonnet-4-6)

| Task | Baseline | trap_aware | Winner |
|------|----------|------------|--------|
| T1 (bat & ball) | 80.0 | **96.0** | B +16 |
| T2 (lily pads) | 90.0 | **97.0** | B +7 |
| T3 (widgets) | 88.0 | **95.0** | B +7 |
| T4 (Monty Hall) | 95.0 | **96.0** | B +1 |
| T5 (jacket price) | **97.0** | 97.0 | tie |
| T6 (rope/Earth) | **97.0** | 95.0 | A +2 |
| T7 (Simpson's) | 96.0 | **97.0** | B +1 |
| **Average** | **91.9** | **96.1** | **B wins (+4.2 pts)** |

**Confidence: 0.69** — directional, not conclusive (n=7 tasks)

### Dimension Scores

| Dimension | Baseline | trap_aware | Delta |
|-----------|----------|------------|-------|
| accuracy | 100.0 | 99.0 | -1.0 |
| task_completion | 98.0 | 100.0 | +2.0 |
| conciseness | 86.7 | 85.3 | -1.4 |

The +4.2 quality delta comes from overall reasoning quality, not captured in standard dimensions — the judge weighted explicit trap-naming even though both were correct.

---

## Key Findings

1. **Correctness is not the discriminator** — haiku-4-5 solves all classic CRT problems without prompting. These are benchmark-contaminated.

2. **Reasoning quality does differ** (+4.2 pts). The SkillConfig gains most on bat-and-ball (T1: +16 pts): baseline solved correctly but never named the "10¢ intuition trap," making it less useful pedagogically.

3. **One reversal on T6** (rope/Earth): baseline scored 97 vs trap_aware's 95. The structured template added verbosity overhead where the baseline naturally explained the counterintuitive insight organically.

4. **trade-off confirmed**: trap_aware is slower (+49% latency), uses more tokens (+35%), costs more (+20%), for a +4.2 reasoning quality improvement.

---

## Judge Analysis

> "The +4.3 pt delta is driven almost entirely by Agent B's consistent, explicit naming of the cognitive trap before solving — the bat-and-ball task illustrates the gap most starkly (80 vs 96: Agent A solved correctly but never called out the '10-cent intuition'). The one reversal (rope-around-Earth: A=97, B=95) suggests Agent B's structured RESTATE/INTUITION-CHECK headers add mild verbosity overhead that can backfire when the baseline already explains the counterintuitive insight organically. At confidence=0.69 across only 7 tasks per agent, the result is directionally credible but not conclusive."

---

## Next Experiment (Judge Recommendation)

> Isolate whether the gain comes from **'name the trap explicitly' alone** versus the full structured template. Test Agent C: a minimal system prompt — `"Before solving, state the most common wrong intuitive answer and explain why it fails"` — no imposed RESTATE/WORK/VERIFY scaffolding. Tests whether pedagogical value is in trap-flagging, not verbosity.

This is a clean, testable hypothesis. Should run next.

---

## Conclusion

**trap_aware wins** on reasoning quality (96.1 vs 91.9, +4.2 pts, winner=b, confidence=0.69). The SkillConfig structured template meaningfully improves the *explainability* of correct answers — important for teaching contexts. It does not improve correctness on these well-known problems.

For harder, less benchmark-contaminated problems, the correctness gap should also emerge. Recommended follow-up: test on novel combinatorics / probability problems not in standard CRT benchmarks.
