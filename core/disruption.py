import random
import logging

logger = logging.getLogger(__name__)


class DisruptionEngine:
    def __init__(self, env, chokepoints):
        self.env = env
        self.chokepoints = chokepoints   # dict[name -> Chokepoint]
        self._event_log = []

    def schedule_disruptions(self, disruption_configs):
        for cfg in disruption_configs:
            self.env.process(self._disruption_process(cfg))

    def _disruption_process(self, cfg):
        name        = cfg['chokepoint']
        start_hours = cfg['start_day'] * 24
        duration_h  = cfg['duration_days'] * 24
        severity    = cfg['severity']

        yield self.env.timeout(start_hours)
        self.chokepoints[name].set_disruption(severity)
        self._event_log.append({
            'time': self.env.now, 'chokepoint': name,
            'event': 'start', 'severity': severity,
        })
        logger.info("[%.0fh] DISRUPTION START: %s severity=%.2f", self.env.now, name, severity)

        yield self.env.timeout(duration_h)
        self.chokepoints[name].set_disruption(1.0)
        self._event_log.append({
            'time': self.env.now, 'chokepoint': name,
            'event': 'end', 'severity': 1.0,
        })
        logger.info("[%.0fh] DISRUPTION END: %s restored", self.env.now, name)

    def get_event_log(self):
        return list(self._event_log)


class StochasticDisruptionEngine(DisruptionEngine):
    """
    Disruptions arrive as a Poisson process with random severity and duration.
    Models unpredictable geopolitical events rather than fixed scenarios.
    """

    def schedule_stochastic(self, chokepoint_names, mean_interval_days,
                             severity_range, duration_mean_days):
        for name in chokepoint_names:
            self.env.process(
                self._stochastic_process(name, mean_interval_days,
                                         severity_range, duration_mean_days)
            )

    def _stochastic_process(self, cp_name, mean_interval_days,
                             severity_range, duration_mean_days):
        mean_interval_h  = mean_interval_days  * 24
        duration_mean_h  = duration_mean_days  * 24

        while True:
            # Exponential inter-arrival time → Poisson disruption arrivals
            wait_h = random.expovariate(1.0 / mean_interval_h)
            yield self.env.timeout(wait_h)

            severity = random.uniform(*severity_range)
            duration = random.expovariate(1.0 / duration_mean_h)

            self.chokepoints[cp_name].set_disruption(severity)
            self._event_log.append({
                'time': self.env.now, 'chokepoint': cp_name,
                'event': 'stochastic_start', 'severity': severity,
            })
            logger.info(
                "[%.0fh] STOCHASTIC DISRUPTION: %s severity=%.2f duration=%.0fh",
                self.env.now, cp_name, severity, duration,
            )

            yield self.env.timeout(duration)

            self.chokepoints[cp_name].set_disruption(1.0)
            self._event_log.append({
                'time': self.env.now, 'chokepoint': cp_name,
                'event': 'stochastic_end', 'severity': 1.0,
            })
