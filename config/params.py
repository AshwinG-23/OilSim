# Simulation time unit: hours
SIM_DURATION_HOURS = 200 * 24  # 200 days

# ── Fleet ──────────────────────────────────────────────────────────────────
# India's oil marketing companies charter ~100–150 crude tankers at any given time.
# Mix: ~55% VLCC (1.9M bbl), ~30% Suezmax (1.0M bbl), ~15% Aframax (0.6M bbl)
# → weighted-average cargo ≈ 1.5M bbl.
# Source: Tribune India (tanker charter activity), EIA (vessel class capacities)
NUM_TANKERS          = 120
TANKER_CAPACITY_BBL  = 1_500_000   # weighted avg across VLCC/Suezmax/Aframax

# ── Port (India aggregate import terminals) ────────────────────────────────
# India's combined commercial crude-tank storage across all major import
# terminals (Mundra, Kandla, Mumbai, Visakhapatnam, etc.) is ~60–80 M bbl.
# Normal operating level: 40–60 days forward cover; "tight" below 20–30 days.
# India's crude imports: 4.0–4.5 M bbl/day (import dependence ~85–90%).
# Source: Kpler / Daily Excelsior (100 M bbl combined incl. SPR + in-transit),
#         NDTV / SEAIR (import volumes), Energy ET (4.5 M bpd demand forecast)
PORT_INITIAL_INVENTORY_BBL  = 60_000_000   # ~14 days supply at 4.2 M bbl/day
PORT_MAX_INVENTORY_BBL      = 100_000_000  # combined commercial terminal capacity
PORT_DAILY_DEMAND_BBL       = 4_200_000    # India crude imports ~4.0–4.5 M bbl/day
PORT_REORDER_POINT_BBL      = 25_000_000   # ~6 days — triggers replenishment orders
PORT_TARGET_INVENTORY_BBL   = 70_000_000   # ~17 days — comfortable operating buffer
PORT_CRITICAL_INVENTORY_BBL = 10_000_000   # ~2.4 days — triggers SPR emergency draw

# ── Strategic Petroleum Reserve ────────────────────────────────────────────
# Three underground caverns: Visakhapatnam (1.33 MT), Padur (2.5 MT),
# Mangaluru (1.5 MT) = 5.33 million metric tonnes ≈ 40 M bbl.
# Current fill: ~64% (3.37 MT of 5.33 MT capacity as of 2024–25).
# Emergency release: 0.7–1.0 M bbl/day (pipeline-throughput limited).
# Source: PMFIAS (SPR capacity), LinkedIn/BusinessToday (64% fill level),
#         IOCL (SPR filling mechanism)
SPR_INITIAL_LEVEL_BBL       = 25_600_000   # 64% of 40 M bbl (3.37 M MT)
SPR_MAX_CAPACITY_BBL        = 40_000_000   # 5.33 M MT × 7.5 bbl/MT
SPR_DAILY_RELEASE_RATE_BBL  =    800_000   # 0.8 M bbl/day pipeline limit
SPR_REFILL_RATE_BBL_PER_DAY =    400_000   # conservative refill rate

