import pytest
from simulation.metrics import Metrics


def test_record_and_retrieve_inventory():
    m = Metrics()
    m.record_inventory(0, 50e6)
    m.record_inventory(24, 45e6)
    log = m.inventory_log
    assert len(log) == 2
    assert log[0]['inventory'] == 50e6


def test_record_cost():
    m = Metrics()
    m.record_cost(time=100, source='Gulf', barrels=2e6, cost_per_bbl=2.5)
    assert len(m.cost_log) == 1
    assert m.cost_log[0]['total_cost'] == pytest.approx(5e6)


def test_summary_total_cost():
    m = Metrics()
    m.record_cost(0, 'Gulf', 2e6, 2.5)
    m.record_cost(24, 'Russia', 2e6, 3.0)
    summary = m.compute_summary(total_sim_hours=4800)
    assert summary['total_cost'] == pytest.approx(11e6)


def test_summary_avg_cost_per_bbl():
    m = Metrics()
    m.record_cost(0, 'Gulf',   2e6, 2.5)   # 5M cost, 2M bbl
    m.record_cost(0, 'Africa', 2e6, 4.0)   # 8M cost, 2M bbl
    summary = m.compute_summary(total_sim_hours=4800)
    assert summary['avg_cost_per_bbl'] == pytest.approx(3.25)


def test_summary_shortage_hours():
    m = Metrics()
    m.record_shortage(10)
    m.record_shortage(11)
    summary = m.compute_summary(total_sim_hours=4800)
    assert summary['shortage_hours'] == 2


def test_summary_fulfillment_rate():
    m = Metrics()
    for h in range(10):
        m.record_shortage(h)
    summary = m.compute_summary(total_sim_hours=4800)
    rate = summary['demand_fulfillment_rate']
    assert 0.0 < rate < 1.0


def test_record_fleet_utilization():
    m = Metrics()
    m.record_fleet_utilization(time=0, in_use=15, total=25)
    assert m.fleet_log[0]['utilization'] == pytest.approx(15 / 25)
