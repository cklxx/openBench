"""Core types for OpenBench A/B testing platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillConfig:
    """A named, versioned agent skill with its own system prompt and required tools."""

    name: str
    """Skill identifier, e.g. 'file_search_v2'."""

    version: str
    """Version string, e.g. '1.0.0' or '2024-03-19'."""

    description: str
    """Human-readable description of what this skill does."""

    system_prompt: str
    """The system prompt that implements this skill."""

    required_tools: list[str] = field(default_factory=list)
    """Tool names required by this skill."""


@dataclass
class ModelRouter:
    """Dynamic model selection based on task complexity.

    When used as AgentConfig.model, the runner resolves the actual model
    at runtime using multiple signals:
    1. Estimated input tokens (prompt + system_prompt)
    2. Task difficulty tag (if TaskItem is used)
    3. Keyword-based complexity detection

    Based on benchmarks: haiku matches sonnet on simple tasks but sonnet
    is 2× more efficient (fewer turns/tokens) on complex ones.
    """

    default: str = "claude-haiku-4-5"
    """Model to use for low-complexity tasks."""

    upgrade: str = "claude-sonnet-4-6"
    """Model to use for high-complexity tasks."""

    threshold_tokens: int = 200
    """Estimated input tokens above which we consider upgrading.
    The actual decision also considers keywords and difficulty."""

    upgrade_keywords: tuple[str, ...] = (
        "implement", "write a function", "write a class", "build",
        "refactor", "debug", "analyze", "design",
    )
    """Keywords in the task that suggest higher complexity."""

    upgrade_difficulties: tuple[str, ...] = ("hard", "very_hard")
    """TaskItem.difficulty values that trigger upgrade."""

    def resolve(
        self,
        estimated_tokens: int,
        difficulty: str | None = None,
        task_text: str = "",
    ) -> str:
        """Return the model to use given task complexity signals."""
        # Signal 1: explicit difficulty tag
        if difficulty and difficulty in self.upgrade_difficulties:
            return self.upgrade

        # Signal 2: token count above threshold
        if estimated_tokens >= self.threshold_tokens:
            return self.upgrade

        # Signal 3: keyword detection in prompt
        lower = task_text.lower()
        if any(kw in lower for kw in self.upgrade_keywords):
            return self.upgrade

        return self.default

    def __str__(self) -> str:
        return f"auto({self.default}|{self.upgrade}@{self.threshold_tokens}tok)"


@dataclass
class AgentConfig:
    """Configuration for one agent in an A/B test."""

    name: str
    """Human-readable name, e.g. 'agent_a' or 'verbose_prompt'."""

    model: str | ModelRouter
    """Claude model identifier (e.g. 'claude-opus-4-6') or a ModelRouter
    for automatic per-task model selection."""

    system_prompt: str | SkillConfig | None = None
    """Optional system prompt override. Can be a plain string or a SkillConfig."""

    allowed_tools: list[str] = field(default_factory=list)
    """Tool names the agent may use, e.g. ['Read', 'Bash', 'Glob']."""

    max_turns: int = 10
    """Maximum number of agentic turns."""

    extra_options: dict[str, Any] = field(default_factory=dict)
    """Additional ClaudeAgentOptions fields passed as kwargs."""

    mcp_servers: list[dict] | None = None
    """Optional MCP server configurations to pass to the SDK."""


@dataclass
class TaskItem:
    """A task with optional metadata for objective evaluation."""

    prompt: str
    """The task prompt sent to the agent."""

    expected: str | None = None
    """Reference answer for objective correctness checking.
    When provided, the evaluator uses it to score accuracy objectively."""

    difficulty: str | None = None
    """Optional difficulty tag: 'easy', 'medium', 'hard'."""

    tags: list[str] = field(default_factory=list)
    """Task-level tags for grouping and analysis."""

    check_fn: str | None = None
    """Optional Python expression for programmatic correctness checking.
    The expression receives `output` (str) and should return bool.
    Example: '"5" in output and "cents" in output.lower()'"""


@dataclass
class DiffSpec:
    """Describes the single variable being tested between agent_a and agent_b."""

    field: str
    """The field name that differs: 'system_prompt', 'model', 'tools', etc."""

    description: str
    """Human-readable description of the difference."""


@dataclass
class Experiment:
    """Defines a complete A/B experiment."""

    name: str
    """Unique experiment name (used as directory name for results)."""

    description: str
    """What this experiment is measuring."""

    diff: DiffSpec
    """The ONE thing that differs between agent_a and agent_b."""

    agent_a: AgentConfig
    """Control agent."""

    agent_b: AgentConfig
    """Variant agent."""

    tasks: list[str | TaskItem]
    """List of prompts / tasks to run through both agents.
    Can be plain strings or TaskItem objects with reference answers."""

    tags: list[str] = field(default_factory=list)
    """Arbitrary tags for filtering/searching experiments."""

    num_samples: int = 1
    """Number of independent trials per (agent, task) pair.
    Use ≥3 to compute pass@k metrics. Higher = more reliable estimates, higher cost."""

    setup_files: dict[str, str] = field(default_factory=dict)
    """Files to write into each trial's isolated working directory before the agent starts.
    Keys are relative paths (e.g. 'problem.py'), values are file contents.
    Paths must be relative and must not contain '..' (directory traversal is rejected)."""

    setup_script: str | None = None
    """Optional shell command run in the workdir after setup_files are written
    but before the agent starts. Use for environment setup, e.g. 'pip install -q pytest'.
    A non-zero exit code causes the trial to be recorded as an error."""


@dataclass
class TrialMetrics:
    """Performance metrics for a single agent run on a single task."""

    latency_ms: float
    """Wall-clock time from first token request to final result, in milliseconds."""

    total_tokens: int
    """Total tokens used (input + output). May be estimated if SDK doesn't expose exact counts."""

    input_tokens: int
    """Input / prompt tokens. May be estimated."""

    output_tokens: int
    """Output / completion tokens. May be estimated."""

    estimated_cost_usd: float
    """Estimated cost in USD based on model pricing."""

    num_tool_calls: int
    """Total number of tool-use invocations."""

    tool_call_names: list[str]
    """Ordered list of tool names that were called."""

    num_turns: int
    """Number of assistant turns (AssistantMessage objects received)."""

    stop_reason: str
    """How the run ended: 'end_turn', 'max_turns', 'error', etc."""

    error: str | None
    """Error message if the run failed, otherwise None."""


