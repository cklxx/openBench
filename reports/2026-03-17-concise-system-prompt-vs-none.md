# Experiment: concise_system_prompt_vs_none

**Date:** 2026-03-17
**Run ID:** `14321c42-c23c-47f6-b52d-44331fef71a8`
**Duration:** ~54s (16:54:40 → 16:55:34 UTC)

## Hypothesis

An explicit conciseness-focused system prompt reduces token usage while maintaining answer quality compared to no system prompt.

## Setup

| | Agent A (baseline) | Agent B (variant_v1) |
|--|--|--|
| **System Prompt** | *(none)* | "You are a concise Q&A assistant. Answer in as few words as possible while remaining accurate and complete. Use short sentences. No preamble, no filler phrases, no repetition of the question. If a single word or number suffices, give only that." |
| **Model** | claude-haiku-4-5 | claude-haiku-4-5 |
| **Max Turns** | 2 | 2 |
| **Tools** | none | none |

**Tasks (5):**
1. What is the capital of Australia?
2. Explain the difference between TCP and UDP in networking.
3. A store sells apples for $1.50 each. If I buy 7 apples and pay with a $20 bill, how much change do I get?
4. What are three common causes of a Python KeyError exception?
5. Who wrote the novel '1984' and in what year was it published?

**Diff field:** `system_prompt`

## Result

**Winner: B**

The concise system prompt successfully reduced verbosity across all task types while maintaining accuracy. Agent B consistently delivered shorter, more direct answers without sacrificing completeness.

## Next Experiment

Test whether format-type-specific rules (one sentence for facts, bullets for technical questions, minimal steps for math) further improve the score beyond generic conciseness instruction.
