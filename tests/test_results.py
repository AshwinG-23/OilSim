import pytest
from analysis.results import ResultsAnalyzer

SAMPLE_RESULTS = [
    {'scenario': 'no_disruption', 'strategy': 'cost_focused', 'replication': 0,
     'shortage_hours': 0,   'total_cost': 5e9,   'avg_cost_per_bbl': 2.5,
     'demand_fulfillment_rate': 1.0, 'total_barrels_imported': 2e9},
    {'scenario': 'no_disruption', 'strategy': 'cost_focused', 'replication': 1,
     'shortage_hours': 0,   'total_cost': 5.1e9, 'avg_cost_per_bbl': 2.55,
     'demand_fulfillment_rate': 1.0, 'total_barrels_imported': 2e9},
    {'scenario': 'long_war',      'strategy': 'cost_focused', 'replication': 0,
     'shortage_hours': 120, 'total_cost': 7e9,   'avg_cost_per_bbl': 3.5,
     'demand_fulfillment_rate': 0.7, 'total_barrels_imported': 2e9},
    {'scenario': 'long_war',      'strategy': 'resilient',    'replication': 0,
     'shortage_hours': 20,  'total_cost': 8e9,   'avg_cost_per_bbl': 4.0,
     'demand_fulfillment_rate': 0.9, 'total_barrels_imported': 2e9},
]


def test_aggregate_returns_mean_shortage():
    ra = ResultsAnalyzer(SAMPLE_RESULTS)
    agg = ra.aggregate()
    nd_cf = agg[('no_disruption', 'cost_focused')]
    assert nd_cf['mean_shortage_hours'] == pytest.approx(0.0)


def test_aggregate_returns_mean_cost():
    ra = ResultsAnalyzer(SAMPLE_RESULTS)
    agg = ra.aggregate()
    nd_cf = agg[('no_disruption', 'cost_focused')]
    assert nd_cf['mean_total_cost'] == pytest.approx(5.05e9)


def test_best_strategy_per_scenario_by_shortage():
    ra = ResultsAnalyzer(SAMPLE_RESULTS)
    best = ra.best_strategy_per_scenario(metric='mean_shortage_hours', lower_is_better=True)
    assert best['long_war'] == 'resilient'


def test_to_csv_creates_file(tmp_path):
    ra = ResultsAnalyzer(SAMPLE_RESULTS)
    path = str(tmp_path / "results.csv")
    ra.to_csv(path)
    import os
    assert os.path.exists(path)
    with open(path) as f:
        lines = f.readlines()
    assert len(lines) > 1   # header + data rows


def test_print_summary_runs_without_error(capsys):
    ra = ResultsAnalyzer(SAMPLE_RESULTS)
    ra.print_summary()
    captured = capsys.readouterr()
    assert len(captured.out) > 0
