# Deep Dive: Task Decomposition & Memory Strategy

**Date:** 2026-03-23
**Experiments:** task_decomposition v1-v3, context_pressure_boundary, context_pressure_replace
**Informed by:** Agentless (UIUC), CodeCrash (NeurIPS 2025), JetBrains Complexity Trap, Chroma Context Rot

---

## Part 1: Task Decomposition — The Hint Accuracy Spectrum

### Full Results Across v1-v3

| Agent | Hints | Accuracy | max_turns | Correctness | Avg Cost | Avg Tools |
|:--|:--|:--|:-:|:-:|:-:|:-:|
| discovery | None | N/A | 12 | **0/5** | $0.059 | 15.6 |
| discovery | None | N/A | 20 | **5/5** | $0.064 | 18.4 |
| guided_correct | 4/4 correct | 100% | 12 | **5/5** | $0.049 | 15.4 |
| guided_correct | 4/4 correct | 100% | 20 | **5/5** | $0.038 | 15.4 |
| guided_partial | 3/4 correct | 75% | 20 | **5/5** | $0.074 | 19.2 |

### Key Finding 1: Wrong Hints Don't Kill Correctness — They Kill Efficiency

| Metric | guided_correct | guided_partial | Delta |
|:--|:-:|:-:|:-:|
| Correctness | 5/5 | 5/5 | **0%** |
| Avg tools | 15.4 | 19.2 | **+25%** |
| Avg turns | 28 | 42 | **+51%** |
| Avg cost | $0.038 | $0.074 | **+93%** |

The agent CAN overcome a wrong hint. It reads the code, realizes the hint is wrong, and finds the real bug. But this recovery costs ~14 extra turns — essentially the same overhead as full discovery.

### Key Finding 2: The Efficiency Spectrum

```
Discovery      ████████████████████████ $0.064  (18.4 tools, finds all 4)
Partial hints  ██████████████████████████████ $0.074  (19.2 tools, recovers from wrong hint)
Correct hints  ██████████████ $0.038  (15.4 tools, executes directly)
```

- **Correct hints save 40% vs discovery** — eliminates discovery overhead
- **Partial hints cost ~15% MORE than discovery** — the wrong hint is a net negative, even with 3 correct hints
- **Under tight turns (12), only correct hints succeed** — discovery and partial can't finish

### Key Finding 3: Anchoring vs Efficiency Tradeoff

This connects three experiments:

| Guidance Type | Accuracy | Completeness | Effect on Correctness | Effect on Cost |
|:--|:--|:--|:--|:--|
| Vague file hints (context v4) | Low | Partial | **-37-42%** | Unknown |
| 3 correct + 1 wrong | High (75%) | Complete | **0%** | **+93%** |
| 4/4 correct | High (100%) | Complete | **0%** | **-38%** |
| No guidance (discovery) | N/A | N/A | Baseline | Baseline |

**The anchoring tax:** Each wrong hint costs ~14 turns of recovery — roughly the same as discovering that bug from scratch. The correct hints still save time on the other 3 bugs, but 1 wrong hint nearly wipes out the savings.

**Implication for agent builders:** Only provide hints you're confident about. A 75% accurate bug list is barely better than no list at all. A 100% accurate list saves 40% cost.

### Connection to Literature

| Source | Claim | Our Result |
|:--|:--|:--|
| **Agentless** (UIUC) | Simple pipelines > autonomous agents | Confirmed: guided > discovery at same turns |
| **CodeCrash** (NeurIPS 2025) | Wrong comments degrade reasoning by 23% | Confirmed: wrong hint costs +93% in overhead |
| **ADaPT** (Allen AI) | As-needed decomposition > upfront planning | Nuanced: upfront is better IF accurate |
| **Anchoring bias studies** | LLMs retain ~37% of anchor difference | Confirmed: wrong hint adds ~51% more turns |

---

## Part 2: Memory Strategy — The Constraint Tax

### Full Results Across All Memory Experiments (15-file codebase)

| Strategy | Constraint Level | Correctness | Avg Cost | Avg Tools |
|:--|:--|:-:|:-:|:-:|
| **Implicit (no notes)** | None | **5/5 (100%)** | **$0.066** | **17.2** |
| Additive scratchpad (relaxed) | Medium | **5/5 (100%)** | $0.109 | 22.8 |
| Additive scratchpad (strict) | High (FORBIDDEN) | **1/5 (20%)** | $0.117 | 24.0 |
| Replace scratchpad | High (no re-read) | **2/5 (40%)** | $0.113 | 24.0 |

### Key Finding 4: It's Not Notes That Hurt — It's Rigid Constraints

The difference between 5/5 and 1/5 isn't "notes vs no notes" — it's **constraint strictness**:

