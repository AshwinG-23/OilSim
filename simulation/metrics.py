from collections import Counter


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
            'time':         time,
            'source':       source,
            'barrels':      barrels,
            'cost_per_bbl': cost_per_bbl,
            'total_cost':   barrels * cost_per_bbl,
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
        util_entries = [f for f in self.fleet_log if 'utilization' in f]
        avg_util = (sum(f['utilization'] for f in util_entries) / len(util_entries)
                    if util_entries else 0.0)

        # Per-source breakdown
        source_counts  = Counter(c['source']    for c in self.cost_log)
        source_barrels = Counter()
        source_cost    = Counter()
        for c in self.cost_log:
            source_barrels[c['source']] += c['barrels']
            source_cost[c['source']]    += c['total_cost']

        return {
            'shortage_hours':          shortage_hrs,
            'total_cost':              total_cost,
            'total_barrels_imported':  total_barrels,
            'avg_cost_per_bbl':        total_cost / total_barrels if total_barrels > 0 else 0.0,
            'demand_fulfillment_rate': dfr,
            'avg_fleet_utilization':   avg_util,
            'first_shortage_hour':     self.shortage_times[0] if self.shortage_times else None,
            'deliveries_by_source':    dict(source_counts),
            'barrels_by_source':       dict(source_barrels),
            'cost_by_source':          dict(source_cost),
        }