@dataclass
class TrialResult:
    """Full result for one agent on one task."""

    trial_id: str
    """UUID identifying this specific trial."""

    experiment_name: str
    """Name of the parent experiment."""

    agent_name: str
    """Name of the agent config that ran (e.g. 'agent_a')."""

    task: str
    """The input prompt / task text."""

    task_index: int
    """Zero-based index of this task in the experiment's task list.
    Multiple trials with the same task_index are different samples for pass@k."""

    output: str
    """Final text result produced by the agent."""

    metrics: TrialMetrics
    """Collected performance metrics."""

    timestamp: str
    """ISO-8601 timestamp of when this trial started."""

    workdir: str
    """Temporary working directory that was used for isolation (already deleted)."""

    agent_input: dict = field(default_factory=dict)
    """Snapshot of the inputs given to the agent: system_prompt, task, model, max_turns."""

    full_trace: list[dict] = field(default_factory=list)
    """Complete execution trace.  Each entry is either an assistant turn::

        {"turn": int, "content": [<block_dict>, ...], "usage": {"input_tokens": int, "output_tokens": int}}

    or the final result::

        {"result": str, "stop_reason": str}
    """

    correctness: bool | None = None
    """Objective correctness check result. None if no expected answer provided."""

    expected_answer: str | None = None
    """The reference answer used for correctness checking (if provided)."""

    difficulty: str | None = None
    """Task difficulty tag from TaskItem, if provided."""


@dataclass
class ExperimentResult:
    """Complete results for an entire experiment run."""

    experiment: Experiment
    """The experiment definition (snapshot at run time)."""

    trials_a: list[TrialResult]
    """All trial results for agent_a. With num_samples>1, contains num_samples entries per task."""

    trials_b: list[TrialResult]
    """All trial results for agent_b. With num_samples>1, contains num_samples entries per task."""

    run_id: str
    """UUID for this specific experiment run."""

    started_at: str
    """ISO-8601 timestamp when the run started."""

    finished_at: str
    """ISO-8601 timestamp when the run finished."""


@dataclass
class TournamentConfig:
    """Defines an N-way round-robin tournament among multiple agent configs."""

    name: str
    """Unique tournament name."""

    description: str
    """What this tournament is measuring."""

    configs: list[AgentConfig]
    """≥2 agent configs to pit against each other."""

    tasks: list[str | TaskItem]
    """List of prompts / tasks to run through all agents."""

    num_samples: int = 1
    """Number of independent trials per (agent, task) pair."""

    setup_files: dict[str, str] = field(default_factory=dict)
    """Files to write into each trial's isolated working directory."""

    setup_script: str | None = None
    """Optional shell command run before each agent starts."""

    tags: list[str] = field(default_factory=list)
    """Arbitrary tags for filtering."""


@dataclass
class TournamentResult:
    """Complete results for an N-way tournament."""

    tournament: TournamentConfig
    """The tournament configuration."""

    pairs: list[ExperimentResult]
    """One ExperimentResult per head-to-head pair."""

    ranking: list[tuple[AgentConfig, float]]
    """(config, avg_score) sorted descending by score."""

    run_id: str
    """UUID for this specific tournament run."""

    started_at: str
    """ISO-8601 timestamp when the tournament started."""

    finished_at: str
    """ISO-8601 timestamp when the tournament finished."""