| Prompt Constraint | Correctness |
|:--|:-:|
| "Take notes if you want" (implicit, no constraint) | 100% |
| "MUST update notes, CAN re-read files" (relaxed) | 100% |
| "FORBIDDEN from editing without recent notes update" (strict) | **20%** |
| "FORBIDDEN from re-reading summarized files" (replace) | **40%** |

The strict FORBIDDEN constraints eat turns:
- Strict: 4/5 trials hit max_turns (stop=tool_use)
- Replace: 3/5 trials hit max_turns
- Relaxed: 0/5 hit max_turns
- Implicit: 0/5 hit max_turns

### Key Finding 5: Replace (Observation Masking) Hurts Code Fixing

The JetBrains "Complexity Trap" paper found observation masking matches summarization for SWE-bench. But our replace scratchpad (which simulates observation masking) scored **2/5 vs additive's 5/5**.

**Why the difference:**
- JetBrains masks **tool outputs** (verbose error messages, test logs)
- Our replace masks **source files** (code the agent needs to edit)
- The `Edit` tool requires **exact string matching** — the agent needs to see the real code
- Summaries in notes lose the precision needed for `Edit(old_string=..., new_string=...)`

**Lesson:** Observation masking works for **outputs** but not for **source code**. You can hide old error messages, but you can't hide the files the agent needs to modify.

### Key Finding 6: Even Relaxed Notes Are Pure Overhead at 15 Files

| Metric | Implicit | Relaxed Notes | Delta |
|:--|:-:|:-:|:-:|
| Correctness | 100% | 100% | 0% |
| Cost | $0.066 | $0.109 | **+65%** |
| Tools | 17.2 | 22.8 | **+33%** |
| Latency | 37.3s | 72.7s | **+95%** |

Both achieve 100%, but notes add 65% cost with zero correctness benefit. The context window handles 15 files without needing external memory.

### Updated Scaling Table

| Files | Implicit | Strict Scratch | Relaxed Scratch | Replace Scratch |
|:--|:-:|:-:|:-:|:-:|
| 3 (12 turns) | 100% | 0% | — | — |
| 3 (20 turns) | 100% | 65% | — | — |
| 8 (25 turns) | 100% | 60% | — | — |
| **15 (25 turns)** | **100%** | **20%** | **100%** | **40%** |

Relaxed notes match implicit on correctness at 15 files — but at 65% higher cost. The break-even point where notes HELP is still beyond our test range.

### Connection to Literature

| Source | Claim | Our Result |
|:--|:--|:--|
| **JetBrains Complexity Trap** | Observation masking ≈ summarization | Doesn't apply to source files — Edit needs exact code |
| **Chroma Context Rot** | Performance degrades with input length | Not observed at 15-file scale (implicit=100%) |
| **Lost in the Middle** | Middle of context gets less attention | Implicit still 100% — possibly not enough files to trigger |
| **LIGHT framework** | Multi-tier memory helps | Maybe, but forced single-tier scratchpad hurts |

---

## Unified Principles (Updated)

### Principle 7: Guidance Quality = Accuracy × Completeness

| Quality | Effect | Example |
|:--|:--|:--|
| Accurate + Complete (100%) | **-38% cost** | "Fix these 4 specific bugs: [exact list]" |
| Accurate but Incomplete | Neutral | "There's a bug in config.py" |
| Inaccurate (even partially) | **+93% cost** | "3 correct bugs + 1 wrong diagnosis" |
| Vague hints | **-37-42% correctness** | "This file might have the bug" |

> **Rule: Only provide guidance you're confident is correct. Partial-accuracy guidance is worse than no guidance.**

### Principle 8: Constraints Are the Real Overhead

The scratchpad debate is actually a constraints debate:

| What the agent is told | Correctness | Cost overhead |
|:--|:-:|:-:|
| "Do whatever you want" (implicit) | 100% | 0% |
| "SHOULD take notes" (relaxed) | 100% | +65% |
| "MUST take notes before editing" (strict) | 20% | +77% |
| "CAN'T re-read files" (replace) | 40% | +71% |

> **Rule: Any MUST/FORBIDDEN constraint on the agent's process consumes turns. Prefer suggestions over mandates. Let the agent decide its own process.**

---

## Cost Summary

| Experiment | Trials | Cost |
|:--|:-:|:-:|
| Task decomposition v1 (12 turns) | 10 | ~$0.54 |
| Task decomposition v2 (20 turns) | 10 | ~$0.52 |
| Task decomposition v3 (hint accuracy) | 10 | ~$0.56 |
| Context pressure boundary (15 files) | 10 | ~$0.91 |
| Context pressure replace | 10 | ~$1.11 |
| **Total today** | **50** | **~$3.64** |

**Running total:** 4,824+ trials, ~$84 USD
