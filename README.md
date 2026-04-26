# Hormuz Supply Chain Resilience Simulator

A **Discrete-Event Simulation (DES)** engine built with SimPy that models India's crude oil import supply chain under geopolitical disruptions. Evaluates four sourcing strategies across ten disruption scenarios over a configurable time horizon.

---

## Setup & Run

**Requirements:** Python 3.9+

```bash
# 1. Clone the repo
git clone https://github.com/AshwinG-23/OilSim.git
cd OilSim

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the web dashboard
python web/app.py
# → Open http://localhost:5000 in your browser
```

That's it. The dashboard lets you pick a scenario, strategies, duration, and replications, then run the simulation and view results interactively.

**Optional — run the full experiment matrix from the command line:**
```bash
python main.py
```

**Optional — run the test suite:**
```bash
python -m pytest tests/ -v
```

---

## What This Simulates

India imports ~4.2 million barrels of crude oil per day (import dependence ~85–90%), sourced primarily from the Arabian Gulf, Russia, and West Africa. Each corridor passes through a different maritime chokepoint. When those chokepoints are disrupted, the simulation reveals how sourcing strategies differ in resilience, cost, and recovery speed.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                            SUPPLY SOURCES                                  │
│  Gulf (Saudi/UAE/Iraq)  Russia (Urals/ESPO)  West Africa   UAE ADCOP Pipe │
│  $2.00/bbl freight      $3.00/bbl net cost   $5.00/bbl     $4.00/bbl      │
│  12-day one-way         30-day one-way (Suez) 22-day Cape  12-day         │
│  ~30-40% of imports     ~35-40% of imports   ~10-15%       (bypass only)  │
└──────────┬──────────────────────┬─────────────────┬──────────┬────────────┘
           │                      │                 │          │
      [Hormuz Strait]        [Red Sea/Suez]   [Cape Route] [Pipeline]
      cap: 10 ships            cap: 8 ships    unlimited    no chokepoint
      base: 2 days transit     base: 4 days               (bypasses Hormuz)
           │                      │                 │          │
           └──────────────────────┴─────────────────┴──────────┘
                                  │
                        ┌─────────▼──────────┐
                        │   India Terminals   │
                        │  Commercial storage │
                        │  Demand: 4.2M bbl/d │
                        │  Max: 100M bbl      │
                        └─────────┬───────────┘
                                  │ (if ≤ 10M bbl critical)
                        ┌─────────▼───────────┐
                        │ Strategic Petroleum  │
                        │ Reserve (SPR)        │
                        │ 40M bbl cap, 64% full│
                        │ 0.8M bbl/day release │
                        └─────────────────────┘
