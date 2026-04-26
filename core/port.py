import logging

logger = logging.getLogger(__name__)


class Port:
    def __init__(self, env, name, initial_inventory, max_inventory, hourly_demand,
                 demand_elasticity=False, info_delay_hours=0):
        self.env = env
        self.name = name
        self.inventory = float(initial_inventory)
        self.max_inventory = float(max_inventory)
        self.hourly_demand = float(hourly_demand)
        self._demand_elasticity = demand_elasticity
        self._info_delay_hours = info_delay_hours
        self.shortage_hours = 0
        self.total_delivered_bbl = 0.0
        self.total_demanded_bbl = 0.0
        self._inventory_log = []

    @property
    def effective_hourly_demand(self):
        """Demand reduced under shortage when elasticity is enabled (rationing)."""
        if not self._demand_elasticity:
            return self.hourly_demand
        ratio = self.inventory / self.max_inventory
        if ratio > 0.30:
            return self.hourly_demand              # normal operations
        elif ratio >= 0.10:
            return self.hourly_demand * 0.85       # 15% rationing
        else:
            return self.hourly_demand * 0.60       # 40% emergency rationing

    def get_observed_inventory(self):
        """Inventory as visible to decision-makers — optionally delayed by info_delay_hours."""
        if self._info_delay_hours == 0 or not self._inventory_log:
            return self.inventory
        cutoff = self.env.now - self._info_delay_hours
        past = [e for e in self._inventory_log if e['time'] <= cutoff]
        return past[-1]['inventory'] if past else self.inventory

    def demand_process(self):
        while True:
            yield self.env.timeout(1)
            demand = self.effective_hourly_demand
            consumed = min(self.inventory, demand)
            self.inventory -= consumed
            self.total_demanded_bbl += demand
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
