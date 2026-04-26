import math
import random
import simpy
import logging

from config.params import (
    NUM_TANKERS, TANKER_CAPACITY_BBL,
    PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL, PORT_DAILY_DEMAND_BBL,
    PORT_REORDER_POINT_BBL, PORT_TARGET_INVENTORY_BBL, PORT_CRITICAL_INVENTORY_BBL,
    SPR_INITIAL_LEVEL_BBL, SPR_MAX_CAPACITY_BBL, SPR_DAILY_RELEASE_RATE_BBL,
    SPR_REFILL_RATE_BBL_PER_DAY,
    SOURCES, CHOKEPOINTS, SIM_DURATION_HOURS, UNLOADING_TIME_HOURS,
)
from core.chokepoint import Chokepoint
from core.port import Port
from core.spr import SPR
from core.tanker import Fleet
from core.disruption import DisruptionEngine, StochasticDisruptionEngine
from strategies.policy import OrderingPolicy
from simulation.metrics import Metrics

logger = logging.getLogger(__name__)

_DEFAULT_CFG = {
    # Tanker breakdowns (Poisson MTBF model; repair adds delay to return voyage)
    'enable_tanker_breakdowns':  False,
    'tanker_mtbf_hours':         365 * 24,
    'tanker_repair_mean_hours':  14 * 24,
    # Demand elasticity (refineries reduce throughput under shortage)
    'enable_demand_elasticity':  False,
    # Seasonal Indian Ocean weather (monsoon / cyclone multiplier on transit)
    'enable_seasonal_weather':   False,
    # Panic ordering — 3× tankers dispatched when disruption is active (bullwhip)
    'enable_panic_ordering':     False,
    'panic_multiplier':          3,
    # Information delay — ordering based on N-hour-old inventory reading
    'enable_information_delay':  False,
    'information_delay_hours':   24,
    # SPR automatic refill during calm periods
    'enable_spr_refill':         False,
    # Freight dynamics — spot-market premium when fleet utilisation > 70%
    'enable_freight_dynamics':   False,
    # UAE ADCOP pipeline bypass activated after Hormuz disruption
    'enable_pipeline_bypass':    False,
}