```

---

## Architecture

```
OilSim/
├── config/params.py        ← All constants, source configs, 8 scenarios
├── core/
│   ├── chokepoint.py       ← SimPy Resource + disruption severity + congestion + seasonal weather
│   ├── port.py             ← Inventory buffer + demand drain + elasticity + info delay
│   ├── spr.py              ← SPR with threshold-triggered release + refill process
│   ├── tanker.py           ← Tanker entity + Fleet (simpy.Store pool) + fleet shocks
│   └── disruption.py       ← Deterministic DisruptionEngine + StochasticDisruptionEngine
├── strategies/policy.py    ← Four ordering strategies (see below)
├── simulation/
│   ├── engine.py           ← Wires all components, feature flags, scenario processes
│   └── metrics.py          ← Cost, shortage, fleet utilization, per-source breakdown
├── experiments/runner.py   ← Scenario × strategy × replication matrix
├── analysis/results.py     ← Aggregation, CSV export, comparison tables
└── main.py                 ← Entry point
```

### Key SimPy Design Patterns

| Component | SimPy Mechanism | Why |
|---|---|---|
| Chokepoint | `simpy.Resource(capacity=N)` | Limits simultaneous transits; creates natural queuing |
| Fleet pool | `simpy.Store` | Tankers are objects borrowed and returned |
| Demand | Hourly `timeout(1)` process | Continuous depletion modeled as event stream |
| Tanker voyage | Generator with `yield from cp.transit()` | Each voyage chains loading → transit → unloading → return |
| SPR | Hourly `timeout(1)` monitor | Event-driven threshold trigger |
| Disruption | `timeout(start)` → modify → `timeout(duration)` | Timed severity injection |
| Stochastic disruption | `expovariate(1/mean)` inter-arrival | Poisson disruption arrivals |
| Pipeline bypass | `_disabled_sources` set + activation process | Pipeline starts disabled; activated only after sustained Hormuz disruption |

---

## Simulation Parameters

All constants are calibrated to real-world data (see [Real-World Calibration](#real-world-calibration) section below).

| Parameter | Value | Real-World Basis |
|---|---|---|
| Duration | 200 days | Enough to observe full disruption + recovery cycle |
| Fleet size | 120 tankers | India charters ~100–150 crude tankers at any time |
| Average cargo | 1.5M bbl | Weighted avg: 55% VLCC (1.9M) + 30% Suezmax (1.0M) + 15% Aframax (0.6M) |
| Daily demand | 4.2M bbl/day | India crude imports 4.0–4.5M bbl/day (85–90% import dependence) |
| Initial inventory | 60M bbl | ~14 days forward cover at commercial terminals |
| Max storage | 100M bbl | Combined commercial crude-tank capacity across all terminals |
| Reorder point | 25M bbl | ~6 days — triggers replenishment orders |
| Target inventory | 70M bbl | ~17 days — comfortable operating buffer |
| Critical threshold | 10M bbl | ~2.4 days — triggers SPR emergency draw |
| SPR capacity | 40M bbl | 5.33M metric tonnes across 3 caverns (Vizag, Padur, Mangaluru) |
| SPR fill level | 25.6M bbl | ~64% full (3.37M MT of 5.33M MT as of 2024–25) |
| SPR release rate | 0.8M bbl/day | Pipeline throughput constraint (0.7–1.0M bbl/day range) |
| Gulf voyage (one-way) | 12 days | Saudi/UAE/Iraq to Indian west-coast ports |
| Russia voyage (one-way) | 30 days | Baltic/Black Sea via Suez Canal to India |
| Africa voyage (one-way) | 22 days | Nigeria/Angola via Cape of Good Hope to India |
| Gulf freight | $2.00/bbl | Normal-conditions ocean freight (PPAC data: $1.5–3.0/bbl) |
| Russia freight | $3.00/bbl | Net cost after ~$10–15/bbl Urals discount offsets high freight |
| Africa freight | $5.00/bbl | Aframax/Suezmax benchmark ($3–6/bbl, Kpler) |
| Pipeline tariff | $4.00/bbl | UAE ADNOC/ADCOP Fujairah terminal cost |

---

## Strategies

Each strategy is an **ordering policy** — a set of rules that decides *when* to order oil, *which source to order from*, and *how to react to disruptions*. The simulation runs the same scenario through each strategy and compares outcomes.

Every strategy shares the same trigger rule: **order when inventory falls below 25 million barrels** and at least one tanker is free. What differs is which source gets chosen once that trigger fires.

---

### 1. Cost-Focused

**One-line rule:** Always buy from the cheapest available route, unless that route is essentially destroyed (70%+ blocked).

**Decision rules:**
1. Each day, check whether each chokepoint's status is below **0.3** (the disruption threshold). If yes, that chokepoint is "disrupted."
2. Any source whose route passes through a disrupted chokepoint is moved to the back of the queue. Safe sources go first.
3. Within each group, sources are sorted by base transport cost: **Gulf ($2.00) → Russia ($3.00) → Africa ($5.00)**.
4. Result: Gulf wins almost always. Russia wins only if Hormuz is blocked. Africa is last resort.

**What "threshold 0.3" means in practice:** A chokepoint at status 0.5 (50% blocked, ships take twice as long) is *not* considered disrupted by this strategy. It will keep routing ships through a heavily congested Hormuz even as queue times balloon.

**Why this hurts in long_war:** When both Hormuz (status 0.1) and Red Sea (status 0.5) are disrupted, Hormuz is finally below 0.3 so Gulf is deprioritised — but Red Sea is still 0.5 which is above 0.3, so Russia ships keep going through a slow, congested Red Sea. Those tankers get stuck for days in the queue, tying up the fleet, and new orders can't be dispatched because there are no free tankers.

**Best for:** No disruption, short conflict (fast Gulf round trips = maximum barrels/day)

---

### 2. Diversified

**One-line rule:** Never rely on a single source — cycle through all available sources in rotation, skipping ones whose routes are blocked.

**Decision rules:**
1. Disruption threshold is **0.7** — a chokepoint at 30%+ reduced capacity is already considered disrupted.
2. Build a priority list: safe sources first (sorted cheapest-to-most-expensive), then unsafe sources.
3. Instead of always picking #1 on the list, use a **round-robin**: order 1 → source A, order 2 → source B, order 3 → source C, order 4 → source A again, etc. The index is `order_count % number_of_sources`.
4. This guarantees all non-disrupted sources share the load, regardless of cost.

**What this looks like operationally:** Under no disruption you'll see Gulf, Russia, Africa, Gulf, Russia, Africa… cycling. Under Hormuz disruption (Russia and Africa are safe), it cycles Russia, Africa, Russia, Africa — never Gulf.

**Why it's rarely the best:** It always dilutes throughput. In calm conditions you're wasting fleet capacity on slow Africa voyages when Gulf is faster. In a crisis you're still spreading between 2–3 sources instead of fully committing to the safest one. It hedges without ever optimising.

**Best for:** Scenarios with moderate, uncertain disruption where pure cost-focus is too risky but full resilience is too expensive

---

### 3. Resilient

**One-line rule:** Avoid every chokepoint you possibly can, even at full price, even during calm periods.

**Decision rules:**
1. Disruption threshold is **0.9** — a chokepoint is "disrupted" even if it's only 10% degraded.
2. Sort sources by **number of chokepoints on the route, then by cost** (both ascending). Sources with zero chokepoints always come first.
3. Priority order: **Africa (0 chokepoints, $5.00) → Gulf Pipeline (0 chokepoints, $4.00, if active) → Russia (1 chokepoint: Red Sea, $3.00) → Gulf (1 chokepoint: Hormuz, $2.00)**.
4. This means Africa is the default source in *every* scenario, every day, unless it's at capacity. Gulf is only used if Africa, the pipeline, and Russia are all unavailable.

**What "no chokepoints" means:** Africa ships travel the Cape of Good Hope route — open ocean, no strait to queue at, no disruption risk, fully predictable 26.5-day round trip. The flip side is that each tanker delivers oil less frequently than a Gulf tanker (17.5-day round trip). With 120 tankers the fleet has enough capacity to cover demand on any single source; resilient pays more per barrel but stays fully immune to chokepoint disruptions.

**Throughput math (with calibrated fleet):** 120 tankers × 1.5M bbl/cargo on Africa (22-day one-way = ~26.5-day round trip) = ~6.8M bbl/day throughput capacity >> 4.2M bbl/day demand. The ordering policy limits actual flow to match demand; no structural shortage exists in normal conditions.

**Best for:** Long war (both Hormuz + Red Sea disrupted simultaneously — Africa is completely immune)

---

### 4. Adaptive

**One-line rule:** Watch the chokepoints in real time. Be cost-focused when things are calm, switch to resilient when things get bad.

**Decision rules:**
1. Every 24-hour ordering cycle, compute the **average status across all active chokepoints**.
2. Use that average to set the disruption threshold dynamically:
   - avg status ≥ 0.8 (calm) → threshold = **0.3** → behaves exactly like Cost-Focused
   - avg status 0.5–0.8 (moderate stress) → threshold = **0.7** → behaves like Diversified
   - avg status < 0.5 (crisis) → threshold = **0.9** → behaves like Resilient
3. Because the threshold changes, the source priority list recalculates every cycle.

```
Chokepoint health:  ████████████░░░░░░░░░░░░░░░░░░░░░░
                    1.0        0.8      0.5      0.0
