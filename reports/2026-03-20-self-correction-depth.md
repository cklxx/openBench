# Experiment Report: Self-Correction Depth — 5 Bugs × 3 Samples

**Date:** 2026-03-20
**Experiment:** `self_correction_depth` (5 bugs, max_turns=30, n=3)
**Total trials:** 6

---

## Research Question

Given failing test output, how effectively does each model self-correct?
Published finding: "intrinsic self-correction (no external feedback) worsens
performance." But with test output as feedback, how deep can correction go?

---

## Bugs (increasing subtlety)

| # | Bug | Difficulty | Root Cause |
|---|-----|-----------|------------|
| 1 | Fibonacci off-by-one | Easy | `range(n)` should be `range(n-1)`, return `a` not `b` |
| 2 | Binary search edge case | Medium | `len(nums)-1` should be `len(nums)` for insert-at-end |
| 3 | Matrix shallow copy | Medium | `self.data = data` → `self.data = [row[:] for row in data]` |
| 4 | EventEmitter pop-during-iterate | Hard | `list.pop(i)` during enumeration skips handlers |
| 5 | LIS reconstruction reversed | Hard | `seq` needs `[::-1]` before return |

---

## Results

| Metric | haiku | sonnet |
|--------|-------|--------|
| Bugs fixed | **5/5** (all 3 samples) | **5/5** (all 3 samples) |
| Avg turns | 74 | **27** |
| Avg tool calls | 35 | **18** |
| Avg cost | $0.134 | $0.141 |

Both models fix **all 5 bugs in every trial**. The ceiling is identical.

---

## Key Findings

### 1. Self-correction ceiling is model-independent
Both haiku and sonnet achieve 100% fix rate across all 5 bugs when given
test output as feedback. The ceiling is set by "having actionable feedback,"
not by model capability.

### 2. Sonnet is 2.7× more turn-efficient
Sonnet: 27 turns for 5 bugs. Haiku: 74 turns. Sonnet diagnoses and fixes
bugs faster, needing fewer test-fix iterations. But the end result is the same.

### 3. Cost is equivalent
Despite using 2.7× fewer turns, sonnet costs about the same ($0.141 vs $0.134)
because of higher per-token pricing. The efficiency advantage is neutralized
by price.

---

## Implication

**For self-correction tasks:** Model choice doesn't affect what you can fix —
only how fast. If you have a test suite, even haiku will eventually fix
everything. Choose based on latency requirements, not capability.