# ── Sources: transport cost + timing + route ───────────────────────────────
# Freight rates (ocean, normal conditions):
#   Gulf → India:   $1.5–3.0/bbl   (PPAC price build-up sheets)
#   Russia → India: $10–20/bbl all-in (post-2022 sanctions premium + insurance);
#                   offset by $10–15/bbl Urals FOB discount → net cost competitive
#   Africa → India: $3–6/bbl       (Aframax/Suezmax benchmark, Kpler)
# War-risk premium (Hormuz/Red Sea): +100–300% during high-tension periods.
# Source: Bharat Petroleum PPAC, ScanX / Economic Times, Kpler Q1-2026 outlook
#
# Voyage times (one-way, sea leg):
#   Gulf → India:   10–14 days  (midpoint 12 days = 288 h)
#   Russia → India: 25–35 days via Suez/Red Sea  (midpoint 30 days = 720 h)
#   Africa → India: 20–25 days Cape route  (midpoint 22 days = 528 h)
# Loading: VLCC 1–2 days; discharge: 1.5–2.5 days at Indian port.
# Source: MOL Service (voyage days), Splash247 (VLCC discharge), Sberbank (Russia route)
SOURCES = {
    'Gulf': {
        'base_cost_per_bbl':  2.00,   # freight $1.5–3.0/bbl, midpoint $2.00
        'loading_time_hours': 36,     # 1.5 days (VLCC loading: 1–2 days)
        'return_time_hours':  288,    # 12-day return voyage (10–14 days one-way)
        'chokepoints':        ['Hormuz'],
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
    'Russia': {
        'base_cost_per_bbl':  3.00,   # high freight offset by Urals discount
        'loading_time_hours': 48,     # 2 days (Baltic / Black Sea terminals)
        'return_time_hours':  720,    # 30-day return via Suez (25–35 days one-way)
        'chokepoints':        ['Red_Sea'],
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
    'Africa': {
        'base_cost_per_bbl':  5.00,   # freight $3–6/bbl; no crude-price discount
        'loading_time_hours': 60,     # 2.5 days (West African terminals)
        'return_time_hours':  528,    # 22-day return via Cape (20–25 days one-way)
        'chokepoints':        [],     # open ocean — Cape of Good Hope, no bottleneck
        'cargo_bbl':          TANKER_CAPACITY_BBL,
    },
    # UAE ADNOC / ADCOP pipeline: bypasses Hormuz entirely via Fujairah terminal.
    # Activated with a 10-day ramp-up delay after severe Hormuz disruption.
    'Gulf_Pipeline': {
        'base_cost_per_bbl':  4.00,   # pipeline tariff on top of crude price
        'loading_time_hours': 48,     # Fujairah east-of-Hormuz terminal
        'return_time_hours':  288,    # same sailing distance as Gulf sea route
        'chokepoints':        [],     # bypasses Hormuz entirely
        'cargo_bbl':          500_000, # smaller pipeline-size batches
        'pipeline':           True,
        'activation_delay_days': 10,  # 10 days to ramp after Hormuz disruption
    },
}

# Chokepoints: simultaneous-ship capacity + baseline transit time
CHOKEPOINTS = {
    'Hormuz': {
        'capacity':           10,
        'base_transit_hours': 48,    # 2 days through strait
    },
    'Red_Sea': {
        'capacity':           8,
        'base_transit_hours': 96,    # 4 days
    },
}

# ── Disruption scenarios ───────────────────────────────────────────────────

SCENARIOS = {
    'no_disruption': {
        'disruptions': [],
    },

    'short_conflict': {
        # Hormuz at 50 % capacity for 30 days — mild, recoverable
        'disruptions': [
            {'chokepoint': 'Hormuz', 'start_day': 30, 'duration_days': 30, 'severity': 0.5},
        ],
    },

    'medium_blockade': {
        # Hormuz near-closed (20 % capacity) for 90 days — cost_focused starts hurting
        'disruptions': [
            {'chokepoint': 'Hormuz', 'start_day': 30, 'duration_days': 90, 'severity': 0.2},
        ],
    },

    'long_war': {
        # Hormuz and Red Sea both near-closed; 15 tankers lost to conflict.
        # At severity 0.05 / 0.10, strait transit times are 40 + days —
        # Gulf and Russia routes are effectively paralysed.
        'disruptions': [
            {'chokepoint': 'Hormuz',  'start_day': 15, 'duration_days': 175, 'severity': 0.05},
            {'chokepoint': 'Red_Sea', 'start_day': 25, 'duration_days': 155, 'severity': 0.10},
        ],
        'fleet_shocks': [
            {'tankers_lost': 15, 'day': 30},
        ],
    },

    'all_out_war': {
        # Catastrophic scenario: both chokepoints essentially sealed,
        # Russia sanctioned from day 0, and 65 tankers lost to strikes.
        # Only Africa Cape route and UAE pipeline survive — tests every strategy's
        # ceiling when fleet capacity falls below demand.
        'disruptions': [
            {'chokepoint': 'Hormuz',  'start_day': 7,  'duration_days': 200, 'severity': 0.02},
            {'chokepoint': 'Red_Sea', 'start_day': 10, 'duration_days': 200, 'severity': 0.02},
        ],
        'source_shutdowns': [
            {'source': 'Russia', 'start_day': 0, 'duration_days': 200},
        ],
        'fleet_shocks': [
            {'tankers_lost': 65, 'day': 14},
        ],
    },

    'cape_disruption': {
        # Indian Ocean cyclone + piracy closes the Africa Cape route entirely.
        # Simultaneously Hormuz and Red Sea are both significantly disrupted.
        # Resilient strategy is forced off its preferred Africa route —
        # the scenario that most uniquely stresses the resilient approach.
        'disruptions': [
            {'chokepoint': 'Hormuz',  'start_day': 0, 'duration_days': 200, 'severity': 0.15},
            {'chokepoint': 'Red_Sea', 'start_day': 0, 'duration_days': 200, 'severity': 0.20},
        ],
        'source_shutdowns': [
            {'source': 'Africa', 'start_day': 0, 'duration_days': 200},
        ],
    },

    # ── Realistic geopolitical scenarios ──────────────────────────────────
    'houthi_red_sea': {
        # Based on 2024 Houthi attacks; Red Sea near-closed (5 % capacity),
        # all Russia/Suez traffic forced onto longer Cape routes.
        'disruptions': [
            {'chokepoint': 'Red_Sea', 'start_day': 0, 'duration_days': 200, 'severity': 0.05},
        ],
    },

    'russia_sanctions': {
        # Secondary sanctions shut down Russian supply at day 60.
        # Tests how strategies adapt when their cheapest source disappears.
        'disruptions': [],
        'source_shutdowns': [
            {'source': 'Russia', 'start_day': 60, 'duration_days': 140},
        ],
    },

    'tanker_strike': {
        # Missile strike during Hormuz disruption destroys 25 tankers — 21 % of fleet.
        # Combined fleet + chokepoint shock; tests fleet resilience under fire.
        'disruptions': [
            {'chokepoint': 'Hormuz', 'start_day': 30, 'duration_days': 60, 'severity': 0.30},
        ],
        'fleet_shocks': [
            {'tankers_lost': 25, 'day': 30},
        ],
    },

    'stochastic_conflict': {
        # Disruptions arrive as a Poisson process — random timing, severity, duration.
        # Use multiple replications to build a Monte Carlo distribution of outcomes.
        'disruptions': [],
        'stochastic': True,
        'disruption_mean_interval_days': 60,
        'disruption_severity_range':     (0.1, 0.7),
        'disruption_duration_mean_days': 45,
    },
}

STRATEGIES       = ['cost_focused', 'diversified', 'resilient', 'adaptive']
NUM_REPLICATIONS = 5
UNLOADING_TIME_HOURS = 48   # 2 days at port

# ── Feature flags (all off by default → existing tests unaffected) ─────────

ENABLE_TANKER_BREAKDOWNS    = False
TANKER_MTBF_HOURS           = 365 * 24   # mean time between failures: 1 year
TANKER_REPAIR_MEAN_HOURS    = 14 * 24    # mean repair time: 14 days

ENABLE_DEMAND_ELASTICITY    = False      # refineries reduce throughput under shortage
ENABLE_SEASONAL_WEATHER     = False      # Indian Ocean cyclone/monsoon season

ENABLE_PANIC_ORDERING       = False      # over-ordering during disruption (bullwhip)
PANIC_ORDER_MULTIPLIER      = 3          # 3× tankers per order when panicking

ENABLE_INFORMATION_DELAY    = False      # ordering based on delayed inventory signal
INFORMATION_DELAY_HOURS     = 24         # how stale the inventory reading is

ENABLE_SPR_REFILL           = False      # refill SPR during calm periods
ENABLE_FREIGHT_DYNAMICS     = False      # freight rates respond to fleet utilization
ENABLE_PIPELINE_BYPASS      = False      # activate UAE ADCOP pipeline when Hormuz disrupted
