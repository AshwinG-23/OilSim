import pytest
from config.params import SCENARIOS, STRATEGIES
from experiments.runner import ExperimentRunner


def test_runner_produces_results_for_all_combinations():
    runner = ExperimentRunner(
        scenarios=['no_disruption', 'short_conflict'],
        strategies=['cost_focused'],
        num_replications=2,
        duration_hours=5 * 24,   # 5 days for speed
    )
    results = runner.run()
    assert len(results) == 2 * 1 * 2   # 2 scenarios × 1 strategy × 2 reps


def test_runner_result_has_required_fields():
    runner = ExperimentRunner(
        scenarios=['no_disruption'],
        strategies=['cost_focused'],
        num_replications=1,
        duration_hours=3 * 24,
    )
    results = runner.run()
    r = results[0]
    assert 'scenario' in r
    assert 'strategy' in r
    assert 'replication' in r
    assert 'shortage_hours' in r
    assert 'total_cost' in r


def test_runner_uses_different_seeds_per_replication():
    runner = ExperimentRunner(
        scenarios=['no_disruption'],
        strategies=['cost_focused'],
        num_replications=3,
        duration_hours=2 * 24,
    )
    results = runner.run()
    seeds = [r['seed'] for r in results]
    assert len(set(seeds)) == 3   # all different seeds