Mode:               [Cost-Focused] [Diversified] [Resilient]
Threshold:               0.3           0.7          0.9
```

**The lag problem:** The strategy reacts *after* it observes the degraded status. If Hormuz drops from 1.0 to 0.1 overnight, adaptive will route one more costly Gulf shipment (the cycle that triggered before the update) before switching. In stochastic scenarios with gradual degradation this lag is small; in sudden-onset scenarios it costs one cycle.

**Why it can beat all static strategies:** In a long war that eventually ends, adaptive pays cheap Gulf prices during the calm period, switches to resilient during the crisis, then switches back — rather than paying Africa's premium for the entire 200-day run (as resilient does) or getting stuck during the crisis (as cost-focused does).

**Best for:** Stochastic conflict, any scenario with variable disruption timing

---

### How the strategies compare at a glance

| | Cost-Focused | Diversified | Resilient | Adaptive |
|---|---|---|---|---|
| Disruption threshold | 0.3 | 0.7 | 0.9 | 0.3 → 0.9 (dynamic) |
| Default first source | Gulf ($2.00) | Cycles all | Africa ($5.00) | Gulf → Africa |
| Source selection method | Cheapest safe first | Round-robin rotation | Fewest chokepoints first | Depends on current mode |
| Reacts to mild disruption? | No | Yes (≥30% degraded) | Yes (≥10% degraded) | Yes (mode-dependent) |
| Normal-conditions cost | Lowest | Medium | Highest | Lowest |
| Severe disruption cost | Spikes sharply | Moderate | Flat | Moderate |
| Real-world analogue | India's pre-2022 policy | Diversified oil basket | Full Cape-route switch | Adaptive hedging strategy |

---

## What are Replications?

A replication is **one complete run of the simulation** from day 0 to the end date with a fixed random seed.

The simulation has stochastic (random) elements — tanker breakdown timing, stochastic disruption arrival times, noise in transit duration, random repair durations. Each replication uses a different seed, so these random events unfold differently. Running 5 replications is like running the same geopolitical scenario 5 times in 5 parallel universes and averaging the results.

**Why replications matter:**
- A single run might get lucky (the breakdown happens during a calm period) or unlucky (it happens mid-crisis). The result from one run can be misleading.
- With N replications the dashboard shows the **mean ± standard deviation** across all runs. The inventory chart's shaded band is exactly this uncertainty: wider band = more variance across replications = the strategy's performance is less predictable.
- For purely deterministic scenarios (e.g. `no_disruption` with all feature flags off), replications will produce nearly identical results — the std dev will be ~0. This is a sanity check.
- For stochastic scenarios (`stochastic_conflict`) or when feature flags like `Tanker Breakdowns` are on, you need more replications (5–10) to get stable mean estimates.

**Performance:** Each simulation run takes ~25ms, so even 200 reps across 4 strategies completes in under 20 seconds.

**Rule of thumb:**
- 5–10 reps: quick exploration during development
- 30 reps: good default — stable means, reasonable confidence intervals (UI default)
- 100 reps: recommended for final results or publication-quality comparisons
- 200 reps: maximum precision; variance estimates converge fully

---

## Disruption Scenarios

### Deterministic (fixed schedule)

| Scenario | What Happens | Duration | Severity |
|---|---|---|---|
| `no_disruption` | Normal operations | — | — |
| `short_conflict` | Hormuz at 50% capacity | Days 30–60 | status=0.5 |
| `medium_blockade` | Hormuz at 20% capacity | Days 30–120 | status=0.2 |
| `long_war` | Hormuz at 5% + Red Sea at 10% + 15 tankers lost day 30 | Days 15–190 / Days 25–180 | 0.05 / 0.10 |
| `all_out_war` | Hormuz 2% + Red Sea 2% + Russia sanctioned + 65 tankers lost | From day 7/10 | 0.02 / 0.02 |
| `cape_disruption` | Africa route closed + Hormuz 15% + Red Sea 20% | Days 0–200 | 0.15 / 0.20 |

### Regional / Event-Driven Scenarios

| Scenario | What Happens | Key Feature |
|---|---|---|
| `houthi_red_sea` | Red Sea at 40% capacity for 60 days | Based on 2024 Houthi attacks; isolates Russia route disruption |
| `russia_sanctions` | Russia source shut down for 100 days | Source shutdown mechanism; tests Gulf + Africa fallback |
| `tanker_strike` | 25 tankers permanently destroyed on day 10 | Fleet shock; tests throughput resilience under reduced capacity |
| `stochastic_conflict` | Poisson-distributed random disruptions | Randomised severity + duration; enables Monte Carlo analysis |

**How severity maps to transit time:**
```
transit_time = base_transit / status + queue_length × 0.5h + seasonal_multiplier + noise
```
- status=1.0 → normal (48h through Hormuz)
- status=0.5 → 2× slower (96h) + queue buildup
- status=0.1 → 10× slower (480h) + severe congestion cascade

---

## Implemented Improvements

All improvements are **opt-in via `config` dict** — existing tests pass `config=None` so none of these activate by default.

```python
engine = SimulationEngine(
    SCENARIOS['long_war'], 'adaptive', seed=42,
    config={
        'enable_panic_ordering':     True,
        'enable_demand_elasticity':  True,
        'enable_seasonal_weather':   True,
        'enable_freight_dynamics':   True,
        'enable_pipeline_bypass':    True,
        'enable_information_delay':  True,
        'information_delay_hours':   48,
        'enable_tanker_breakdowns':  True,
        'enable_spr_refill':         True,
    },
)
```

---

### Stochastic Disruptions (`StochasticDisruptionEngine`)

Disruptions arrive as a **Poisson process** with exponentially-distributed inter-arrival times, random severity, and exponential duration. Replaces the fixed schedule with probabilistic geopolitical shocks.

```python
sde.schedule_stochastic(
    chokepoint_names=['Hormuz', 'Red_Sea'],
    mean_interval_days=60,         # average one disruption per 60 days
    severity_range=(0.1, 0.7),     # uniform draw
    duration_mean_days=45,         # exponential, mean 45 days
)
```

Enables Monte Carlo analysis: run multiple replications with `seed=None` to get a distribution of shortage outcomes.

---

### Adaptive Strategy (dynamic threshold)

The `adaptive` strategy updates `disruption_threshold` every ordering cycle based on observed mean chokepoint status. It switches between cost-focused, diversified, and resilient behaviour in real-time — no manual tuning needed.

---

### Panic Ordering / Bullwhip Effect (`enable_panic_ordering`)

When a disruption is detected, the ordering process dispatches `panic_multiplier × 3` tankers instead of the normal 3. This creates the **bullwhip effect**: over-ordering floods chokepoints → congestion spikes → delayed deliveries → more shortage → more panic → oscillations in inventory time series.

```python
config={'enable_panic_ordering': True, 'panic_multiplier': 2}
```

---

### Demand Elasticity (`enable_demand_elasticity`)

When inventory is critically low, refineries reduce throughput (rationing). This attenuates shortage and extends the time before stockout.

| Inventory level | Demand multiplier |
|---|---|
| > 30% of max | 1.00 (normal operations) |
| 10–30% of max | 0.85 (15% rationing) |
| < 10% of max | 0.60 (40% emergency rationing) |

---

### Information Delay (`enable_information_delay`)

Ordering decisions are based on an N-hour-old inventory reading rather than real-time inventory. This causes overshoot/undershoot cycles: orders are placed based on what inventory was, not what it is — a fundamental cause of supply chain oscillations.

```python
config={'enable_information_delay': True, 'information_delay_hours': 48}
```

---

### Seasonal Weather (`enable_seasonal_weather`)

Indian Ocean cyclone season (days 120–330 of each simulated year) slows maritime routes via a sinusoidal transit-time multiplier peaking at **1.30×** at the September peak.

```
Multiplier = 1 + sin(π × (day − 120) / 210) × 0.30
```

Affects all tanker transits through Chokepoint objects; can compound with disruption delays.

---

### Freight Rate Dynamics (`enable_freight_dynamics`)

When fleet utilization exceeds 70%, spot-market scarcity drives a quadratic freight premium on top of the base cost. Models the observed behaviour during the 2024 Houthi attacks (Baltic Dirty Tanker Index spiked 3×).

```
freight_multiplier = 1 + ((utilization − 0.70) / 0.30)² × 2.0
```

---

### UAE ADCOP Pipeline Bypass (`enable_pipeline_bypass`)

The Gulf_Pipeline source is **disabled by default** (in `_disabled_sources`). When Hormuz is severely disrupted (status < 0.3) and remains so for `activation_delay_days` (default 10), the pipeline is activated and becomes available as a source.

- No chokepoints: fully immune to Hormuz disruption
- Smaller batches: 500,000 bbl per delivery vs 1,500,000 bbl by tanker
- Higher tariff: $4.00/bbl (pipeline cost vs $2.00/bbl Gulf tanker freight)

The resilient strategy prioritises it (0 chokepoints) once activated.

---

### Fleet Shocks (`tanker_strike` scenario)

The `_fleet_shock_process` permanently removes tankers from the `simpy.Store` fleet pool at a specified simulation day. Models missile strikes or sudden fleet loss events.

```python
'fleet_shocks': [{'tankers_lost': 5, 'day': 30}]
```

---

### Source Shutdowns / Sanctions (`russia_sanctions` scenario)

The `_source_shutdown_process` adds a source to `_disabled_sources` at a specified day and removes it after a duration. The ordering policy automatically routes around the disabled source.

---

### SPR Automatic Refill (`enable_spr_refill`)

When port inventory is comfortably above the target level, the SPR refill process transfers oil from the port to the SPR at `SPR_REFILL_RATE_BBL_PER_DAY`. Tracks `spr.total_refilled` for metrics.

---

### Tanker Breakdowns (`enable_tanker_breakdowns`)

Each tanker voyage has a probability of breakdown during the return leg, drawn from a Poisson model with `tanker_mtbf_hours` mean time between failures. Breakdown delays the tanker's return to the pool by a Gaussian-distributed repair time.

```python
config={'enable_tanker_breakdowns': True, 'tanker_mtbf_hours': 365 * 24}
```

---

## Real-World Calibration

This section documents the real-world data used to calibrate simulation constants, with sources. All values are as of 2024–2025 unless otherwise noted.

---

### India's Crude Oil Demand

| Metric | Value | Source |
|---|---|---|
| Total oil demand | ~4.5M bbl/day | Energy Economic Times (2024) |
| Import dependence | ~85–90% | SEAIR crude import data |
| Crude imports | 4.0–4.5M bbl/day | Used 4.2M bbl/day in simulation |

India is the world's third-largest oil importer. Domestic production covers only ~10–15% of needs; the rest is imported via tanker and pipeline.

---

### Tanker Fleet

| Metric | Value | Source |
|---|---|---|
| Active crude tankers (India) | ~100–150 vessels | Tribune India (charter activity) |
| Fleet ownership | Predominantly chartered | Times of India (PSU charter spend) |
| Planned Indian-owned fleet | 100–112 tankers by 2040 | MyInd (Make in India tanker plan) |
| VLCC capacity | 1.8–2.0M bbl | EIA vessel definitions |
| Suezmax capacity | 0.8–1.2M bbl | Oil Capacity Check |
| Aframax capacity | 0.4–0.8M bbl | Septrans (liquid cargo vessels) |
| Volume split | 55% VLCC / 30% Suezmax / 15% Aframax | Inferred from Kpler trade data |
| **Simulation value** | **120 tankers × 1.5M bbl/cargo** | Weighted average cargo |

India's state refiners (IOCL, BPCL, HPCL, MRPL, GAIL) rely almost entirely on the **time-charter market** — they rent vessels rather than own them, making the effective fleet size highly elastic to market conditions.

---

### Voyage Times (one-way, sea leg)

| Route | One-Way Duration | Source |
|---|---|---|
| Gulf (Saudi/UAE/Iraq) → India | 10–14 days | MOL Service (Middle East–Asia routes) |
| Russia (Baltic/Black Sea) → India via Suez | 25–35 days | Sberbank India (Russia–India cargo routes) |
| Russia (ESPO Pacific) → India | 12–18 days | Datamarnews (ESPO Pacific transit) |
| West Africa (Nigeria/Angola) → India | 20–25 days | Hellenic Shipping News (crude tanker outlook) |
| VLCC loading time (at source) | 1.0–2.0 days | Oil Capacity Check |
| Discharge time (Indian port) | 1.5–2.5 days | Splash247 (VLCC at Mundra) |

**Lead time from order to delivery (Gulf):** 30–50 days total (vessel scheduling + voyage + port handling). Source: ET Infra (Deendayal Port Authority).

**Simulation values:** Gulf 12-day one-way (288h), Russia 30-day via Suez (720h), Africa 22-day Cape (528h), 1.5-day loading (36h), 2-day discharge (48h).

---

### Port Storage and Inventory

| Metric | Value | Source |
|---|---|---|
| Combined crude stocks (tanks + SPR + in-transit) | ~100M bbl | Daily Excelsior / Kpler analysis |
| Days of forward cover (combined) | 40–45 days | Daily Excelsior (Hormuz disruption study) |
| Total storage coverage (crude + products) | ~74 days | NDTV (government statement) |
| "Tight" forward cover threshold | ~20–30 days | Inferred from energy-security commentary |
| **Commercial land storage (simulation max)** | **100M bbl** | Combined major terminal capacity |
| **Normal operating level (simulation start)** | **60M bbl (~14 days)** | Conservative operating buffer |

---

### Strategic Petroleum Reserve (SPR)

| Metric | Value | Source |
|---|---|---|
| Total capacity | 5.33M metric tonnes ≈ **40M bbl** | PMFIAS (SPR fact sheet) |
| Sites | Visakhapatnam (1.33 MT), Padur (2.5 MT), Mangaluru (1.5 MT) | PMFIAS |
| Current fill level | ~64% ≈ **3.37M MT (25.6M bbl)** | LinkedIn / Business Today India (2024) |
| Emergency release capacity | 0.7–1.0M bbl/day | IOCL SPR documentation |
| Management | Government-owned, separate from commercial | Policy documentation |
| **Simulation values** | **40M bbl cap, 25.6M bbl initial, 0.8M bbl/day release** | Calibrated to above |

The SPR is managed separately from commercial storage and is held as a purely strategic government reserve for supply emergencies.

---

### Import Source Mix (2023–2025)

| Source | Share of Imports | Notes |
|---|---|---|
| Russia (Urals + ESPO) | **35–40%** | Post-2022 surge; discounted Urals crude |
| Gulf (Iraq, Saudi, UAE, Kuwait) | **30–40%** | Long-standing primary supplier |
| West Africa (Nigeria, Angola) | **10–15%** | Flexible spot purchases |
| Americas (US, Brazil) | **5–10%** | Growing diversification |

Source: KNN India (import share data, H1 2025), Vajiramandravi (oil basket analysis).

Russia surpassed the Gulf as India's top supplier in 2022–23 after Western sanctions made Urals crude available at significant discounts. India's long-term contracts cover ~40–60% of volume; the rest is spot purchases.

---

### Transport Costs (USD per barrel, freight only)

| Route | Normal Freight | Disruption Premium | Source |
|---|---|---|---|
| Gulf → India | $1.5–3.0/bbl | +100–300% war-risk (Hormuz) | PPAC price build-up sheets |
| Russia → India | $10–20/bbl all-in | Partially priced in (sanctions+insurance) | ScanX / Economic Times |
| West Africa → India | $3–6/bbl | +100–300% war-risk (if Red Sea) | Kpler Q1-2026 outlook |
| UAE Pipeline (ADCOP) | ~$4/bbl tariff | n/a (bypasses Hormuz) | Estimated |

**Important:** Russia's high freight ($10–20/bbl post-sanctions) is partially offset by the **Urals FOB price discount** (~$10–15/bbl below Brent at peak). The simulation models the net effective supply cost rather than separating crude price from freight.

---

## Sample Results (100-day run, 40 replications)

Calibrated results (100-day run, 40 replications, no feature flags — 120 tankers × 1.5M bbl, 4.2M bbl/day demand):

```
Scenario             Strategy        Shortage(h)  DFR     $/bbl   Cost($B)
--------------------------------------------------------------------------
no_disruption        cost_focused         0.0    1.000    2.00     0.76
no_disruption        diversified          0.0    1.000    3.32     1.26
no_disruption        resilient            0.0    1.000    5.00     1.87
no_disruption        adaptive             0.0    1.000    2.00     0.76

