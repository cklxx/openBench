# Experiment Report: Cost-Normalized Retry — haiku×N vs sonnet×N

**Date:** 2026-03-20
**Experiment:** `cost_normalized_retry` (8 tasks × n=5)
**Total trials:** 80

---

## Research Question

Haiku is ~3× cheaper than Sonnet. If you spend the same budget, is N haiku
attempts better than N sonnet attempts? Nobody has published cost-normalized
pass rates for coding agents.

---

## Results

| Metric | haiku_retry | sonnet_single |
|--------|-------------|---------------|
| Per-trial correctness | **31/40 (78%)** | 25/40 (62%) |
| Pass@5 (any success in 5 tries) | **7/8 tasks** | 6/8 tasks |
| Avg cost/trial | **$0.031** | $0.069 |
| Total cost | **$1.25** | $2.78 |

### Per-Task Breakdown

| Task | haiku (n=5) | sonnet (n=5) |
|------|-------------|-------------|
| T1: Avg salary by dept | 5/5 | 5/5 |
| T2: Config JSON edit | 5/5 | 5/5 |
| T3: Data analysis script | 5/5 | 3/5 |
| T4: Stable merge sort bug | 2/5 | 0/5 |
| T5: Report generation | 2/5 | 2/5 |
| T6: SQL schema generation | 5/5 | 5/5 |
| T7: Bootstrap statistics | 3/5 | 2/5 |
| T8: Linear regression from scratch | 4/5 | 3/5 |

---

## Key Findings

### 1. Haiku wins on both correctness AND cost
78% per-trial vs 62%. At half the cost. This is not a tradeoff — haiku
dominates on this task mix.

### 2. T4 (stable sort) is the biggest gap
Haiku 2/5 vs sonnet 0/5. The bug requires understanding sort stability
(changing `<` to `<=` in merge). Sonnet's failures are surprising — it
may be overthinking the problem.

### 3. Pass@5 converges
With 5 attempts, haiku covers 7/8 tasks vs sonnet 6/8. The only task
haiku can't reliably solve is T5 (report generation — format-sensitive
check_fn issue).

---

## Implications for Production

**For cost-sensitive deployments:**
- Use haiku with retry strategy (pass@3 or pass@5)
- Total cost < half of sonnet, higher success rate
- Only escalate to sonnet for tasks that fail all haiku attempts

**Cost per successful completion:**
- haiku: $1.25 / 31 successes = **$0.040/success**
- sonnet: $2.78 / 25 successes = $0.111/success
- haiku is **2.8× more cost-efficient per success**
