import simpy
import pytest
from core.port import Port
from core.spr import SPR


def _make_env_port(initial_inv=5000, hourly_demand=100, max_inv=50000):
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inv, max_inv, hourly_demand)
    return env, port


def test_spr_releases_when_below_threshold():
    env, port = _make_env_port(initial_inv=500, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=8_000, daily_release_rate=2400)
    # port inventory starts at 500, threshold=1000 → SPR should release
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=2)
    assert port.inventory > 500   # SPR added to port


def test_spr_does_not_release_above_threshold():
    env, port = _make_env_port(initial_inv=5000, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=8_000, daily_release_rate=2400)
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=5)
    assert spr.total_released == 0


def test_spr_level_decreases_on_release():
    env, port = _make_env_port(initial_inv=100, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=8_000, daily_release_rate=2400)
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=5)
    assert spr.level < 8_000


def test_spr_stops_releasing_when_inventory_recovers():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=0, max_inventory=50_000, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=8_000, daily_release_rate=24_000)
    # Inventory starts at 0, threshold 1000; once filled above threshold it should stop
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=5)
    # After a few hours at 1000 bbl/hour release, port should be above threshold
    assert not spr.is_releasing


def test_spr_cannot_go_negative():
    env, port = _make_env_port(initial_inv=0, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=10, daily_release_rate=2400)
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=50)
    assert spr.level >= 0


def test_spr_log_records_releases():
    env, port = _make_env_port(initial_inv=100, hourly_demand=0)
    spr = SPR(env, capacity=10_000, initial_level=5_000, daily_release_rate=2400)
    env.process(spr.monitor_and_release(port, critical_threshold=1000))
    env.run(until=3)
    assert len(spr.get_level_log()) > 0
