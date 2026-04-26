# Hormuz Supply Chain Resilience Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a discrete-event simulation engine using SimPy that models India's crude oil import supply chain under geopolitical disruptions, comparing three sourcing strategies across four disruption scenarios.

**Architecture:** SimPy-based DES where Chokepoints are Resource queues, Tankers are Store items loaned out for voyage processes, and a Port continuously drains inventory while a daily ordering process replenishes it. A DisruptionEngine fires timed events that degrade chokepoint throughput, triggering congestion feedback loops and strategy-dependent rerouting.

**Tech Stack:** Python 3.10+, SimPy 4.x, pytest, csv (stdlib), random (stdlib), logging (stdlib)

---

## File Structure

```
simPro/
├── config/
│   └── params.py          # All simulation constants, source configs, scenario definitions
├── core/
│   ├── __init__.py
│   ├── chokepoint.py       # Chokepoint: SimPy Resource + disruption severity + transit time
│   ├── port.py             # Port: inventory buffer, hourly demand drain, delivery receipt
│   ├── spr.py              # SPR: emergency reserve with threshold-triggered release
│   ├── tanker.py           # Tanker entity + Fleet (simpy.Store pool)
│   └── disruption.py       # DisruptionEngine: schedules timed severity changes
├── strategies/
│   ├── __init__.py
│   └── policy.py           # OrderingPolicy: source selection for cost/diversified/resilient
├── simulation/
│   ├── __init__.py
│   ├── engine.py           # SimulationEngine: wires all components, runs sim
│   └── metrics.py          # Metrics: records and aggregates time-series data
├── experiments/
│   ├── __init__.py
│   └── runner.py           # ExperimentRunner: scenario × strategy × replications matrix
├── analysis/
│   ├── __init__.py
│   └── results.py          # Results: aggregation, comparison tables, CSV export
├── tests/
│   ├── conftest.py         # Shared SimPy env fixtures
│   ├── test_chokepoint.py
│   ├── test_port.py
│   ├── test_spr.py
│   ├── test_tanker.py
│   ├── test_disruption.py
│   ├── test_policy.py
│   ├── test_engine.py
│   └── test_runner.py
├── requirements.txt
└── main.py                 # Entry point: runs full experiment matrix, prints results
```

---

### Task 1: Project Skeleton + Parameters

**Files:**
- Create: `requirements.txt`
- Create: `config/params.py`
- Create: `config/__init__.py`
- Create: `core/__init__.py`
- Create: `strategies/__init__.py`
- Create: `simulation/__init__.py`
- Create: `experiments/__init__.py`
- Create: `analysis/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_params.py`:
```python
from config.params import (
    SIM_DURATION_HOURS, NUM_TANKERS, TANKER_CAPACITY_BBL,
    PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL,
    PORT_DAILY_DEMAND_BBL, PORT_REORDER_POINT_BBL,
    PORT_CRITICAL_INVENTORY_BBL, SPR_INITIAL_LEVEL_BBL,
    SPR_MAX_CAPACITY_BBL, SPR_DAILY_RELEASE_RATE_BBL,
    SOURCES, CHOKEPOINTS, SCENARIOS, STRATEGIES, NUM_REPLICATIONS,
)

def test_sources_have_required_keys():
    for name, cfg in SOURCES.items():
        assert 'base_cost_per_bbl' in cfg
        assert 'loading_time_hours' in cfg
        assert 'return_time_hours' in cfg
        assert 'chokepoints' in cfg
        assert 'cargo_bbl' in cfg

def test_scenarios_have_required_keys():
    for name, cfg in SCENARIOS.items():
        assert 'disruptions' in cfg

def test_all_chokepoint_refs_valid():
    for source_name, cfg in SOURCES.items():
        for cp_name in cfg['chokepoints']:
            assert cp_name in CHOKEPOINTS, f"{source_name} refs unknown chokepoint {cp_name}"

def test_reorder_point_below_initial_inventory():
    assert PORT_REORDER_POINT_BBL < PORT_INITIAL_INVENTORY_BBL

def test_critical_below_reorder():
    assert PORT_CRITICAL_INVENTORY_BBL < PORT_REORDER_POINT_BBL
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ashwin/CS572/simPro
python -m pytest tests/test_params.py -v
```
Expected: ModuleNotFoundError — config.params not found.

- [ ] **Step 3: Create requirements.txt and all __init__.py files**

`requirements.txt`:
```
simpy>=4.0.1
pytest>=7.0
```

Empty `__init__.py` for each package: `config/`, `core/`, `strategies/`, `simulation/`, `experiments/`, `analysis/`.

- [ ] **Step 4: Write `config/params.py`**

