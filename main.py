#!/usr/bin/env python3
"""
Hormuz Supply Chain Resilience Simulator
Entry point: runs full scenario×strategy experiment matrix and prints results.
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
    print(f"  Duration  : {SIM_DURATION_HOURS / 24:.0f} days")
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
