# Experiment Report: ModelRouter Validation (n=5, 240 total trials)

**Date:** 2026-03-19
**Run ID:** b02ef1a6-1e89-4b2d-9434-01f47885c7db
**Experiment:** `model_router_validation` (3-way tournament, 8 tasks × 5 samples × 3 pairs)
**Total trials:** 240 (80 per agent across all pairs)

---

## Setup

3-way round-robin: fixed haiku vs fixed sonnet vs auto ModelRouter.

| Agent | Model | Routing |
|-------|-------|---------|
| haiku_fixed | claude-haiku-4-5 | Always haiku |
| sonnet_fixed | claude-sonnet-4-6 | Always sonnet |
| auto_router | ModelRouter | haiku for simple, sonnet for complex |

ModelRouter signals: difficulty tag, token threshold (200), keyword detection.

8 tasks: 4 simple (arithmetic, factual) + 4 complex (coding, analysis, SQL, algorithms).

---

## Results (n=5 per task per pair, 80 trials per agent)

### Per-Task Correctness

| Task | Difficulty | haiku | sonnet | auto_router | Router picked |
|------|-----------|-------|--------|-------------|---------------|
| 17×23 | easy | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | haiku |
| Capital of France | easy | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | haiku |
| °F→°C | easy | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | haiku |
| GCD(48,36) | easy | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | haiku |
| Bracket balancing | medium | **9/10 (90%)** | 8/10 (80%) | 8/10 (80%) | sonnet* |
| Data analysis | medium | **1/10 (10%)** | 0/10 (0%) | 0/10 (0%) | sonnet* |
| SQL queries | hard | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | sonnet |
| Palindrome substr | hard | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | sonnet |

*Router correctly routes to sonnet via keyword detection ("implement", "analyze").

### Aggregate

| Agent | Correct/Total | Correctness | Avg Cost/Trial | Total Cost |
|-------|--------------|-------------|----------------|------------|
| **haiku_fixed** | **70/80** | **87.5%** | **$0.0107** | **$0.86** |
| sonnet_fixed | 68/80 | 85.0% | $0.0182 | $1.45 |
| auto_router | 68/80 | 85.0% | $0.0146 | $1.17 |

### Cost Savings

| Comparison | Cost Difference |
|-----------|----------------|
| auto_router vs sonnet_fixed | **-19.5%** ($1.17 vs $1.45) |
| auto_router vs haiku_fixed | +35.8% ($1.17 vs $0.86) |
| haiku_fixed vs sonnet_fixed | **-40.8%** ($0.86 vs $1.45) |

---

## Statistical Significance (McNemar's paired test)

| Comparison | Agree | A wins | B wins | Significant? |
|-----------|-------|--------|--------|-------------|
| haiku vs auto_router | 76/80 | 3 | 1 | **No** (p > 0.30) |
| sonnet vs auto_router | 76/80 | 2 | 2 | **No** (exactly tied) |
| haiku vs sonnet | 76/80 | 3 | 1 | **No** (p > 0.30) |

**No pair shows statistically significant correctness difference.** The 2.5 percentage point gaps (87.5% vs 85.0%) are driven by 2-3 discordant trials out of 80 — well within random noise.

---

## Key Findings

### 1. All three agents are statistically equivalent on correctness
87.5% vs 85.0% vs 85.0% — the differences are NOT significant. With 80 trials per agent, the 95% confidence interval on 85% is ±8%, so these are indistinguishable.

### 2. T6 (data analysis) is broken for everyone
0-10% correctness across all agents. The check_fn (`"2245" in output`) is too rigid — agents compute the right total but format it differently. This is a check_fn bug, not a model bug. Excluding T6, all agents are ~96% correct.

### 3. Auto-router saves 20% vs sonnet-only with same quality
auto_router and sonnet_fixed have identical 85.0% correctness, but auto_router costs $1.17 vs $1.45 (−19.5%). The savings come from routing simple tasks to haiku.

### 4. Haiku-only is cheapest but the quality gap isn't real
haiku_fixed appears 2.5 pts better (87.5% vs 85.0%), but this is NOT significant. Given equal quality, haiku at $0.86 total is the cheapest option.

### 5. The router works correctly
- Simple tasks (T1-T4): routed to haiku → all 100% correct, at haiku prices
- Complex tasks (T5-T8): routed to sonnet → same quality as sonnet_fixed
- Cost is between haiku-only and sonnet-only as designed

---

## Verdict

**All three approaches produce statistically equivalent quality (85-88%).** The choice is purely about cost:

| Strategy | When to use | Cost |
|----------|------------|------|
| haiku_fixed | Budget-constrained, tasks not too complex | $0.011/trial |
| auto_router | Mixed workload, want cost savings on simple tasks | $0.015/trial |
| sonnet_fixed | Maximum consistency, cost not a concern | $0.018/trial |

**ModelRouter achieves its design goal**: same quality as sonnet at 20% lower cost by using haiku for simple tasks.

---

## Limitations

1. **Check_fn fragility** — T6 shows 0-10% correctness due to output format mismatch, not actual errors
2. **Task selection** — These 8 tasks may not represent real production workloads
3. **Single routing strategy** — Only tested token+keyword+difficulty routing; ML-based routing could do better
4. **No multi-turn tasks** — All tasks here are simple enough for both models; complex multi-turn tasks might show bigger model differences