short_conflict       cost_focused         0.0    1.000    2.57     0.91
short_conflict       diversified          0.0    1.000    3.58     1.34
short_conflict       resilient            0.0    1.000    5.00     1.87
short_conflict       adaptive             0.0    1.000    2.71     1.03

medium_blockade      cost_focused       402.8    0.832    2.63     0.67  ← keeps routing via congested Hormuz
medium_blockade      diversified          0.0    1.000    3.86     1.44
medium_blockade      resilient            0.0    1.000    5.00     1.87
medium_blockade      adaptive             0.0    1.000    3.54     1.34  ← switches to diversified mode

long_war             cost_focused         0.0    1.000    4.58     1.66  ← pivots to Africa once Hormuz<threshold
long_war             diversified          0.0    1.000    4.76     1.78
long_war             resilient            0.0    1.000    5.00     1.87
long_war             adaptive             0.0    1.000    4.66     1.72

all_out_war          cost_focused       136.0    0.943    5.00     1.42  ← capacity floor: same for all
all_out_war          diversified        136.0    0.943    5.00     1.42
all_out_war          resilient          136.0    0.943    5.00     1.42
all_out_war          adaptive           136.0    0.943    5.00     1.42

cape_disruption      cost_focused      1093.7    0.544    4.55     0.34  ← Africa closed, no safe route
cape_disruption      diversified        869.6    0.638    5.24     0.68  ← best: uses both disrupted routes
cape_disruption      resilient         1094.2    0.544    4.55     0.34
cape_disruption      adaptive          1095.6    0.543    4.55     0.34

