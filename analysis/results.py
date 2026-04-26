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
            shortage = [r['shortage_hours']          for r in runs]
            cost     = [r['total_cost']               for r in runs]
            cost_bbl = [r['avg_cost_per_bbl']         for r in runs]
            dfr      = [r['demand_fulfillment_rate']  for r in runs]
            aggregated[key] = {
                'scenario':              key[0],
                'strategy':              key[1],
                'n_runs':                len(runs),
                'mean_shortage_hours':   statistics.mean(shortage),
                'std_shortage_hours':    statistics.stdev(shortage) if len(shortage) > 1 else 0,
                'mean_total_cost':       statistics.mean(cost),
                'mean_avg_cost_per_bbl': statistics.mean(cost_bbl),
                'mean_fulfillment_rate': statistics.mean(dfr),
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
