import simpy
import pytest
from config.params import SOURCES, CHOKEPOINTS
from core.chokepoint import Chokepoint
from core.port import Port
from core.tanker import Fleet
from strategies.policy import OrderingPolicy


def _make_components(initial_inv=30_000_000, hourly_demand=0):
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inv, 80_000_000, hourly_demand)
    fleet = Fleet(env, 10, 2_000_000)
    cps = {n: Chokepoint(env, n, cfg['capacity'], cfg['base_transit_hours'])
           for n, cfg in CHOKEPOINTS.items()}
    return env, port, fleet, cps


# ── Source priority ──────────────────────────────────────────────────────────

def test_cost_focused_picks_gulf_when_no_disruption():
    _, port, fleet, cps = _make_components()
    policy = OrderingPolicy('cost_focused', SOURCES, 40_000_000, 60_000_000)
    priority = policy.get_source_priority(disrupted_chokepoints=[])
    assert priority[0] == 'Gulf'   # cheapest


def test_cost_focused_deprioritizes_gulf_when_hormuz_disrupted():
    _, port, fleet, cps = _make_components()
    policy = OrderingPolicy('cost_focused', SOURCES, 40_000_000, 60_000_000)
    priority = policy.get_source_priority(disrupted_chokepoints=['Hormuz'])
    assert priority[0] != 'Gulf'


def test_resilient_avoids_disrupted_routes_first():
    _, port, fleet, cps = _make_components()
    policy = OrderingPolicy('resilient', SOURCES, 40_000_000, 60_000_000)
    # Pipeline disabled at runtime; pass that here to mirror engine behaviour
    priority = policy.get_source_priority(
        disrupted_chokepoints=['Hormuz', 'Red_Sea'],
        disabled_sources={'Gulf_Pipeline'},
    )
    assert priority[0] == 'Africa'   # only safe route


def test_diversified_puts_safe_sources_first():
    _, port, fleet, cps = _make_components()
    policy = OrderingPolicy('diversified', SOURCES, 40_000_000, 60_000_000)
    priority = policy.get_source_priority(disrupted_chokepoints=['Hormuz'])
    safe   = [s for s in priority if 'Hormuz' not in SOURCES[s]['chokepoints']]
    unsafe = [s for s in priority if 'Hormuz' in SOURCES[s]['chokepoints']]
    if safe and unsafe:
        last_safe_idx    = max(priority.index(s) for s in safe)
        first_unsafe_idx = min(priority.index(s) for s in unsafe)
        assert last_safe_idx < first_unsafe_idx


# ── should_order ─────────────────────────────────────────────────────────────

def test_should_order_when_inventory_below_reorder():
    env, port, fleet, cps = _make_components(initial_inv=20_000_000)
    policy = OrderingPolicy('cost_focused', SOURCES, 30_000_000, 60_000_000)
    assert policy.should_order(port, fleet) is True


def test_no_order_when_inventory_sufficient():
    env, port, fleet, cps = _make_components(initial_inv=50_000_000)
    policy = OrderingPolicy('cost_focused', SOURCES, 30_000_000, 60_000_000)
    assert policy.should_order(port, fleet) is False


def test_no_order_when_fleet_empty():
    env = simpy.Environment()
    port = Port(env, "Mumbai", 20_000_000, 80_000_000, 0)
    fleet = Fleet(env, 0, 2_000_000)
    policy = OrderingPolicy('cost_focused', SOURCES, 30_000_000, 60_000_000)
    assert policy.should_order(port, fleet) is False


# ── place_order ──────────────────────────────────────────────────────────────

def test_place_order_returns_valid_order():
    env, port, fleet, cps = _make_components(initial_inv=20_000_000)
    policy = OrderingPolicy('cost_focused', SOURCES, 30_000_000, 60_000_000)
    order = policy.place_order(port, fleet, cps, disrupted_chokepoints=[])
    assert order is not None
    assert order['cargo_bbl'] > 0
    assert order['source'] in SOURCES
    assert isinstance(order['route_chokepoints'], list)


def test_place_order_computes_cost():
    env, port, fleet, cps = _make_components(initial_inv=20_000_000)
    policy = OrderingPolicy('cost_focused', SOURCES, 30_000_000, 60_000_000)
    order = policy.place_order(port, fleet, cps, disrupted_chokepoints=[])
    assert order['cost_per_bbl'] > 0
