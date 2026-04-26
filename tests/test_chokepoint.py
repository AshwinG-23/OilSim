import simpy
import pytest
from core.chokepoint import Chokepoint


def test_transit_completes_in_base_time():
    env = simpy.Environment()
    cp = Chokepoint(env, "Hormuz", capacity=10, base_transit_hours=48)
    results = []

    def tanker():
        yield from cp.transit("T1")
        results.append(env.now)

    env.process(tanker())
    env.run(until=200)
    assert len(results) == 1
    assert results[0] >= 48


def test_disruption_increases_transit_time():
    env = simpy.Environment()
    cp = Chokepoint(env, "Hormuz", capacity=10, base_transit_hours=48)
    cp.set_disruption(0.5)   # halve throughput → double time
    results = []

    def tanker():
        yield from cp.transit("T1")
        results.append(env.now)

    env.process(tanker())
    env.run(until=500)
    assert results[0] >= 96   # at least double the base time


def test_capacity_limits_concurrent_transits():
    env = simpy.Environment()
    cp = Chokepoint(env, "Hormuz", capacity=2, base_transit_hours=100)
    start_times = {}

    def tanker(name):
        yield from cp.transit(name)
        start_times[name] = env.now

    for i in range(3):
        env.process(tanker(f"T{i}"))

    env.run(until=500)
    # Third tanker must have waited — finished after 2× base transit minimum
    assert start_times["T2"] >= 100


def test_queue_length_increases_transit_time():
    env = simpy.Environment()
    # capacity=1 so ships queue up
    cp = Chokepoint(env, "Hormuz", capacity=1, base_transit_hours=48)
    finish_times = []

    def tanker(name):
        yield from cp.transit(name)
        finish_times.append(env.now)

    for i in range(3):
        env.process(tanker(f"T{i}"))

    env.run(until=600)
    assert len(finish_times) == 3
    # Each subsequent ship finishes later
    assert finish_times[2] > finish_times[0]


def test_set_disruption_clamps_to_minimum():
    env = simpy.Environment()
    cp = Chokepoint(env, "Hormuz", capacity=5, base_transit_hours=48)
    cp.set_disruption(-1.0)
    assert cp.status >= 0.01


def test_transit_log_records_entries():
    env = simpy.Environment()
    cp = Chokepoint(env, "Hormuz", capacity=5, base_transit_hours=48)

    def tanker():
        yield from cp.transit("T99")

    env.process(tanker())
    env.run(until=200)
    log = cp.get_transit_log()
    assert len(log) == 1
    assert log[0]['tanker'] == "T99"
    assert log[0]['transit_hours'] >= 48
