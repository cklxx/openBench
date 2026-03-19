"""Tests for TournamentRunner."""
from __future__ import annotations

import pytest

from openbench.types import AgentConfig, TournamentConfig, TournamentResult


def make_config(name: str) -> AgentConfig:
    return AgentConfig(name=name, model="claude-haiku-4-5")


def make_tournament(n_configs: int = 3) -> TournamentConfig:
    return TournamentConfig(
        name="test_tournament",
        description="Test tournament",
        configs=[make_config(f"agent_{i}") for i in range(n_configs)],
        tasks=["Say hello.", "What is 2+2?"],
    )


def test_n_less_than_2_raises_value_error() -> None:
    from openbench.tournament import TournamentRunner

    config = TournamentConfig(
        name="bad",
        description="bad",
        configs=[make_config("a")],
        tasks=["hello"],
    )
    runner = TournamentRunner()
    with pytest.raises(ValueError, match="≥2"):
        runner.run(config, confirm=False)


def test_n3_generates_3_pairs() -> None:
    """N=3 configs should produce C(3,2)=3 pairs."""
    import itertools
    from openbench.tournament import TournamentRunner

    configs = [make_config(f"a{i}") for i in range(3)]
    pairs = list(itertools.combinations(configs, 2))
    assert len(pairs) == 3


def test_tournament_config_n_pairs_formula() -> None:
    """Verify pair count formula for various N."""
    import itertools
    for n in range(2, 6):
        configs = [make_config(f"c{i}") for i in range(n)]
        expected = n * (n - 1) // 2
        actual = len(list(itertools.combinations(configs, 2)))
        assert actual == expected, f"N={n}: expected {expected}, got {actual}"


def test_estimated_cost_formula() -> None:
    from openbench.tournament import TournamentRunner

    config = make_tournament(n_configs=4)
    runner = TournamentRunner()
    cost = runner.estimated_cost(config)
    # 4 configs → 6 pairs, 2 tasks, 1 sample, 2 agents each trial
    expected = 6 * 2 * 1 * 2 * 0.002
    assert abs(cost - expected) < 1e-9


def test_tournament_result_dataclass() -> None:
    """TournamentResult fields are accessible."""
    from openbench.types import ExperimentResult, Experiment, DiffSpec

    agent_a = make_config("a")
    agent_b = make_config("b")
    config = make_tournament(n_configs=2)

    exp = Experiment(
        name="t__a_vs_b",
        description="test",
        diff=DiffSpec(field="allowed_tools", description="a vs b"),
        agent_a=agent_a,
        agent_b=agent_b,
        tasks=["hello"],
    )
    pair = ExperimentResult(
        experiment=exp,
        trials_a=[],
        trials_b=[],
        run_id="rid",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:01:00Z",
    )
    result = TournamentResult(
        tournament=config,
        pairs=[pair],
        ranking=[(agent_a, 60.0), (agent_b, 40.0)],
        run_id="tournament-run-id",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:02:00Z",
    )
    assert result.run_id == "tournament-run-id"
    assert len(result.pairs) == 1
    assert result.ranking[0][0].name == "a"
    assert result.ranking[0][1] == 60.0