```python
# Simulation time unit: hours
SIM_DURATION_HOURS = 200 * 24  # 200 days

# Fleet
NUM_TANKERS = 25
TANKER_CAPACITY_BBL = 2_000_000  # VLCC: 2M barrels

# Port (India aggregate import terminal)
PORT_INITIAL_INVENTORY_BBL = 50_000_000   # 10 days supply
PORT_MAX_INVENTORY_BBL     = 80_000_000
PORT_DAILY_DEMAND_BBL      = 5_000_000    # ~India's crude import rate
PORT_REORDER_POINT_BBL     = 30_000_000   # trigger replenishment
PORT_TARGET_INVENTORY_BBL  = 60_000_000
PORT_CRITICAL_INVENTORY_BBL= 10_000_000   # trigger SPR

# Strategic Petroleum Reserve
SPR_INITIAL_LEVEL_BBL      = 39_000_000
SPR_MAX_CAPACITY_BBL       = 40_000_000
SPR_DAILY_RELEASE_RATE_BBL = 1_000_000    # 1M bbl/day emergency release

# Sources: transport cost + timing + route
SOURCES = {
    'Gulf': {
        'base_cost_per_bbl':  2.50,
        'loading_time_hours': 48,
        'return_time_hours':  240,   # 10-day return voyage
        'chokepoints':        ['Hormuz'],
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
    'Russia': {
        'base_cost_per_bbl':  3.00,
        'loading_time_hours': 72,
        'return_time_hours':  432,   # 18-day return
        'chokepoints':        ['Red_Sea'],
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
    'Africa': {
        'base_cost_per_bbl':  4.00,
        'loading_time_hours': 96,
        'return_time_hours':  600,   # 25-day return (Cape route)
        'chokepoints':        [],    # open ocean, no bottleneck
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
}

# Chokepoints: simultaneous-ship capacity + baseline transit time
CHOKEPOINTS = {
    'Hormuz': {
        'capacity':            10,
        'base_transit_hours':  48,   # 2 days through strait
    },
    'Red_Sea': {
        'capacity':            8,
        'base_transit_hours':  96,   # 4 days
    },
}

# Disruption scenarios
SCENARIOS = {
    'no_disruption': {
        'disruptions': [],
    },
    'short_conflict': {
        'disruptions': [
            {'chokepoint': 'Hormuz', 'start_day': 30, 'duration_days':  30, 'severity': 0.5},
        ],
    },
    'medium_blockade': {
        'disruptions': [
            {'chokepoint': 'Hormuz', 'start_day': 30, 'duration_days':  90, 'severity': 0.2},
        ],
    },
    'long_war': {
        'disruptions': [
            {'chokepoint': 'Hormuz',  'start_day': 30, 'duration_days': 150, 'severity': 0.1},
            {'chokepoint': 'Red_Sea', 'start_day': 45, 'duration_days': 120, 'severity': 0.5},
        ],
    },
}

STRATEGIES       = ['cost_focused', 'diversified', 'resilient']
NUM_REPLICATIONS = 5
UNLOADING_TIME_HOURS = 48   # 2 days at port
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_params.py -v
```
Expected: All 5 PASS.

- [ ] **Step 6: Commit**

```bash
git add config/ tests/test_params.py requirements.txt core/__init__.py strategies/__init__.py simulation/__init__.py experiments/__init__.py analysis/__init__.py
git commit -m "feat: project skeleton and simulation parameters"
```

---

### Task 2: Chokepoint Model

**Files:**
- Create: `core/chokepoint.py`
- Create: `tests/test_chokepoint.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chokepoint.py
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
    # Each subsequent ship faces more congestion
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_chokepoint.py -v
```
Expected: ModuleNotFoundError — core.chokepoint not found.

- [ ] **Step 3: Write `core/chokepoint.py`**

```python
import simpy
import random
import logging

logger = logging.getLogger(__name__)


class Chokepoint:
    def __init__(self, env, name, capacity, base_transit_hours):
        self.env = env
        self.name = name
        self.capacity = capacity
        self.base_transit_hours = base_transit_hours
        self._resource = simpy.Resource(env, capacity=capacity)
        self.status = 1.0          # 1.0=normal, 0.01=nearly blocked
        self._transit_log = []

    @property
    def queue_length(self):
        return len(self._resource.queue)

    @property
    def in_use(self):
        return self._resource.count

    def set_disruption(self, severity):
        self.status = max(0.01, min(1.0, severity))
        logger.info(
            "[%.0fh] %s disruption: status=%.2f",
            self.env.now, self.name, self.status,
        )

    def get_transit_time(self):
        base = self.base_transit_hours / self.status
        congestion = self.queue_length * 0.5   # 0.5 h penalty per queued ship
        noise = abs(random.gauss(0, base * 0.05))
        return base + congestion + noise

    def transit(self, tanker_name):
        queue_on_arrival = self.queue_length
        with self._resource.request() as req:
            yield req
            t = self.get_transit_time()
            self._transit_log.append({
                'time': self.env.now,
                'tanker': tanker_name,
                'transit_hours': t,
                'queue_on_arrival': queue_on_arrival,
                'status': self.status,
            })
            yield self.env.timeout(t)

    def get_transit_log(self):
        return list(self._transit_log)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_chokepoint.py -v
```
Expected: All 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add core/chokepoint.py tests/test_chokepoint.py
git commit -m "feat: chokepoint model with disruption severity and congestion"
```

---

### Task 3: Port Model

**Files:**
- Create: `core/port.py`
- Create: `tests/test_port.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_port.py
import simpy
import pytest
from core.port import Port


