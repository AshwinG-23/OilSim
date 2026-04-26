import simpy
import pytest
from core.chokepoint import Chokepoint
from core.disruption import DisruptionEngine


def _setup(disruption_configs):
    env = simpy.Environment()
    cps = {
        'Hormuz':  Chokepoint(env, 'Hormuz',  capacity=10, base_transit_hours=48),
        'Red_Sea': Chokepoint(env, 'Red_Sea', capacity=8,  base_transit_hours=96),
    }
    de = DisruptionEngine(env, cps)
    de.schedule_disruptions(disruption_configs)
    return env, cps, de


def test_no_disruption_leaves_status_normal():
    env, cps, de = _setup([])
    env.run(until=100)
    assert cps['Hormuz'].status == 1.0


def test_disruption_fires_at_scheduled_time():
    cfg = [{'chokepoint': 'Hormuz', 'start_day': 1, 'duration_days': 5, 'severity': 0.5}]
    env, cps, de = _setup(cfg)
    env.run(until=23)   # just before 1 day = 24 h
    assert cps['Hormuz'].status == 1.0
    env.run(until=25)   # just after
    assert cps['Hormuz'].status == pytest.approx(0.5)


def test_disruption_restores_after_duration():
    cfg = [{'chokepoint': 'Hormuz', 'start_day': 1, 'duration_days': 2, 'severity': 0.5}]
    env, cps, de = _setup(cfg)
    env.run(until=24 + 48 + 1)   # 1 day start + 2 day duration + 1 h
    assert cps['Hormuz'].status == pytest.approx(1.0)


def test_multiple_chokepoints_disrupted():
    cfg = [
        {'chokepoint': 'Hormuz',  'start_day': 1, 'duration_days': 5, 'severity': 0.2},
        {'chokepoint': 'Red_Sea', 'start_day': 2, 'duration_days': 3, 'severity': 0.5},
    ]
    env, cps, de = _setup(cfg)
    env.run(until=3 * 24 + 1)   # after both have started
    assert cps['Hormuz'].status  == pytest.approx(0.2)
    assert cps['Red_Sea'].status == pytest.approx(0.5)


def test_event_log_records_start_and_end():
    cfg = [{'chokepoint': 'Hormuz', 'start_day': 1, 'duration_days': 1, 'severity': 0.5}]
    env, cps, de = _setup(cfg)
    env.run(until=24 + 24 + 1)
    log = de.get_event_log()
    assert len(log) == 2
    assert log[0]['event'] == 'start'
    assert log[1]['event'] == 'end'
