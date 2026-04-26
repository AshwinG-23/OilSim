import sys
import os
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from config.params import SCENARIOS, STRATEGIES, SOURCES
from simulation.engine import SimulationEngine
from analysis.results import ResultsAnalyzer

app = Flask(__name__, static_folder='static')

# ── Meta (served once on page load) ──────────────────────────────────────────

_META = {
    'scenarios': list(SCENARIOS.keys()),
    'strategies': list(STRATEGIES),
    'feature_flags': [
        {
            'key': 'enable_tanker_breakdowns', 'label': 'Tanker Breakdowns',
            'params': [
                {'key': 'tanker_mtbf_hours',        'label': 'MTBF (hours)',     'default': 8760},
                {'key': 'tanker_repair_mean_hours',  'label': 'Repair mean (h)', 'default': 336},
            ],
        },
        {'key': 'enable_demand_elasticity',  'label': 'Demand Elasticity',    'params': []},
        {'key': 'enable_seasonal_weather',   'label': 'Seasonal Weather',     'params': []},
        {
            'key': 'enable_panic_ordering', 'label': 'Panic Ordering',
            'params': [
                {'key': 'panic_multiplier', 'label': 'Multiplier', 'default': 3},
            ],
        },
        {
            'key': 'enable_information_delay', 'label': 'Information Delay',
            'params': [
                {'key': 'information_delay_hours', 'label': 'Delay (hours)', 'default': 24},
            ],
        },
        {'key': 'enable_spr_refill',        'label': 'SPR Auto-Refill',      'params': []},
        {'key': 'enable_freight_dynamics',   'label': 'Freight Dynamics',     'params': []},
        {'key': 'enable_pipeline_bypass',    'label': 'Pipeline Bypass (UAE)', 'params': []},
    ],
    'sources': list(SOURCES.keys()),
    'duration_range': {'min_days': 30, 'max_days': 365},
    'reps_range':     {'min': 1, 'max': 200},
}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/meta')
def meta():
    return jsonify(_META)


@app.route('/api/run', methods=['POST'])
def run_simulation():
    body = request.get_json(force=True)

    # Accept single 'scenario' string (primary) or 'scenarios' array (future use)
    raw = body.get('scenarios') or [body.get('scenario', '')]
    scenario_names = [s for s in raw if s]

    strategies    = body.get('strategies', [])
    duration_days = int(body.get('duration_days', 90))
    replications  = int(body.get('replications', 3))
    flags         = body.get('feature_flags', {})

    # Validation
    if not scenario_names:
        return jsonify({'error': 'Select a scenario'}), 400
    invalid_sc = [s for s in scenario_names if s not in SCENARIOS]
    if invalid_sc:
        return jsonify({'error': f'Unknown scenario: {invalid_sc}'}), 400
    invalid_st = [s for s in strategies if s not in STRATEGIES]
    if invalid_st:
        return jsonify({'error': f'Unknown strategies: {invalid_st}'}), 400
    if not strategies:
        return jsonify({'error': 'Select at least one strategy'}), 400
    if not (30 <= duration_days <= 365):
        return jsonify({'error': 'duration_days must be between 30 and 365'}), 400
    if not (1 <= replications <= 200):
        return jsonify({'error': 'replications must be between 1 and 200'}), 400

    duration_h   = duration_days * 24
    scenario_cfg = (_merge_scenarios(scenario_names) if len(scenario_names) > 1
                    else SCENARIOS[scenario_names[0]])
    scenario_key = '+'.join(scenario_names)   # stable key for seeds
    out_strategies = {}

    for strategy in strategies:
        rep_results = []
        inv_logs    = []
        disruption_events = []

        for rep in range(replications):
            seed = hash((scenario_key, strategy, rep)) % (2 ** 31)
            engine = SimulationEngine(scenario_cfg, strategy, seed=seed, config=flags)
            summary = engine.run(duration_h)
            summary['scenario'] = scenario_key
            summary['strategy'] = strategy
            rep_results.append(summary)
            inv_logs.append(engine.metrics.inventory_log)
            if rep == 0:
                raw_events = engine.disruption_engine.get_event_log()
                disruption_events = [
                    {
                        'time_days':  e['time'] / 24.0,
                        'chokepoint': e['chokepoint'],
                        'event':      e['event'],
                        'severity':   e['severity'],
                    }
                    for e in raw_events
                ]

        # Aggregate KPIs
        agg  = ResultsAnalyzer(rep_results).aggregate()
        kpis = dict(agg[(scenario_key, strategy)])
        kpis['mean_fleet_utilization'] = statistics.mean(
            r['avg_fleet_utilization'] for r in rep_results
        )
        kpis['first_shortage_hour'] = next(
            (r['first_shortage_hour'] for r in rep_results if r['first_shortage_hour']),
            None,
        )

        out_strategies[strategy] = {
            'kpis':                kpis,
            'inventory_timeseries': _aggregate_timeseries(inv_logs, duration_h),
            'source_mix':           _aggregate_source_mix(rep_results),
            'disruption_events':    disruption_events,
        }

    return jsonify({
        'scenario':      scenario_names[0] if len(scenario_names) == 1 else '+'.join(scenario_names),
        'scenarios':     scenario_names,
        'duration_days': duration_days,
        'replications':  replications,
        'strategies':    out_strategies,
    })