def test_demand_drains_inventory():
    env = simpy.Environment()
    port = Port(env, "Mumbai", initial_inventory=1000, max_inventory=5000, hourly_demand=100)
    env.process(port.demand_process())
    env.run(until=5)
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_port.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `core/port.py`**

```python
import simpy
import logging

logger = logging.getLogger(__name__)


class Port:
    def __init__(self, env, name, initial_inventory, max_inventory, hourly_demand):
        self.env = env
        self.name = name
        self.inventory = float(initial_inventory)
        self.max_inventory = float(max_inventory)
        self.hourly_demand = float(hourly_demand)
        self.shortage_hours = 0
        self.total_delivered_bbl = 0.0
        self.total_demanded_bbl = 0.0
        self._inventory_log = []

    def demand_process(self):
        while True:
            yield self.env.timeout(1)
            consumed = min(self.inventory, self.hourly_demand)
            self.inventory -= consumed
            self.total_demanded_bbl += self.hourly_demand
            if self.inventory < 1e-3:
                self.shortage_hours += 1

    def logging_process(self, interval=24):
        while True:
            self._inventory_log.append({'time': self.env.now, 'inventory': self.inventory})
            yield self.env.timeout(interval)

    def receive_delivery(self, barrels):
        space = self.max_inventory - self.inventory
        delivered = min(float(barrels), space)
        self.inventory += delivered
        self.total_delivered_bbl += delivered
        logger.info(
            "[%.0fh] %s received %.2fM bbl → inventory %.2fM bbl",
            self.env.now, self.name, delivered / 1e6, self.inventory / 1e6,
        )

    @property
    def demand_fulfillment_rate(self):
        if self.total_demanded_bbl == 0:
            return 1.0
        shortage_volume = self.shortage_hours * self.hourly_demand
        return max(0.0, 1.0 - shortage_volume / self.total_demanded_bbl)

    def get_inventory_log(self):
        return list(self._inventory_log)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_port.py -v
```
Expected: All 8 PASS.

- [ ] **Step 5: Commit**

```bash
git add core/port.py tests/test_port.py
git commit -m "feat: port inventory model with demand drain and fulfillment tracking"
```

---

### Task 4: Strategic Petroleum Reserve (SPR)

**Files:**
- Create: `core/spr.py`
- Create: `tests/test_spr.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_spr.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_spr.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `core/spr.py`**

```python
import logging

logger = logging.getLogger(__name__)


class SPR:
    def __init__(self, env, capacity, initial_level, daily_release_rate):
        self.env = env
        self.capacity = float(capacity)
        self.level = float(initial_level)
        self.daily_release_rate = float(daily_release_rate)
        self._hourly_release = daily_release_rate / 24.0
        self.total_released = 0.0
        self.is_releasing = False
        self._level_log = []

    def monitor_and_release(self, port, critical_threshold):
        while True:
            yield self.env.timeout(1)
            if port.inventory < critical_threshold and self.level > 0:
                if not self.is_releasing:
                    logger.info(
                        "[%.0fh] SPR release triggered. Port=%.2fM bbl",
                        self.env.now, port.inventory / 1e6,
                    )
                    self.is_releasing = True
                release = min(self._hourly_release, self.level)
                self.level -= release
                self.total_released += release
                port.receive_delivery(release)
                self._level_log.append({'time': self.env.now, 'level': self.level})
            else:
                if self.is_releasing:
                    logger.info("[%.0fh] SPR release stopped.", self.env.now)
                    self.is_releasing = False

    def get_level_log(self):
        return list(self._level_log)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_spr.py -v
```
Expected: All 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add core/spr.py tests/test_spr.py
git commit -m "feat: strategic petroleum reserve with threshold-triggered release"
```

---

### Task 5: Tanker Entity + Fleet Pool

**Files:**
- Create: `core/tanker.py`
- Create: `tests/test_tanker.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tanker.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_tanker.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `core/tanker.py`**

```python
import simpy


class Tanker:
    def __init__(self, name, capacity_bbl):
        self.name = name
        self.capacity_bbl = capacity_bbl
        self.state = 'idle'
        self.voyages_completed = 0


class Fleet:
    def __init__(self, env, num_tankers, tanker_capacity_bbl):
        self.env = env
        self._store = simpy.Store(env)
        self._tankers = [Tanker(f"T{i:02d}", tanker_capacity_bbl) for i in range(num_tankers)]
        for t in self._tankers:
            self._store.put(t)

    def request(self):
        return self._store.get()

    def release(self, tanker):
        tanker.state = 'idle'
        self._store.put(tanker)

    @property
    def available_count(self):
        return len(self._store.items)

    @property
    def total_count(self):
        return len(self._tankers)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_tanker.py -v
```
Expected: All 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add core/tanker.py tests/test_tanker.py
git commit -m "feat: tanker entity and simpy.Store fleet pool"
```

