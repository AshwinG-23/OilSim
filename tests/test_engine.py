import pytest
from config.params import SCENARIOS
from simulation.engine import SimulationEngine


def test_engine_runs_without_error():
    engine = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    results = engine.run(duration_hours=10 * 24)
    assert results is not None


def test_no_disruption_no_shortage():
    engine = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    results = engine.run(duration_hours=60 * 24)
    assert results['shortage_hours'] == 0


def test_results_have_expected_keys():
    engine = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    results = engine.run(duration_hours=10 * 24)
    for key in ('shortage_hours', 'total_cost', 'avg_cost_per_bbl',
                'demand_fulfillment_rate', 'total_barrels_imported'):
        assert key in results, f"Missing key: {key}"


def test_cost_increases_under_disruption():
    normal = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    r_normal = normal.run(duration_hours=100 * 24)

    disrupted = SimulationEngine(SCENARIOS['short_conflict'], 'cost_focused', seed=42)
    r_disrupted = disrupted.run(duration_hours=100 * 24)

    assert r_disrupted['avg_cost_per_bbl'] >= r_normal['avg_cost_per_bbl']


def test_resilient_strategy_fewer_shortages_under_long_war():
    cost_eng  = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    resil_eng = SimulationEngine(SCENARIOS['long_war'], 'resilient',    seed=42)

    r_cost  = cost_eng.run(duration_hours=200 * 24)
    r_resil = resil_eng.run(duration_hours=200 * 24)

    assert r_resil['shortage_hours'] <= r_cost['shortage_hours']


def test_spr_reduces_shortage():
    engine_with = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    engine_with.spr.level = 39_000_000
    r_with = engine_with.run(200 * 24)

    engine_without = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    engine_without.spr.level = 0
    r_without = engine_without.run(200 * 24)

    assert r_with['shortage_hours'] <= r_without['shortage_hours']
