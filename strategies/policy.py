import logging

logger = logging.getLogger(__name__)

# Per-strategy disruption tolerance threshold.
# A chokepoint with status < threshold is treated as "disrupted" during source selection.
_DISRUPTION_THRESHOLDS = {
    'cost_focused': 0.3,   # only reacts to near-total blockades
    'diversified':  0.7,   # reacts to moderate disruption
    'resilient':    0.9,   # avoids even mild disruptions
    'adaptive':     0.3,   # starts cost-focused; updated dynamically at runtime
}


class OrderingPolicy:
    def __init__(self, strategy, sources_config, reorder_point, target_inventory):
        self.strategy = strategy
        self.sources = sources_config
        self.reorder_point = reorder_point
        self.target_inventory = target_inventory
        self.disruption_threshold = _DISRUPTION_THRESHOLDS.get(strategy, 0.7)
        self._orders_log = []

    # ── Adaptive: dynamically shift threshold based on observed conditions ───

    def update_adaptive_threshold(self, chokepoints):
        """
        Adaptive strategy adjusts disruption_threshold (and thus source priority)
        in real-time based on chokepoint health. This is the key behavioral
        difference: adaptive switches *strategy mode* dynamically.
        """
        if self.strategy != 'adaptive':
            return
        statuses = [cp.status for cp in chokepoints.values()]
        avg_status = sum(statuses) / len(statuses) if statuses else 1.0
        if avg_status >= 0.8:
            self.disruption_threshold = 0.3   # calm → cost-focused mode
        elif avg_status >= 0.5:
            self.disruption_threshold = 0.7   # moderate stress → diversified mode
        else:
            self.disruption_threshold = 0.9   # crisis → resilient mode

    # ── Should we place an order? ────────────────────────────────────────────

    def should_order(self, port, fleet, observed_inventory=None):
        inv = observed_inventory if observed_inventory is not None else port.inventory
        return inv < self.reorder_point and fleet.available_count > 0

    # ── Which source to use? ─────────────────────────────────────────────────

    def get_source_priority(self, disrupted_chokepoints, disabled_sources=None):
        disrupted = set(disrupted_chokepoints)
        disabled  = disabled_sources or set()

        def is_safe(source_name):
            return not any(c in disrupted for c in self.sources[source_name]['chokepoints'])

        # Filter out disabled sources (e.g. pipeline not yet active, Russia sanctioned)
        available = {s: v for s, v in self.sources.items() if s not in disabled}

        if self.strategy in ('resilient', 'adaptive') and self.disruption_threshold >= 0.8:
            # Safety-first: prefer routes with fewest chokepoints
            def sort_key(s):
                return (len(available[s]['chokepoints']),
                        available[s]['base_cost_per_bbl'])
            all_sorted = sorted(available, key=sort_key)
            safe   = [s for s in all_sorted if is_safe(s)]
            unsafe = [s for s in all_sorted if not is_safe(s)]
            return safe + unsafe

        # Cost-first (cost_focused, diversified, adaptive in calm mode):
        # cheapest safe routes, then cheapest unsafe routes
        safe   = sorted((s for s in available if is_safe(s)),
                        key=lambda s: available[s]['base_cost_per_bbl'])
        unsafe = sorted((s for s in available if not is_safe(s)),
                        key=lambda s: available[s]['base_cost_per_bbl'])
        return safe + unsafe

    # ── Build the order dict ──────────────────────────────────────────────────

    def place_order(self, port, fleet, chokepoints, disrupted_chokepoints,
                    disabled_sources=None, fleet_utilization=0.0,
                    enable_freight_dynamics=False):
        priority = self.get_source_priority(disrupted_chokepoints, disabled_sources)
        if not priority:
            return None

        if self.strategy == 'diversified':
            # Round-robin to avoid always using the same source
            source_name = priority[len(self._orders_log) % len(priority)]
        else:
            source_name = priority[0]

        src = self.sources[source_name]

        # Disruption risk premium on cost
        disruption_premium = 1.0
        for cp_name in src['chokepoints']:
            if cp_name in chokepoints:
                cp = chokepoints[cp_name]
                disruption_premium += max(0.0, (1.0 - cp.status)) * 1.5

        # Freight rate dynamics: scarcity premium when fleet is heavily utilised
        freight_multiplier = 1.0
        if enable_freight_dynamics and fleet_utilization > 0.7:
            excess = (fleet_utilization - 0.7) / 0.3   # 0→1 as util goes 70%→100%
            freight_multiplier = 1.0 + excess ** 2 * 2.0

        cost_per_bbl = src['base_cost_per_bbl'] * disruption_premium * freight_multiplier

        order = {
            'source':             source_name,
            'cargo_bbl':          src['cargo_bbl'],
            'cost_per_bbl':       cost_per_bbl,
            'loading_time_hours': src['loading_time_hours'],
            'return_time_hours':  src['return_time_hours'],
            'route_chokepoints':  [chokepoints[c] for c in src['chokepoints']
                                   if c in chokepoints],
        }
        self._orders_log.append({'source': source_name, 'cost_per_bbl': cost_per_bbl})
        logger.info(
            "Order placed: %s via %s ($%.2f/bbl)",
            source_name, src['chokepoints'], cost_per_bbl,
        )
        return order

    def get_orders_log(self):
        return list(self._orders_log)