class SimulationEngine:
    def __init__(self, scenario_config, strategy_name, seed=None, config=None):
        if seed is not None:
            random.seed(seed)
        self.env = simpy.Environment()
        self.scenario = scenario_config
        self.strategy_name = strategy_name

        # Merge caller config over defaults; existing tests pass nothing → all off
        self._cfg = dict(_DEFAULT_CFG)
        if config:
            self._cfg.update(config)

        # Sources whose orders are currently blocked (pipeline not yet active, sanctions, etc.)
        self._disabled_sources = set()
        if 'Gulf_Pipeline' in SOURCES:
            self._disabled_sources.add('Gulf_Pipeline')   # pipeline off until activated

        self.chokepoints = {
            name: Chokepoint(
                self.env, name, cfg['capacity'], cfg['base_transit_hours'],
                seasonal_weather=self._cfg['enable_seasonal_weather'],
            )
            for name, cfg in CHOKEPOINTS.items()
        }
        self.port = Port(
            self.env, "India_Terminals",
            PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL,
            PORT_DAILY_DEMAND_BBL / 24,
            demand_elasticity=self._cfg['enable_demand_elasticity'],
            info_delay_hours=(self._cfg['information_delay_hours']
                              if self._cfg['enable_information_delay'] else 0),
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

    # ── Helper: current fleet utilisation ratio ───────────────────────────────

    def _fleet_utilization(self):
        busy = self.fleet.total_count - self.fleet.available_count
        return busy / self.fleet.total_count if self.fleet.total_count > 0 else 0.0

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

        # Optional: random breakdown during return leg (extends idle delay)
        if self._cfg['enable_tanker_breakdowns']:
            mtbf = self._cfg['tanker_mtbf_hours']
            voyage_h = order['loading_time_hours'] + order['return_time_hours']
            if random.random() < (voyage_h / mtbf):
                repair_mean = self._cfg['tanker_repair_mean_hours']
                repair_time = abs(random.gauss(repair_mean, repair_mean * 0.35))
                tanker.state = 'repair'
                logger.info(
                    "[%.0fh] Tanker %s breakdown — repair %.0fh",
                    self.env.now, tanker.name, repair_time,
                )
                yield self.env.timeout(repair_time)

        tanker.voyages_completed += 1
        self.fleet.release(tanker)

    # ── Tanker assignment ─────────────────────────────────────────────────────

    def _assign_tanker(self, order):
        tanker = yield self.fleet.request()
        self.env.process(self._tanker_voyage(tanker, order))

    # ── Ordering process (daily) ──────────────────────────────────────────────

    def _ordering_process(self):
        threshold = self.policy.disruption_threshold
        while True:
            yield self.env.timeout(24)

            # Adaptive strategy updates its threshold each cycle
            if self.strategy_name == 'adaptive':
                self.policy.update_adaptive_threshold(self.chokepoints)
                threshold = self.policy.disruption_threshold

            disrupted = [
                name for name, cp in self.chokepoints.items()
                if cp.status < threshold
            ]
            disruption_active = bool(disrupted)

            # Information delay: order based on observed (possibly stale) inventory
            observed_inv = self.port.get_observed_inventory()

            if not self.policy.should_order(self.port, self.fleet,
                                            observed_inventory=observed_inv):
                continue

            order = self.policy.place_order(
                self.port, self.fleet, self.chokepoints, disrupted,
                disabled_sources=self._disabled_sources,
                fleet_utilization=self._fleet_utilization(),
                enable_freight_dynamics=self._cfg['enable_freight_dynamics'],
            )
            if order is None:
                continue

            # Panic ordering: dispatch 3× tankers when disruption detected (bullwhip)
            if disruption_active and self._cfg['enable_panic_ordering']:
                num = min(self._cfg['panic_multiplier'] * 3, self.fleet.available_count)
            else:
                num = min(3, self.fleet.available_count)

            for _ in range(num):
                self.env.process(self._assign_tanker(order))

    # ── Metrics process (hourly) ──────────────────────────────────────────────

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

    # ── Pipeline bypass activation ────────────────────────────────────────────

    def _pipeline_activation_process(self, activation_delay_days=10):
        """Activate Gulf_Pipeline when Hormuz has been disrupted for activation_delay days."""
        if 'Gulf_Pipeline' not in SOURCES:
            return
        severe_threshold = 0.3
        while True:
            yield self.env.timeout(24)
            if self.chokepoints.get('Hormuz') and \
               self.chokepoints['Hormuz'].status < severe_threshold:
                # Hormuz is severely disrupted — wait for pipeline activation delay
                logger.info("[%.0fh] Hormuz disrupted — pipeline activation in %dd",
                            self.env.now, activation_delay_days)
                yield self.env.timeout(activation_delay_days * 24)
                # Re-check still disrupted after delay
                if self.chokepoints['Hormuz'].status < severe_threshold:
                    self._disabled_sources.discard('Gulf_Pipeline')
                    logger.info("[%.0fh] UAE ADCOP pipeline ACTIVATED", self.env.now)
                return  # activate only once

    # ── Source shutdown (sanctions, embargoes) ────────────────────────────────

    def _source_shutdown_process(self, source_name, start_day, duration_days):
        yield self.env.timeout(start_day * 24)
        self._disabled_sources.add(source_name)
        logger.info("[%.0fh] Source '%s' SHUT DOWN (sanctions/embargo)", self.env.now, source_name)

        yield self.env.timeout(duration_days * 24)
        self._disabled_sources.discard(source_name)
        logger.info("[%.0fh] Source '%s' RESTORED", self.env.now, source_name)

    # ── Fleet shock (tanker strike / missile attack) ──────────────────────────

    def _fleet_shock_process(self, tankers_lost, shock_day):
        yield self.env.timeout(shock_day * 24)
        lost = self.fleet.remove_tankers(tankers_lost)
        logger.info("[%.0fh] FLEET SHOCK: %d tankers lost permanently", self.env.now, lost)
        self.metrics.fleet_log.append({
            'time': self.env.now, 'event': 'fleet_shock', 'lost': lost,
        })

    # ── Stochastic disruption setup ───────────────────────────────────────────

    def _setup_stochastic(self):
        sc = self.scenario
        engine = StochasticDisruptionEngine(self.env, self.chokepoints)
        engine.schedule_stochastic(
            chokepoint_names=list(self.chokepoints.keys()),
            mean_interval_days=sc.get('disruption_mean_interval_days', 60),
            severity_range=sc.get('disruption_severity_range', (0.2, 0.7)),
            duration_mean_days=sc.get('disruption_duration_mean_days', 45),
        )

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, duration_hours=None):
        if duration_hours is None:
            duration_hours = SIM_DURATION_HOURS

        # Core processes
        self.env.process(self.port.demand_process())
        self.env.process(self.port.logging_process())
        self.env.process(self.spr.monitor_and_release(self.port, PORT_CRITICAL_INVENTORY_BBL))
        self.env.process(self._ordering_process())
        self.env.process(self._metrics_process())

        # Optional processes
        if self._cfg['enable_spr_refill']:
            self.env.process(self.spr.refill_process(
                self.port, PORT_TARGET_INVENTORY_BBL, SPR_REFILL_RATE_BBL_PER_DAY,
            ))
        if self._cfg['enable_pipeline_bypass']:
            activation_delay = (SOURCES.get('Gulf_Pipeline', {})
                                .get('activation_delay_days', 10))
            self.env.process(self._pipeline_activation_process(activation_delay))

        # Deterministic disruptions
        self.disruption_engine.schedule_disruptions(
            self.scenario.get('disruptions', [])
        )
        # Stochastic disruptions
        if self.scenario.get('stochastic'):
            self._setup_stochastic()

        # Source shutdowns (sanctions, embargoes)
        for sd in self.scenario.get('source_shutdowns', []):
            self.env.process(
                self._source_shutdown_process(sd['source'], sd['start_day'], sd['duration_days'])
            )

        # Fleet shocks (tanker strikes)
        for fs in self.scenario.get('fleet_shocks', []):
            self.env.process(self._fleet_shock_process(fs['tankers_lost'], fs['day']))

        self.env.run(until=duration_hours)
        return self.metrics.compute_summary(duration_hours)
