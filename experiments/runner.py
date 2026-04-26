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
                    seed = hash((scenario_name, strategy, rep)) % (2 ** 31)
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
                    print(
                        f"  [{done}/{total}] {scenario_name}/{strategy}/rep{rep} "
                        f"shortages={summary['shortage_hours']}h "
                        f"cost=${summary['total_cost']/1e9:.2f}B"
                    )
        return all_results
