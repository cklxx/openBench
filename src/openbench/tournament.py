"""TournamentRunner — N-way round-robin tournaments among AgentConfigs."""

from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timezone

import anyio

from .runner import ExperimentRunner
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

    def __init__(self) -> None:
        self._runner = ExperimentRunner()

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
        pair_results: list[ExperimentResult] = []

        for a, b in pairs:
            exp = Experiment(
                name=f"{config.name}__{a.name}_vs_{b.name}",
                description=config.description,
                diff=DiffSpec(
                    field="allowed_tools",
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
            result = self._runner.run(exp)
            pair_results.append(result)

        ranking = self._rank(config.configs, pair_results)
        finished_at = datetime.now(timezone.utc).isoformat()

        return TournamentResult(
            tournament=config,
            pairs=pair_results,
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
        """Count average output length as proxy score; caller should use evaluator for real scores."""
        # Build a win-count map using a simple heuristic: longer output = better
        # (real scoring requires AutoEvaluator, which is async and expensive here)
        scores: dict[str, list[float]] = {c.name: [] for c in configs}

        for result in pair_results:
            avg_a = sum(len(t.output) for t in result.trials_a) / max(len(result.trials_a), 1)
            avg_b = sum(len(t.output) for t in result.trials_b) / max(len(result.trials_b), 1)
            total = avg_a + avg_b
            if total > 0:
                scores[result.experiment.agent_a.name].append(avg_a / total * 100)
                scores[result.experiment.agent_b.name].append(avg_b / total * 100)
            else:
                scores[result.experiment.agent_a.name].append(50.0)
                scores[result.experiment.agent_b.name].append(50.0)

        # Build config lookup by name
        config_map = {c.name: c for c in configs}

        ranking = [
            (config_map[name], sum(s) / max(len(s), 1))
            for name, s in scores.items()
            if name in config_map
        ]
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking
