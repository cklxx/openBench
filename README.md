<h1 align="center">OpenBench</h1>

<p align="center">
  <strong>A/B testing platform for Claude agents.</strong><br/>
  Automates the plan → run → evaluate → repeat loop to find optimal agent configurations.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/SDK-claude--agent--sdk-blueviolet.svg" alt="claude-agent-sdk"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"/>
</p>

---

## What is OpenBench?

An experimentation platform that treats Claude agent configurations as hypotheses and tests them with statistical rigor. Define two agent configs that differ in **exactly one variable**, run them against the same tasks, and get a verdict backed by data — not vibes.

Over 7 days of dogfooding: **~200 experiment groups, ~6,000 trials, ~$110 USD** across math, coding, reasoning, and security tasks.

---

## Preview

<table>
<tr>
<td width="50%">

**AutoResearch Loop** — generates hypotheses, runs A/B tests, iterates automatically

<img src="docs/images/example0.png" alt="AutoResearch running" width="100%"/>
</td>
<td width="50%">

**Research Complete** — key findings, best config, and next steps

<img src="docs/images/example1.png" alt="Research results" width="100%"/>
</td>
</tr>
</table>

---

## Quick Start

```bash
# Install
pip install -e .

# Run a single A/B experiment
openbench run experiments/quicktest_model.py

# Automated research from a natural language goal
openbench research "Find the best system prompt for a concise Q&A assistant" --max-iter 3

# N-way tournament
openbench tournament experiments/verified_math_tournament.py --yes

# Browse results interactively
openbench tui
```

Requires `claude-agent-sdk` (uses Claude Max subscription — no API key needed).

---

## How It Works

```
You: "Find the optimal turn budget for coding tasks"
        ↓
  Planner (LLM)           — generates A/B hypothesis & experiment config
        ↓
  Runner                   — executes both agents in isolated temp dirs
        │                     collects: output, tokens, cost, tool calls, traces
        ↓
  Evaluator                — LLM-as-judge + optional ground-truth check_fn
        ↓
  Comparator               — statistical comparison, winner selection
        ↓
  Loop (if auto-research)  — winner becomes baseline, next hypothesis proposed
```

---

## Key Concepts

| Concept | Description |
|---|---|
| **Experiment** | Two agent configs (`agent_a` vs `agent_b`) differing in exactly **one** variable |
| **DiffSpec** | The single variable being tested: `system_prompt`, `model`, `max_turns`, `allowed_tools`, … |
| **TaskItem** | A task with optional `expected_answer` + `check_fn` for objective correctness |
| **ModelRouter** | Auto-select haiku vs sonnet per-task based on complexity signals |
| **TournamentConfig** | N-way round-robin comparison with correctness-based ranking |
| **ResearchProgram** | Natural language objective that drives automated experiment loops |

---

## CLI

| Command | Description |
|---|---|
| `openbench run <file>` | Run a single A/B experiment |
| `openbench tournament <file>` | Run N-way round-robin tournament |
| `openbench research "<goal>"` | Auto-generate & run experiments from a goal |
| `openbench list` | List all experiment results |
| `openbench compare <name>` | Side-by-side comparison report |
| `openbench show <name>` | Show experiment details |
| `openbench runs <name>` | List individual trial runs |
| `openbench lineage <name>` | Show experiment lineage chain |
| `openbench save-program <name>` | Save a research program config |
| `openbench tui` | Interactive history browser (Textual TUI) |

---

## Model Selection Guide

Benchmark results from 240+ trials across math, coding, and reasoning tasks:

| Strategy | Best For | Correctness | Cost/Trial |
|----------|---------|-------------|------------|
| `"claude-haiku-4-5"` | Budget-constrained, known-simple tasks | 87.5% | ~$0.011 |
| `ModelRouter()` | **Mixed workloads, unknown complexity** | 85.0% | ~$0.015 |
| `"claude-sonnet-4-6"` | Maximum efficiency, complex coding/analysis | 85.0% | ~$0.018 |

> The 2.5% correctness gap is NOT statistically significant (McNemar's test, p > 0.30, n=80 paired trials). All three are equivalent on quality — the real difference is cost and efficiency.

### ModelRouter — Automatic Model Selection

```python
from openbench.types import AgentConfig, ModelRouter

agent = AgentConfig(
    name="auto",
    model=ModelRouter(
        default="claude-haiku-4-5",   # Simple tasks (5× lower cost)
        upgrade="claude-sonnet-4-6",  # Complex tasks (2× fewer tokens)
        threshold_tokens=200,
    ),
    allowed_tools=["Read", "Bash", "Glob"],
    max_turns=20,
)
```

| Signal | Condition | Routes to |
|--------|-----------|-----------|
| **Difficulty tag** | `TaskItem(difficulty="hard")` | sonnet |
| **Token count** | Estimated input ≥ 200 tokens | sonnet |
| **Keywords** | "implement", "debug", "analyze", "build", … | sonnet |
| **Default** | None of the above | haiku |

---

## Key Findings

From 200+ experiments on this platform:

| Finding | Recommendation |
|---------|----------------|
| haiku + Bash = sonnet on math | Give haiku tools instead of upgrading models |
| Sonnet uses 66% fewer tokens on coding | Use sonnet for code tasks if efficiency matters |
| max_turns=20 is optimal (100% success) | Set `max_turns = 2× expected tool calls` |
| Structured prompts can hurt | Prefer minimal prompts over heavy templates |
| Turn budget matters more than model choice | Optimize turns before spending on bigger models |
| Posture ("be careful") > procedure (step lists) | Attitude-based prompts outperform rigid instructions |

Full experiment write-ups → [`reports/`](reports/)

---

## Architecture

```
src/openbench/
├── types.py              # AgentConfig, TaskItem, ModelRouter, TournamentConfig
├── runner.py             # ExperimentRunner — orchestrates agent execution
├── evaluator.py          # LLM-as-judge with optional ground truth
├── compare.py            # Rich terminal comparison reports
├── tournament.py         # N-way round-robin tournaments
├── planner.py            # ExperimentPlanner — NL goal → A/B experiment
├── program.py            # ResearchProgram — NL objective for auto-research
├── autoloop.py           # AutoResearchLoop — main orchestration loop
├── isolation.py          # Environment isolation for agent runs
├── metrics.py            # Metrics collection and calculation
├── storage.py            # JSONL + JSON persistence
├── cli.py                # Typer CLI
├── _sdk_call.py          # Thin wrapper for LLM calls via SDK
├── _tui.py               # TUI helpers (progress bars, callbacks)
├── _history_tui.py       # Interactive Textual TUI for browsing results
└── _utils.py             # Shared internal utilities

experiments/              # 80+ experiment definitions
programs/                 # Saved ResearchProgram configs
results/                  # Raw trial data (JSONL + metadata)
reports/                  # 45+ experiment reports
tests/                    # pytest test suite
docs/                     # Guides, memory, plans
```

---

## License

[MIT](LICENSE) © 2025 cklxx
