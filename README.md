# OpenBench

A/B testing platform for Claude agents. Automates the **plan → run → evaluate → repeat** loop to find optimal agent configurations.

## Preview

| Example 1 | Example 2 |
|:---------:|:---------:|
| ![Example 1](docs/images/example0.png) | ![Example 2](docs/images/example1.png) |

## Install

```bash
pip install -e .
```

Requires `claude-agent-sdk` (uses Claude Max subscription — no API key needed).

## Quick Start

```bash
# Run a manually written experiment
openbench run experiments/quicktest_model.py

# Automated research from a natural language goal
openbench research "Find the best system prompt for a concise Q&A assistant" --max-iter 3

# N-way tournament
openbench tournament experiments/verified_math_tournament.py --yes

# View results
openbench list
openbench compare <experiment-name>
```

## How It Works

1. **Plan** — LLM generates an A/B experiment testing one hypothesis (e.g., system prompt variant)
2. **Run** — Both agents execute every task in isolated temp directories; metrics collected
3. **Evaluate** — LLM judge scores each output on quality, accuracy, conciseness
4. **Repeat** — Winner becomes the new baseline; next hypothesis is proposed

## Key Concepts

- **Experiment**: Two agent configs (`agent_a` vs `agent_b`) differing in exactly **one** variable
- **DiffSpec**: The single variable being tested (`system_prompt`, `model`, `max_turns`, etc.)
- **TaskItem**: Task with optional expected answer + `check_fn` for objective correctness checking
- **ModelRouter**: Auto-select haiku vs sonnet per-task based on complexity
- **TournamentConfig**: N-way round-robin comparison with correctness-based ranking
- Results persist to `results/<experiment-name>/` as JSONL + metadata JSON
- Human-readable reports in `reports/`

## Model Selection Guide

Benchmark results from 240+ trials across math, coding, and reasoning tasks:

### When to Use Each Strategy

| Strategy | Best For | Correctness | Cost/Trial |
|----------|---------|-------------|------------|
| `"claude-haiku-4-5"` | Budget-constrained, known-simple tasks | 87.5% | ~$0.011 |
| `ModelRouter()` (default) | **Mixed workloads, unknown complexity** | 85.0% | ~$0.015 |
| `"claude-sonnet-4-6"` | Maximum efficiency, complex coding/analysis | 85.0% | ~$0.018 |

> **Statistical note**: The 2.5% correctness gap between strategies is NOT significant
> (McNemar's test, p > 0.30, n=80 paired trials). All three are equivalent on quality.
> The real difference is cost and efficiency.

### ModelRouter — Automatic Model Selection

```python
from openbench.types import AgentConfig, ModelRouter

agent = AgentConfig(
    name="auto",
    model=ModelRouter(
        default="claude-haiku-4-5",   # Simple tasks (cheap, 5× lower cost)
        upgrade="claude-sonnet-4-6",  # Complex tasks (2× fewer tokens/turns)
        threshold_tokens=200,         # Token count trigger
    ),
    allowed_tools=["Read", "Bash", "Glob"],
    max_turns=20,
)
```

The router selects a model per-task using three signals (in priority order):

| Signal | Condition | Routes to |
|--------|-----------|-----------|
| **Difficulty tag** | `TaskItem(difficulty="hard")` | sonnet |
| **Token count** | Estimated input ≥ 200 tokens | sonnet |
| **Keywords** | Prompt contains "implement", "debug", "analyze", "build", etc. | sonnet |
| **Default** | None of the above | haiku |

### Recommended Defaults

```python
# Most common case: let the router decide
model=ModelRouter()

# Tight budget, simple Q&A / math
model="claude-haiku-4-5"

# Complex coding, multi-file implementation
model="claude-sonnet-4-6"
```

### Benchmark-Backed Guidelines

From experiments on this platform:

| Finding | Source | Recommendation |
|---------|--------|----------------|
| haiku + Bash = sonnet on math | `verified_math_tournament` | Give haiku tools instead of upgrading to sonnet |
| Sonnet uses 66% fewer tokens on coding | `coding_challenge` | Use sonnet for code tasks if efficiency matters |
| Both models solve 5/5 standard algorithms | `coding_challenge` | Use haiku if correctness is all you need |
| max_turns=20 is optimal (100% success) | `turn_budget_scaling` | Set `max_turns = 2× expected tool calls` |
| Structured prompts can hurt | `code_fix_verifiable` | Prefer minimal prompts over heavy templates |

See `reports/` for full experiment write-ups.

## Project Structure

```
src/openbench/     # Core library
  types.py         # AgentConfig, TaskItem, ModelRouter, TournamentConfig
  runner.py        # ExperimentRunner — orchestrates agent execution
  evaluator.py     # LLM-as-judge with optional ground truth
  compare.py       # Rich terminal comparison reports
  tournament.py    # N-way round-robin tournaments
  storage.py       # JSONL + JSON persistence
  cli.py           # Typer CLI
experiments/       # Experiment definitions (Python files)
programs/          # Saved ResearchProgram JSON configs
results/           # Raw trial data (JSONL)
reports/           # Human-readable experiment reports
docs/              # Guides, memory, plans
```
