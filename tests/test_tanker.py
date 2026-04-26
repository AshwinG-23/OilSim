import simpy
import pytest
from core.tanker import Tanker, Fleet


def test_fleet_initial_all_available():
    env = simpy.Environment()
    fleet = Fleet(env, num_tankers=5, tanker_capacity_bbl=2_000_000)
    assert fleet.available_count == 5
    assert fleet.total_count == 5


def test_fleet_request_reduces_available():
    env = simpy.Environment()
    fleet = Fleet(env, num_tankers=3, tanker_capacity_bbl=2_000_000)
    received = []

    def borrower():
        tanker = yield fleet.request()
        received.append(tanker)
        yield env.timeout(10)
        fleet.release(tanker)

    env.process(borrower())
    env.run(until=1)
    assert fleet.available_count == 2


def test_fleet_release_restores_available():
    env = simpy.Environment()
    fleet = Fleet(env, num_tankers=2, tanker_capacity_bbl=2_000_000)
    done = []

    def voyage():
        tanker = yield fleet.request()
        yield env.timeout(5)
        fleet.release(tanker)
        done.append(True)

    env.process(voyage())
    env.run(until=10)
    assert fleet.available_count == 2
    assert done


def test_tanker_has_name_and_capacity():
    t = Tanker("T01", 2_000_000)
    assert t.name == "T01"
    assert t.capacity_bbl == 2_000_000
    assert t.state == 'idle'


def test_fleet_blocks_when_exhausted():
    env = simpy.Environment()
    fleet = Fleet(env, num_tankers=1, tanker_capacity_bbl=2_000_000)
    got_second = []

    def first():
        t = yield fleet.request()
        yield env.timeout(100)
        fleet.release(t)

    def second():
        yield env.timeout(1)
        t = yield fleet.request()   # should block until first returns
        got_second.append(env.now)
        fleet.release(t)

    env.process(first())
    env.process(second())
    env.run(until=200)
    assert got_second[0] >= 100
