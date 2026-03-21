# Experiment Report: Workflow Optimization — TDD, Few-Shot, Scratchpad

**Date:** 2026-03-21
**Three experiments testing workflow changes on the same model (haiku)**

---

## Experiment 1: TDD Workflow (6 tasks × n=3)

**Hypothesis:** Writing tests before implementation forces better spec understanding
(TDFlow reported +27.8% on SWE-Bench with human-written tests).

| Metric | implement_first | TDD |
|--------|----------------|-----|
| Correctness | **18/18 (100%)** | 17/18 (94%) |
| Avg latency | **69s** | 81s (+16%) |
| Avg cost | **$0.076** | $0.086 (+15%) |
| Avg turns | **9.4** | 10.3 (+9%) |

**Finding:** TDD does NOT help when the agent writes its own tests. The TDFlow
paper's gains came from human-written tests (high-quality specifications). When
the agent writes tests, they reflect the agent's own understanding — writing them
first doesn't force better understanding, it just adds overhead.

---

## Experiment 2: Few-Shot Tool Examples (6 tasks × n=3)

**Hypothesis:** Showing 2 worked examples of good tool-use sequences improves
agent behavior vs instructions alone (LearnAct showed +168% on GUI tasks).

| Metric | instructions_only | with_examples |
|--------|------------------|---------------|
| Correctness | 14/18 (78%) | **15/18 (83%)** |
| Avg tokens | 3,425 | **3,216** (-6%) |
| Avg tools | 8.5 | 8.6 |

### Per-Task Detail

| Task | instructions | with_examples | Notes |
|------|-------------|--------------|-------|
| T1: missing return | 3/3 | 3/3 | Both trivial |
| T2: wrong operator | 3/3 | 3/3 | Both trivial |
| T3: dict mutation | 3/3 | 3/3 | Both handle well |
| T4: double encoding | 0/3 | 0/3 | Genuinely hard — neither solves |
| T5: recursive check | 2/3 | **3/3** | Examples helped (+1) |
| T6: error propagation | 3/3 | 3/3 | Both handle well |

**Finding:** +5% from few-shot examples. Modest but consistent. The gain
comes from T5 (tree balance recursive check), the hardest task. Examples anchor
the "read → understand → precise edit" pattern more reliably for complex bugs.
T4 (URL double-encoding) remains unsolved by both — the bug requires understanding
that `%20` in input should NOT be re-encoded, which is a semantic insight
examples don't help with.

---

## Experiment 3: Scratchpad Working Memory (1 multi-step task × n=5)

**Hypothesis:** An explicit scratchpad file for tracking plan, findings, and state
improves coherence on long multi-step tasks.

| Metric | no_scratchpad | with_scratchpad |
|--------|--------------|-----------------|
| Correctness | **5/5 (100%)** | 5/5 (100%) |
| Avg turns | **34** | 49 (+44%) |
| Avg tool calls | **15.4** | 19.4 (+26%) |
| Avg cost | **$0.060** | $0.091 (+51%) |
| Scratchpad used? | N/A | **5/5 yes** |

**Finding:** Scratchpad adds pure overhead with zero quality gain on this task
(6-step investigation + fix + feature add). The agent's context window handles
15-20 tool calls without "forgetting." The scratchpad consumes 4-5 extra tool
calls (create, write, read, update) that contribute nothing to the task.

**When scratchpad might help:** Tasks requiring 50+ tool calls or 100K+ context
tokens, where the context window starts to degrade. Our task didn't reach
that threshold.

---

## Summary: Workflow Optimization ROI

| Technique | Expected (from literature) | Measured | Verdict |
|-----------|--------------------------|----------|---------|
| TDD | +15-30% (TDFlow) | **-6%** (worse) | Not useful with self-written tests |
| Few-shot examples | +10-20% (LearnAct) | **+5%** | Modest, consistent, worth doing |
| Scratchpad memory | +10-20% (hypothesized) | **0%** (+51% cost) | Pure overhead at this scale |
| System prompt + workflow | +10-15% (Anthropic) | **+15%** (scaffold experiment) | **The big win** |

**The literature overstates workflow optimization gains for well-scaffolded agents.**
The large gains (TDFlow +27.8%, LearnAct +168%) come from either human-provided
test specs or weak baseline models/domains. For Claude haiku with claude-agent-sdk,
the baseline is already strong enough that marginal workflow tweaks yield
diminishing returns. The one intervention that reliably helps is a good system
prompt with workflow instructions — which is just basic scaffold quality.
