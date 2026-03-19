"""TournamentRunner — N-way round-robin tournaments among AgentConfigs."""

from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timezone

import anyio

from .runner import ExperimentRunner
from .storage import ResultStore
from .types import (
    AgentConfig,
    DiffSpec,
    Experiment,
    ExperimentResult,
    TournamentConfig,
    TournamentResult,
)


class TournamentRunner:
    """Run N configs head-to-head in a round-robin tournament.

    Usage::

        runner = TournamentRunner()
        result = runner.run(config, confirm=False)
    """

    def __init__(self, store: ResultStore | None = None) -> None:
        self._runner = ExperimentRunner()
        self._store = store or ResultStore()

    def estimated_cost(self, config: TournamentConfig) -> float:
        """Rough cost estimate in USD (assumes ~$0.002 per trial at Haiku pricing)."""
        n = len(config.configs)
        n_pairs = n * (n - 1) // 2
        return n_pairs * len(config.tasks) * config.num_samples * 2 * 0.002

    def run(self, config: TournamentConfig, confirm: bool = True) -> TournamentResult:
        """Run the tournament synchronously.

        Args:
            config: The tournament configuration (≥2 agent configs required).
            confirm: If True, print a cost estimate and ask the user to confirm.
        """
        if len(config.configs) < 2:
            raise ValueError("TournamentConfig requires ≥2 configs")
        if confirm:
            est = self.estimated_cost(config)
            n = len(config.configs)
            n_pairs = n * (n - 1) // 2
            print(
                f"\nTournament: {config.name}\n"
                f"  Configs: {n}  |  Pairs: {n_pairs}  |  Tasks: {len(config.tasks)}\n"
                f"  Estimated cost: ~${est:.4f} USD\n"
            )
            answer = input("Proceed? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                raise RuntimeError("Tournament aborted by user.")
        return anyio.run(self._run_async, config)

    async def _run_async(self, config: TournamentConfig) -> TournamentResult:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        pairs = list(itertools.combinations(config.configs, 2))
        pair_results: list[ExperimentResult | None] = [None] * len(pairs)

        async def _run_pair(idx: int, a: AgentConfig, b: AgentConfig) -> None:
            exp = Experiment(
                name=f"{config.name}__{a.name}_vs_{b.name}",
                description=config.description,
                diff=DiffSpec(
                    field="system_prompt",
                    description=f"{a.name} vs {b.name}",
                ),
                agent_a=a,
                agent_b=b,
                tasks=config.tasks,
                num_samples=config.num_samples,
                setup_files=config.setup_files,
                setup_script=config.setup_script,
                tags=config.tags + ["tournament", config.name],
            )
            # Use _run_async directly — we're already inside anyio.run()
            result = await self._runner._run_async(exp, None, None)
            pair_results[idx] = result
            # Auto-save each pair result to disk
            self._store.save_result(result)

        async with anyio.create_task_group() as tg:
            for idx, (a, b) in enumerate(pairs):
                tg.start_soon(_run_pair, idx, a, b)

        completed: list[ExperimentResult] = [r for r in pair_results if r is not None]
        ranking = self._rank(config.configs, completed)
        finished_at = datetime.now(timezone.utc).isoformat()

        return TournamentResult(
            tournament=config,
            pairs=completed,
            ranking=ranking,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
        )

    def _rank(
        self,
        configs: list[AgentConfig],
        pair_results: list[ExperimentResult],
    ) -> list[tuple[AgentConfig, float]]:
        """Rank agents by correctness (primary) then success rate (secondary).

        Scoring (per pair, per agent):
        - If correctness data available: % of trials objectively correct
        - Else: % of trials that succeeded (no error)
        Final score: average across all pairs the agent participated in.
        """
        scores: dict[str, list[float]] = {c.name: [] for c in configs}

        for result in pair_results:
            score_a = self._agent_score(result.trials_a)
            score_b = self._agent_score(result.trials_b)
            scores[result.experiment.agent_a.name].append(score_a)
            scores[result.experiment.agent_b.name].append(score_b)

        config_map = {c.name: c for c in configs}
        ranking = [
            (config_map[name], sum(s) / max(len(s), 1))
            for name, s in scores.items()
            if name in config_map
        ]
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    @staticmethod
    def _agent_score(trials: list) -> float:
        """Score an agent's trials: correctness if available, else success rate."""
        if not trials:
            return 0.0
        # Check if correctness data is available
        checked = [t for t in trials if t.correctness is not None]
        if checked:
            return sum(1 for t in checked if t.correctness) / len(checked) * 100
        # Fallback: success rate
        ok = sum(
            1 for t in trials
            if t.metrics.stop_reason != "error" and t.metrics.error is None
        )
        return ok / len(trials) * 100