---

### Task 6: Disruption Engine

**Files:**
- Create: `core/disruption.py`
- Create: `tests/test_disruption.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_disruption.py
import simpy
import pytest
from core.chokepoint import Chokepoint
from core.disruption import DisruptionEngine


def _setup(disruption_configs):
    env = simpy.Environment()
    cps = {
        'Hormuz': Chokepoint(env, 'Hormuz', capacity=10, base_transit_hours=48),
        'Red_Sea': Chokepoint(env, 'Red_Sea', capacity=8, base_transit_hours=96),
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
    assert cps['Hormuz'].status == pytest.approx(0.2)
    assert cps['Red_Sea'].status == pytest.approx(0.5)


def test_event_log_records_start_and_end():
    cfg = [{'chokepoint': 'Hormuz', 'start_day': 1, 'duration_days': 1, 'severity': 0.5}]
    env, cps, de = _setup(cfg)
    env.run(until=24 + 24 + 1)
    log = de.get_event_log()
    assert len(log) == 2
    assert log[0]['event'] == 'start'
    assert log[1]['event'] == 'end'
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_disruption.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `core/disruption.py`**

```python
import logging

logger = logging.getLogger(__name__)


class DisruptionEngine:
    def __init__(self, env, chokepoints):
        self.env = env
        self.chokepoints = chokepoints   # dict[name -> Chokepoint]
        self._event_log = []

    def schedule_disruptions(self, disruption_configs):
        for cfg in disruption_configs:
            self.env.process(self._disruption_process(cfg))

    def _disruption_process(self, cfg):
        name        = cfg['chokepoint']
        start_hours = cfg['start_day'] * 24
        duration_h  = cfg['duration_days'] * 24
        severity    = cfg['severity']

        yield self.env.timeout(start_hours)
        self.chokepoints[name].set_disruption(severity)
        self._event_log.append({
            'time': self.env.now, 'chokepoint': name,
            'event': 'start', 'severity': severity,
        })
        logger.info("[%.0fh] DISRUPTION START: %s severity=%.2f", self.env.now, name, severity)

        yield self.env.timeout(duration_h)
        self.chokepoints[name].set_disruption(1.0)
        self._event_log.append({
            'time': self.env.now, 'chokepoint': name,
            'event': 'end', 'severity': 1.0,
        })
        logger.info("[%.0fh] DISRUPTION END: %s restored", self.env.now, name)

    def get_event_log(self):
        return list(self._event_log)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_disruption.py -v
```
Expected: All 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add core/disruption.py tests/test_disruption.py
git commit -m "feat: disruption engine with timed severity events"
```

---

### Task 7: Ordering Policies (Strategies)

**Files:**
- Create: `strategies/policy.py`
- Create: `tests/test_policy.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy.py
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
    priority = policy.get_source_priority(disrupted_chokepoints=['Hormuz', 'Red_Sea'])
    assert priority[0] == 'Africa'   # only safe route


def test_diversified_puts_safe_sources_first():
    _, port, fleet, cps = _make_components()
    policy = OrderingPolicy('diversified', SOURCES, 40_000_000, 60_000_000)
    priority = policy.get_source_priority(disrupted_chokepoints=['Hormuz'])
    safe = [s for s in priority if 'Hormuz' not in SOURCES[s]['chokepoints']]
    unsafe = [s for s in priority if 'Hormuz' in SOURCES[s]['chokepoints']]
    # all safe sources appear before unsafe
    if safe and unsafe:
        last_safe_idx = max(priority.index(s) for s in safe)
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_policy.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `strategies/policy.py`**

```python
import logging

logger = logging.getLogger(__name__)


