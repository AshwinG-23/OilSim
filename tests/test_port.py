import simpy
import pytest
from core.port import Port


def test_demand_drains_inventory():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=1000, max_inventory=5000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=6)   # demand fires at t=1..5 → 5 steps consumed
    assert port.inventory == pytest.approx(500, rel=0.01)


def test_shortage_hours_counted_when_empty():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=50, max_inventory=5000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=10)
    assert port.shortage_hours > 0


def test_no_shortage_with_ample_inventory():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=10_000, max_inventory=50_000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=50)
    assert port.shortage_hours == 0


def test_receive_delivery_adds_inventory():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=1000, max_inventory=5000, hourly_demand=0)
    port.receive_delivery(500)
    assert port.inventory == 1500


def test_receive_delivery_clips_at_max():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=4800, max_inventory=5000, hourly_demand=0)
    port.receive_delivery(500)
    assert port.inventory == 5000


def test_demand_fulfillment_rate_perfect_when_no_shortage():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=10_000, max_inventory=50_000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=50)
    assert port.demand_fulfillment_rate == pytest.approx(1.0, rel=0.01)


def test_demand_fulfillment_rate_drops_on_shortage():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=100, max_inventory=5000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=10)
    assert port.demand_fulfillment_rate < 1.0


def test_inventory_log_populated():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=1000, max_inventory=5000, hourly_demand=10)
    env.process(port.demand_process())
    env.process(port.logging_process(interval=24))
    env.run(until=50)
    log = port.get_inventory_log()
    assert len(log) >= 2