houthi_red_sea       cost_focused         0.0    1.000    2.00     0.76  ← Gulf unaffected by Red Sea
houthi_red_sea       diversified          0.0    1.000    3.50     1.32
houthi_red_sea       resilient            0.0    1.000    5.00     1.87
houthi_red_sea       adaptive             0.0    1.000    3.50     1.32

russia_sanctions     cost_focused         0.0    1.000    2.00     0.76  ← Gulf covers full demand
russia_sanctions     diversified          0.0    1.000    3.38     1.28
russia_sanctions     resilient            0.0    1.000    5.00     1.87
russia_sanctions     adaptive             0.0    1.000    2.00     0.76

tanker_strike        cost_focused       428.7    0.821    3.24     0.75  ← fleet shock causes throughput gap
tanker_strike        diversified          0.0    1.000    3.79     1.44
tanker_strike        resilient            0.0    1.000    5.00     1.87
tanker_strike        adaptive             0.0    1.000    3.44     1.27

stochastic_conflict  cost_focused        77.4    0.968    2.51     0.82  ← surprised by random disruptions
stochastic_conflict  diversified          0.0    1.000    3.70     1.39
stochastic_conflict  resilient            0.0    1.000    5.00     1.87
stochastic_conflict  adaptive             0.0    1.000    3.07     1.15  ← best value: pays premium only when disrupted
```

**DFR** = Demand Fulfillment Rate (1.0 = zero shortage, 0.5 = 50% of demand unmet)

### Key Findings

1. **Cost-focused fails under sustained moderate disruptions** — medium_blockade (Hormuz at 20%) causes 402h shortage; tanker_strike (−25 tankers) causes 428h. Both are survivable by every other strategy, revealing that lean single-source routing has no slack.

2. **All strategies tie in all-out war** — when 65 tankers are destroyed and every chokepoint is near-closed simultaneously, Africa is the only viable route but has insufficient throughput (55 tankers × 1.5M bbl / 24.5-day trip ≈ 3.4M bbl/day < 4.2M demand). No ordering policy can compensate for a physical capacity floor.

3. **Cape disruption is the hardest scenario** — closing Africa + disrupting Hormuz + disrupting Red Sea leaves no safe route. Diversified's multi-route round-robin (spreading across both disrupted Gulf and Russia routes) reduces shortage by 20% vs single-route strategies, but DFR remains ~0.55 for everyone.

4. **Adaptive offers the best cost/resilience trade-off** — in calm markets it matches cost_focused ($2.00/bbl); under stress it matches resilient/diversified. Stochastic conflict demonstrates this clearly: $3.07/bbl and zero shortage, vs resilient's $5.00/bbl or cost_focused's 77h shortage.

5. **Resilient is costly but nearly bullet-proof** — DFR = 1.000 in 8 of 10 scenarios (only all_out_war and cape_disruption breach it, and those breach every strategy). It pays $5.00/bbl continuously, including in perfectly calm conditions.

6. **Houthi and Russia sanctions cause zero shortage** — both are single-route disruptions that the fleet absorbs through rerouting. Consistent with observed 2022–24 market outcomes where Gulf + Africa covered the gap.

---

## Outputs

- **Console table:** mean shortage hours, total cost, $/bbl, demand fulfillment rate per scenario/strategy
- **results.csv:** raw per-replication data for external analysis
- **Metrics tracked:** inventory time-series, cost log per delivery, fleet utilization, shortage timestamps, SPR level log, chokepoint transit log, per-source delivery counts and barrel volumes

---

## Running Experiments

```python
from experiments.runner import ExperimentRunner
from analysis.results import ResultsAnalyzer

runner = ExperimentRunner(
    scenarios=['no_disruption', 'long_war', 'stochastic_conflict'],
    strategies=['cost_focused', 'resilient', 'adaptive'],
    num_replications=10,
    duration_hours=365 * 24,   # full year
)
results = runner.run()
analyzer = ResultsAnalyzer(results)
analyzer.print_summary()
analyzer.to_csv("my_results.csv")
```

---

## Extending the Simulator

| What to change | Where to change it |
|---|---|
| New scenario | `config/params.py` → add entry to `SCENARIOS` |
| New strategy | `strategies/policy.py` → add threshold to `_DISRUPTION_THRESHOLDS`, branch in `get_source_priority()` |
| New source | `config/params.py` → add entry to `SOURCES` with `chokepoints` list |
| New chokepoint | `config/params.py` → add to `CHOKEPOINTS`, reference in a source's `chokepoints` list |
| New feature flag | `simulation/engine.py` → add key to `_DEFAULT_CFG`, wire process in `run()` |

---

## Dependencies

```
simpy >= 4.0.1    # discrete-event simulation
pytest >= 7.0     # testing
```

Standard library only for analysis (`csv`, `statistics`, `random`, `logging`).