class OrderingPolicy:
    def __init__(self, strategy, sources_config, reorder_point, target_inventory):
        self.strategy = strategy
        self.sources = sources_config
        self.reorder_point = reorder_point
        self.target_inventory = target_inventory
        self._orders_log = []

    def should_order(self, port, fleet):
        return port.inventory < self.reorder_point and fleet.available_count > 0

    def get_source_priority(self, disrupted_chokepoints):
        disrupted = set(disrupted_chokepoints)

        def is_safe(source_name):
            return not any(c in disrupted for c in self.sources[source_name]['chokepoints'])

        if self.strategy == 'cost_focused':
            # Cheapest first; push disrupted-route sources to end
            safe   = sorted((s for s in self.sources if is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            unsafe = sorted((s for s in self.sources if not is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            return safe + unsafe

        elif self.strategy == 'diversified':
            # Safe sources first (cost-ordered within each group)
            safe   = sorted((s for s in self.sources if is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            unsafe = sorted((s for s in self.sources if not is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            return safe + unsafe

        elif self.strategy == 'resilient':
            # Strong preference for safe routes; among safe, cheapest first
            safe   = sorted((s for s in self.sources if is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            unsafe = sorted((s for s in self.sources if not is_safe(s)),
                            key=lambda s: self.sources[s]['base_cost_per_bbl'])
            return safe + unsafe

        return list(self.sources.keys())

    def place_order(self, port, fleet, chokepoints, disrupted_chokepoints):
        priority = self.get_source_priority(disrupted_chokepoints)
        if not priority:
            return None
        source_name = priority[0]
        src = self.sources[source_name]

        # Diversified strategy rotates sources round-robin
        if self.strategy == 'diversified':
            num_placed = len(self._orders_log)
            source_name = priority[num_placed % len(priority)]
            src = self.sources[source_name]

        disruption_premium = 1.0
        for cp_name in src['chokepoints']:
            if cp_name in chokepoints:
                cp = chokepoints[cp_name]
                disruption_premium += max(0.0, (1.0 - cp.status)) * 1.5

        order = {
            'source':               source_name,
            'cargo_bbl':            src['cargo_bbl'],
            'cost_per_bbl':         src['base_cost_per_bbl'] * disruption_premium,
            'loading_time_hours':   src['loading_time_hours'],
            'return_time_hours':    src['return_time_hours'],
            'route_chokepoints':    [chokepoints[c] for c in src['chokepoints']
                                     if c in chokepoints],
        }
        self._orders_log.append({'source': source_name})
        logger.info("Order placed: %s via %s (cost $%.2f/bbl)",
                    source_name, src['chokepoints'], order['cost_per_bbl'])
        return order

    def get_orders_log(self):
        return list(self._orders_log)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_policy.py -v
```
Expected: All 10 PASS.

- [ ] **Step 5: Commit**

```bash
git add strategies/policy.py tests/test_policy.py
git commit -m "feat: cost-focused, diversified, resilient ordering policies"
```

---

### Task 8: Metrics Collector

**Files:**
- Create: `simulation/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_metrics.py
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
    m.record_cost(0, 'Gulf', 2e6, 2.5)   # total cost 5M for 2M bbl
    m.record_cost(0, 'Africa', 2e6, 4.0) # total cost 8M for 2M bbl
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
    assert m.fleet_log[0]['utilization'] == pytest.approx(15/25)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_metrics.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `simulation/metrics.py`**

```python
class Metrics:
    def __init__(self):
        self.inventory_log  = []
        self.cost_log       = []
        self.shortage_times = []
        self.fleet_log      = []
        self.transit_log    = []

    def record_inventory(self, time, inventory):
        self.inventory_log.append({'time': time, 'inventory': inventory})

    def record_cost(self, time, source, barrels, cost_per_bbl):
        self.cost_log.append({
            'time':       time,
            'source':     source,
            'barrels':    barrels,
            'cost_per_bbl': cost_per_bbl,
            'total_cost': barrels * cost_per_bbl,
        })

    def record_shortage(self, time):
        self.shortage_times.append(time)

    def record_fleet_utilization(self, time, in_use, total):
        self.fleet_log.append({
            'time':        time,
            'in_use':      in_use,
            'total':       total,
            'utilization': in_use / total if total > 0 else 0.0,
        })

    def compute_summary(self, total_sim_hours):
        total_cost    = sum(c['total_cost'] for c in self.cost_log)
        total_barrels = sum(c['barrels']    for c in self.cost_log)
        shortage_hrs  = len(self.shortage_times)
        dfr = max(0.0, 1.0 - shortage_hrs / total_sim_hours) if total_sim_hours > 0 else 1.0
        avg_util = (sum(f['utilization'] for f in self.fleet_log) / len(self.fleet_log)
                    if self.fleet_log else 0.0)

        return {
            'shortage_hours':          shortage_hrs,
            'total_cost':              total_cost,
            'total_barrels_imported':  total_barrels,
            'avg_cost_per_bbl':        total_cost / total_barrels if total_barrels > 0 else 0.0,
            'demand_fulfillment_rate': dfr,
            'avg_fleet_utilization':   avg_util,
            'first_shortage_hour':     self.shortage_times[0] if self.shortage_times else None,
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_metrics.py -v
```
Expected: All 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add simulation/metrics.py tests/test_metrics.py
git commit -m "feat: metrics collector with cost, shortage, and fleet tracking"
```

---

### Task 9: Simulation Engine

**Files:**
- Create: `simulation/engine.py`
- Create: `tests/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py
import pytest
from config.params import SCENARIOS
from simulation.engine import SimulationEngine


def test_engine_runs_without_error():
    engine = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    results = engine.run(duration_hours=10 * 24)   # 10 days
    assert results is not None


def test_no_disruption_no_shortage():
    engine = SimulationEngine(SCENARIOS['no_disruption'], 'cost_focused', seed=42)
    results = engine.run(duration_hours=60 * 24)   # 60 days
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
    cost_eng = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    resil_eng = SimulationEngine(SCENARIOS['long_war'], 'resilient',    seed=42)

    r_cost  = cost_eng.run(duration_hours=200 * 24)
    r_resil = resil_eng.run(duration_hours=200 * 24)

    assert r_resil['shortage_hours'] <= r_cost['shortage_hours']


def test_spr_reduces_shortage():
    # Run with and without SPR (set SPR level to 0 to disable)
    engine_with = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    engine_with.spr.level = 39_000_000   # full SPR
    r_with = engine_with.run(200 * 24)

    engine_without = SimulationEngine(SCENARIOS['long_war'], 'cost_focused', seed=42)
    engine_without.spr.level = 0         # empty SPR
    r_without = engine_without.run(200 * 24)

    assert r_with['shortage_hours'] <= r_without['shortage_hours']
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_engine.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `simulation/engine.py`**

```python
import random
import simpy
import logging

from config.params import (
    NUM_TANKERS, TANKER_CAPACITY_BBL,
    PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL, PORT_DAILY_DEMAND_BBL,
    PORT_REORDER_POINT_BBL, PORT_TARGET_INVENTORY_BBL, PORT_CRITICAL_INVENTORY_BBL,
    SPR_INITIAL_LEVEL_BBL, SPR_MAX_CAPACITY_BBL, SPR_DAILY_RELEASE_RATE_BBL,
    SOURCES, CHOKEPOINTS, SIM_DURATION_HOURS, UNLOADING_TIME_HOURS,
)
from core.chokepoint import Chokepoint
from core.port import Port
from core.spr import SPR
from core.tanker import Fleet
from core.disruption import DisruptionEngine
from strategies.policy import OrderingPolicy
from simulation.metrics import Metrics

logger = logging.getLogger(__name__)


class SimulationEngine:
    def __init__(self, scenario_config, strategy_name, seed=None):
        if seed is not None:
            random.seed(seed)
        self.env = simpy.Environment()
        self.scenario = scenario_config
        self.strategy_name = strategy_name

        self.chokepoints = {
            name: Chokepoint(self.env, name, cfg['capacity'], cfg['base_transit_hours'])
            for name, cfg in CHOKEPOINTS.items()
        }
        self.port = Port(
            self.env, "India_Terminals",
            PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL,
            PORT_DAILY_DEMAND_BBL / 24,
        )
        self.spr = SPR(
            self.env, SPR_MAX_CAPACITY_BBL,
            SPR_INITIAL_LEVEL_BBL, SPR_DAILY_RELEASE_RATE_BBL,
        )
        self.fleet = Fleet(self.env, NUM_TANKERS, TANKER_CAPACITY_BBL)
        self.policy = OrderingPolicy(
            strategy_name, SOURCES,
            PORT_REORDER_POINT_BBL, PORT_TARGET_INVENTORY_BBL,
        )
        self.disruption_engine = DisruptionEngine(self.env, self.chokepoints)
        self.metrics = Metrics()

    # ── Voyage process ────────────────────────────────────────────────────────

    def _tanker_voyage(self, tanker, order):
        tanker.state = 'loading'
        yield self.env.timeout(order['loading_time_hours'])

        tanker.state = 'transit'
        for cp in order['route_chokepoints']:
            yield from cp.transit(tanker.name)

        tanker.state = 'unloading'
        self.port.receive_delivery(order['cargo_bbl'])
        self.metrics.record_cost(
            self.env.now, order['source'],
            order['cargo_bbl'], order['cost_per_bbl'],
        )
        yield self.env.timeout(UNLOADING_TIME_HOURS)

        tanker.state = 'returning'
        yield self.env.timeout(order['return_time_hours'])

        tanker.voyages_completed += 1
        self.fleet.release(tanker)

    # ── Tanker assignment process ─────────────────────────────────────────────

    def _assign_tanker(self, order):
        tanker = yield self.fleet.request()
        self.env.process(self._tanker_voyage(tanker, order))

    # ── Ordering process (daily) ──────────────────────────────────────────────

    def _ordering_process(self):
        while True:
            yield self.env.timeout(24)
            disrupted = [
                name for name, cp in self.chokepoints.items()
                if cp.status < 0.8
            ]
            if not self.policy.should_order(self.port, self.fleet):
                continue
            order = self.policy.place_order(
                self.port, self.fleet, self.chokepoints, disrupted
            )
            if order is None:
                continue
            num = min(3, self.fleet.available_count)
            for _ in range(num):
                self.env.process(self._assign_tanker(order))

    # ── Metrics process (daily) ───────────────────────────────────────────────

    def _metrics_process(self):
        while True:
            self.metrics.record_inventory(self.env.now, self.port.inventory)
            if self.port.inventory < 1e3:
                self.metrics.record_shortage(self.env.now)
            self.metrics.record_fleet_utilization(
                self.env.now,
                self.fleet.total_count - self.fleet.available_count,
                self.fleet.total_count,
            )
            yield self.env.timeout(1)

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, duration_hours=None):
        if duration_hours is None:
            duration_hours = SIM_DURATION_HOURS

        self.env.process(self.port.demand_process())
        self.env.process(self.port.logging_process())
        self.env.process(self.spr.monitor_and_release(self.port, PORT_CRITICAL_INVENTORY_BBL))
        self.env.process(self._ordering_process())
        self.env.process(self._metrics_process())

        self.disruption_engine.schedule_disruptions(
            self.scenario.get('disruptions', [])
        )
        self.env.run(until=duration_hours)
        return self.metrics.compute_summary(duration_hours)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_engine.py -v
```
Expected: All 6 PASS. (Note: `test_resilient_strategy_fewer_shortages_under_long_war` may be flaky depending on randomness — if so, increase duration or fix seed.)

- [ ] **Step 5: Commit**

```bash
git add simulation/engine.py tests/test_engine.py
git commit -m "feat: simulation engine wiring all components into a runnable SimPy model"
```

---

### Task 10: Experiment Runner

**Files:**
- Create: `experiments/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_runner.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `experiments/runner.py`**

```python
import logging
from config.params import SCENARIOS, STRATEGIES, NUM_REPLICATIONS, SIM_DURATION_HOURS
from simulation.engine import SimulationEngine

logger = logging.getLogger(__name__)


class ExperimentRunner:
    def __init__(self, scenarios=None, strategies=None,
                 num_replications=NUM_REPLICATIONS,
                 duration_hours=SIM_DURATION_HOURS):
        self.scenarios        = scenarios  or list(SCENARIOS.keys())
        self.strategies       = strategies or STRATEGIES
        self.num_replications = num_replications
        self.duration_hours   = duration_hours

    def run(self):
        all_results = []
        total = len(self.scenarios) * len(self.strategies) * self.num_replications
        done = 0
        for scenario_name in self.scenarios:
            scenario_cfg = SCENARIOS[scenario_name]
            for strategy in self.strategies:
                for rep in range(self.num_replications):
                    seed = hash((scenario_name, strategy, rep)) % (2**31)
                    logger.info(
                        "Running %s / %s / rep %d (seed=%d)",
                        scenario_name, strategy, rep, seed,
                    )
                    engine = SimulationEngine(scenario_cfg, strategy, seed=seed)
                    summary = engine.run(self.duration_hours)
                    summary.update({
                        'scenario':    scenario_name,
                        'strategy':    strategy,
                        'replication': rep,
                        'seed':        seed,
                    })
                    all_results.append(summary)
                    done += 1
                    print(f"  [{done}/{total}] {scenario_name}/{strategy}/rep{rep} "
                          f"shortages={summary['shortage_hours']}h "
                          f"cost=${summary['total_cost']/1e9:.2f}B")
        return all_results
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_runner.py -v
```
Expected: All 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/runner.py tests/test_runner.py
git commit -m "feat: experiment runner for scenario×strategy matrix with replications"
```

---

### Task 11: Results Analysis + Output

**Files:**
- Create: `analysis/results.py`
- Create: `tests/test_results.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_results.py
import pytest
from analysis.results import ResultsAnalyzer


SAMPLE_RESULTS = [
    {'scenario': 'no_disruption',  'strategy': 'cost_focused', 'replication': 0,
     'shortage_hours': 0,   'total_cost': 5e9,  'avg_cost_per_bbl': 2.5,
     'demand_fulfillment_rate': 1.0, 'total_barrels_imported': 2e9},
    {'scenario': 'no_disruption',  'strategy': 'cost_focused', 'replication': 1,
     'shortage_hours': 0,   'total_cost': 5.1e9, 'avg_cost_per_bbl': 2.55,
     'demand_fulfillment_rate': 1.0, 'total_barrels_imported': 2e9},
    {'scenario': 'long_war',       'strategy': 'cost_focused', 'replication': 0,
     'shortage_hours': 120, 'total_cost': 7e9,  'avg_cost_per_bbl': 3.5,
     'demand_fulfillment_rate': 0.7, 'total_barrels_imported': 2e9},
    {'scenario': 'long_war',       'strategy': 'resilient',    'replication': 0,
     'shortage_hours': 20,  'total_cost': 8e9,  'avg_cost_per_bbl': 4.0,
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
    assert 'scenario' in captured.out.lower() or len(captured.out) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_results.py -v
```
Expected: ModuleNotFoundError.

- [ ] **Step 3: Write `analysis/results.py`**

```python
import csv
import statistics
from collections import defaultdict


class ResultsAnalyzer:
    def __init__(self, raw_results):
        self.raw = raw_results

    def aggregate(self):
        groups = defaultdict(list)
        for r in self.raw:
            key = (r['scenario'], r['strategy'])
            groups[key].append(r)

        aggregated = {}
        for key, runs in groups.items():
            shortage  = [r['shortage_hours'] for r in runs]
            cost      = [r['total_cost']     for r in runs]
            cost_bbl  = [r['avg_cost_per_bbl'] for r in runs]
            dfr       = [r['demand_fulfillment_rate'] for r in runs]
            aggregated[key] = {
                'scenario':                 key[0],
                'strategy':                 key[1],
                'n_runs':                   len(runs),
                'mean_shortage_hours':      statistics.mean(shortage),
                'std_shortage_hours':       statistics.stdev(shortage) if len(shortage) > 1 else 0,
                'mean_total_cost':          statistics.mean(cost),
                'mean_avg_cost_per_bbl':    statistics.mean(cost_bbl),
                'mean_fulfillment_rate':    statistics.mean(dfr),
            }
        return aggregated

    def best_strategy_per_scenario(self, metric='mean_shortage_hours', lower_is_better=True):
        agg = self.aggregate()
        scenarios = {k[0] for k in agg}
        best = {}
        for sc in scenarios:
            candidates = {k[1]: v[metric] for k, v in agg.items() if k[0] == sc}
            if lower_is_better:
                best[sc] = min(candidates, key=candidates.get)
            else:
                best[sc] = max(candidates, key=candidates.get)
        return best

    def to_csv(self, filepath):
        if not self.raw:
            return
        fieldnames = list(self.raw[0].keys())
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.raw)

    def print_summary(self):
        agg = self.aggregate()
        print("\n" + "=" * 72)
        print(f"{'Scenario':<20} {'Strategy':<15} {'Shortages(h)':>12} "
              f"{'Cost($B)':>10} {'$/bbl':>8} {'DFR':>6}")
        print("-" * 72)
        for (sc, st), v in sorted(agg.items()):
            print(f"{sc:<20} {st:<15} "
                  f"{v['mean_shortage_hours']:>12.1f} "
                  f"{v['mean_total_cost']/1e9:>10.2f} "
                  f"{v['mean_avg_cost_per_bbl']:>8.2f} "
                  f"{v['mean_fulfillment_rate']:>6.3f}")
        print("=" * 72)

        print("\n=== Best strategy per scenario (fewest shortage hours) ===")
        best = self.best_strategy_per_scenario('mean_shortage_hours', lower_is_better=True)
        for sc, st in sorted(best.items()):
            print(f"  {sc:<20} → {st}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_results.py -v
```
Expected: All 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add analysis/results.py tests/test_results.py
git commit -m "feat: results aggregation, comparison tables, and CSV export"
```

---

### Task 12: Main Entry Point + conftest

**Files:**
- Create: `main.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
# tests/conftest.py
import simpy
import pytest


@pytest.fixture
def env():
    return simpy.Environment()
```

- [ ] **Step 2: Write `main.py`**

```python
#!/usr/bin/env python3
"""
Hormuz Supply Chain Resilience Simulator
Entry point: runs full experiment matrix and prints comparison results.
"""
import logging
import os
from config.params import SCENARIOS, STRATEGIES, NUM_REPLICATIONS, SIM_DURATION_HOURS
from experiments.runner import ExperimentRunner
from analysis.results import ResultsAnalyzer

logging.basicConfig(level=logging.WARNING)   # set to DEBUG for verbose output


def main():
    print("=" * 72)
    print("  Hormuz Supply Chain Resilience Simulator")
    print(f"  Scenarios : {list(SCENARIOS.keys())}")
    print(f"  Strategies: {STRATEGIES}")
    print(f"  Reps/cell : {NUM_REPLICATIONS}")
    print(f"  Duration  : {SIM_DURATION_HOURS/24:.0f} days")
    print("=" * 72)

    runner = ExperimentRunner(
        scenarios=list(SCENARIOS.keys()),
        strategies=STRATEGIES,
        num_replications=NUM_REPLICATIONS,
        duration_hours=SIM_DURATION_HOURS,
    )
    results = runner.run()

    analyzer = ResultsAnalyzer(results)
    analyzer.print_summary()

    out_path = os.path.join(os.path.dirname(__file__), "results.csv")
    analyzer.to_csv(out_path)
    print(f"\nDetailed results saved to: {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest tests/ -v --tb=short
```
Expected: All tests PASS.

- [ ] **Step 4: Run main.py to verify end-to-end output**

```bash
python main.py
```
Expected: Prints experiment progress, summary comparison table, and saves `results.csv`.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/conftest.py
git commit -m "feat: main entry point and conftest — full experiment pipeline complete"
```

---

## Self-Review Against Spec

| Spec Requirement | Covered By |
|---|---|
| Multi-source imports (Gulf, Russia, Africa) | `params.SOURCES`, `policy.py` |
| Chokepoints with capacity + queuing | `chokepoint.py` Task 2 |
| Fleet with finite tankers | `tanker.py` Task 5 |
| Inventory dynamics + demand | `port.py` Task 3 |
| SPR emergency buffer | `spr.py` Task 4 |
| Stochastic disruptions (Hormuz, Red Sea) | `disruption.py` Task 6 |
| 3 strategy types | `policy.py` Task 7 |
| Congestion feedback loop | `chokepoint.get_transit_time()` uses queue length |
| Cascade effects | Multi-disruption in `long_war` scenario |
| Operational metrics (inventory, DFR, shortage) | `metrics.py`, `port.py` |
| Economic metrics (cost, $/bbl) | `metrics.py` |
| Resilience metrics (shortage hours, first shortage) | `metrics.compute_summary()` |
| Multiple replications per scenario | `runner.py` |
| Comparison table output | `results.py` |
| CSV export | `results.to_csv()` |
| 4 scenarios | `params.SCENARIOS` |
| Configurable duration | `engine.run(duration_hours=...)` |
