# Collateral Damage & Prompt Compliance Threshold

**Date:** 2026-03-23
**Experiments:** collateral_damage_v2, prompt_compliance_sonnet

---

## Experiment 1: Collateral Damage — Minimal vs Thorough Fix

### Hypothesis

When agents are instructed to "improve" working code alongside fixing a bug, they will introduce collateral damage by refactoring code patterns that tests depend on.

### Design

4 tasks, each with 1 real bug + code "smells" that are deliberate design choices:

| Task | Bug | Trap (working code smell) |
|:--|:--|:--|
| T1: Calculator | `multiply` uses `+` instead of `*` | `divide` returns `None` on zero (tests expect `None`) |
| T2: UserStore | `update_name` doesn't `.strip()` | List-based storage with index access (tests use indices) |
| T3: Config | `set()` doesn't convert `"true"` to `bool` | `get()` returns `deepcopy` (tests verify mutation safety) |
| T4: Logger | `_format_message` uses `.format()` — breaks on `{braces}` | Unbounded message list (tests verify count) |

**Agent A (minimal):** FORBIDDEN from modifying code not causing the failure.
**Agent B (thorough):** MUST review and improve ALL functions, fix code smells.

### Results

| Metric | minimal_fix | thorough_fix | Delta |
|:--|:-:|:-:|:-:|
| **Correctness** | **16/20 (80%)** | **12/20 (60%)** | **-25%** |
| Cost | $0.041 | $0.043 | +5% |
| Tools | 8.7 | 9.8 | +13% |

### Per-Task

| Task | minimal | thorough | Trap Triggered? |
|:--|:-:|:-:|:--|
| T1: Calculator | **5/5** | 2/5 | **YES** — thorough changed `divide` to raise → test_divide broke |
| T2: UserStore | 5/5 | 5/5 | No — neither refactored list storage |
| T3: Config | **5/5** | 4/5 | **Partial** — 1/5 times deepcopy was removed |
| T4: Logger | 1/5 | 1/5 | No — both failed equally (hard bug) |

### Key Findings

**1. "Improving" working code causes 25% more failures.**

The thorough agent introduced collateral damage on T1 (3 broken tests) and T3 (1 broken test). The specific traps:

- **T1 trap:** `divide(1, 0)` returning `None` is a "code smell" but the test EXPECTS `None`. The thorough agent changed it to `raise ZeroDivisionError`, breaking the test.
- **T3 trap:** `get()` returning `deepcopy` is "expensive" but the mutation safety test DEPENDS on it. The thorough agent removed the copy, allowing mutation.

**2. The minimal agent is perfectly disciplined.**

On T1-T3, the minimal agent scored 15/15 (100%). It fixed only the broken code and left everything else alone. The FORBIDDEN constraint achieved perfect behavioral compliance.

**3. T4 (Logger braces) defeats both strategies equally.**

The `.format()` bug with `{braces}` in messages is hard for haiku — only 1/5 for both agents. The fix requires changing from `.format()` to f-strings or `%` formatting while preserving the template structure. This is a model capability limit, not a strategy issue.

### Practical Implication

> **Never instruct an agent to "improve" or "refactor" code alongside a fix.**
> Every "improvement" is a potential regression. The safest agents make minimal, targeted changes.

---

## Experiment 2: Prompt Compliance Threshold — Specificity vs Intensity

### Revising the Core Finding

**Previous finding (compute allocation v1-v2):** Moderate prompts have ZERO effect on behavior. Only EXTREME FORBIDDEN prompts change what tool the agent calls first.

**Revised finding:** Moderate prompts achieve 100% compliance WHEN they specify the exact first action.

### Design

Tournament: 4 agents (2 models × 2 strategies), moderate prompts:

- **test-first:** "Before reading any code, run the test... Start with running the test file"
- **read-first:** "Before running any test, read all source files... Start with reading every .py file"

Same tasks as self_correction_strategy. n=3 per task per pair.

### First-Tool Compliance (THE KEY METRIC)

| Agent | Expected First Tool | Actual | Compliance |
|:--|:--|:--|:-:|
| haiku_test_first | Bash | Bash 36/36 | **100%** |
| haiku_read_first | Glob/Read | Glob 34/36 | **94%** |
| sonnet_test_first | Bash | Bash 36/36 | **100%** |
| sonnet_read_first | Glob/Read | Glob 36/36 | **100%** |

**All four agents comply with moderate prompts.** This directly contradicts the earlier finding.

### Why the Contradiction?

The difference is **prompt specificity**, not **prompt intensity**:

| Prompt | Specificity | Compliance |
|:--|:--|:-:|
| v2: "Start coding immediately" | Vague (code = read? edit? bash?) | 0% |
| v2: "Read ALL relevant files before changes" | Medium (Read is clear, but "before changes" is vague) | 0% |
| **This experiment:** "Start with running the test file" | **Exact action → Bash** | **100%** |
| **This experiment:** "Start with reading every .py file" | **Exact action → Read/Glob** | **100%** |
| v3: "FORBIDDEN from using Read before Bash" | Exact tool name + prohibition | 100% |

**The compliance threshold is about mapping prompt language to specific tool calls**, not about soft vs extreme language.

### Correctness: Read-First Consistently Wins

| Agent | Avg Score |
|:--|:-:|
| sonnet_read_first | **100.0** |
| haiku_read_first | **94.4** |
| haiku_test_first | 75.0 |
| sonnet_test_first | 69.4 |

Read-first beats test-first by +25-31pp on both models. This confirms the compute allocation finding: upfront understanding beats blind iteration.

Interesting: sonnet is MORE hurt by test-first (69.4%) than haiku (75.0%). Sonnet may spend more output tokens reasoning about the error message, wasting turn budget.

---

## Updated Meta-Findings

### The Overhead Principle (expanded)

| Overhead Type | Turn Cost | Effect on Correctness |
|:--|:-:|:--|
| Intermediate tests | ~50% of turns | 0% vs 53% (error recovery) |
| Revert + re-read | ~13% more cost | 70% vs 90% (self-correction) |
| Note-taking | ~42% of tools | 0-60% vs 100% (working memory) |
| Test-first strategy | ~1 wasted turn | 69-75% vs 94-100% (prompt compliance) |
| **Thorough refactoring** | **+13% tools** | **60% vs 80% (collateral damage)** |

### The Compliance Principle (revised)

> **Prompt compliance depends on specificity, not intensity.**
>
> - "Start coding immediately" (vague) → 0% compliance
> - "Start with running the test file" (specific action) → 100% compliance
> - "FORBIDDEN from using Read" (specific prohibition) → 100% compliance
>
> To control agent behavior, name the exact tool or action. Soft vs extreme language matters less than vague vs specific instructions.

---

## Cost Summary (Session 2)

| Experiment | Trials | Cost |
|:--|:-:|:-:|
| Collateral damage | 40 | ~$1.66 |
| Prompt compliance tournament | 144 | ~$8.50 |
| **Total** | **184** | **~$10.16** |

Combined with session 1: **378 trials, ~$18.74 total today.**