# ── Error handler ─────────────────────────────────────────────────────────────

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500


# ── Helpers ───────────────────────────────────────────────────────────────────

def _merge_scenarios(scenario_names):
    """Combine multiple scenario configs into one compound config.

    Disruptions, source shutdowns, and fleet shocks are concatenated.
    When two scenarios disrupt the same chokepoint in overlapping windows,
    the engine applies each event independently — the last one to start
    determines the live severity until it ends, then the earlier one resumes.
    """
    merged = {
        'disruptions':     [],
        'source_shutdowns': [],
        'fleet_shocks':    [],
        'stochastic':      False,
    }
    for name in scenario_names:
        cfg = SCENARIOS[name]
        merged['disruptions'].extend(cfg.get('disruptions', []))
        merged['source_shutdowns'].extend(cfg.get('source_shutdowns', []))
        merged['fleet_shocks'].extend(cfg.get('fleet_shocks', []))
        if cfg.get('stochastic'):
            merged['stochastic'] = True
            merged.setdefault('disruption_mean_interval_days',
                              cfg.get('disruption_mean_interval_days', 60))
            merged.setdefault('disruption_severity_range',
                              cfg.get('disruption_severity_range', (0.1, 0.7)))
            merged.setdefault('disruption_duration_mean_days',
                              cfg.get('disruption_duration_mean_days', 45))
    return merged


def _step_lookup(times, vals, t):
    """Return the last inventory value recorded at time ≤ t."""
    result = vals[0] if vals else 0.0
    for i, time in enumerate(times):
        if time <= t:
            result = vals[i]
        else:
            break
    return result


def _aggregate_timeseries(inv_logs, duration_hours):
    """Resample each rep's inventory log onto a daily grid; return mean ± 1-std band."""
    ticks = list(range(0, int(duration_hours) + 1, 24))
    per_rep = []
    for log in inv_logs:
        times = [e['time']      for e in log]
        vals  = [e['inventory'] for e in log]
        per_rep.append([_step_lookup(times, vals, t) for t in ticks])

    n = len(per_rep)
    means, uppers, lowers = [], [], []
    for i in range(len(ticks)):
        col = [per_rep[r][i] for r in range(n)]
        m   = statistics.mean(col)
        s   = statistics.stdev(col) if n > 1 else 0.0
        means.append(round(m / 1e6, 3))
        uppers.append(round((m + s) / 1e6, 3))
        lowers.append(round(max(0.0, m - s) / 1e6, 3))

    return {
        'labels_days': [t // 24 for t in ticks],
        'mean':  means,
        'upper': uppers,
        'lower': lowers,
    }


def _aggregate_source_mix(rep_results):
    """Average barrels / cost / deliveries per source across reps."""
    n = len(rep_results)
    out = {}
    for src in SOURCES:
        out[src] = {
            'barrels':    round(statistics.mean(
                r['barrels_by_source'].get(src, 0) for r in rep_results)),
            'cost':       round(statistics.mean(
                r['cost_by_source'].get(src, 0) for r in rep_results)),
            'deliveries': round(statistics.mean(
                r['deliveries_by_source'].get(src, 0) for r in rep_results)),
        }
    return out


if __name__ == '__main__':
    app.run(debug=True, port=5000)
