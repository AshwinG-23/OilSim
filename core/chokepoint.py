import math
import simpy
import random
import logging

logger = logging.getLogger(__name__)


class Chokepoint:
    def __init__(self, env, name, capacity, base_transit_hours, seasonal_weather=False):
        self.env = env
        self.name = name
        self.capacity = capacity
        self.base_transit_hours = base_transit_hours
        self._resource = simpy.Resource(env, capacity=capacity)
        self.status = 1.0               # 1.0=normal, 0.01=nearly blocked
        self.seasonal_weather = seasonal_weather
        self._transit_log = []

    @property
    def queue_length(self):
        return len(self._resource.queue)

    @property
    def in_use(self):
        return self._resource.count

    def set_disruption(self, severity):
        self.status = max(0.01, min(1.0, severity))
        logger.info(
            "[%.0fh] %s disruption: status=%.2f",
            self.env.now, self.name, self.status,
        )

    def _seasonal_multiplier(self):
        """Indian Ocean cyclone + monsoon season (May–Nov) slows maritime routes."""
        if not self.seasonal_weather:
            return 1.0
        day_of_year = (self.env.now / 24.0) % 365.0
        # Season: days 120–330 (early May to late Nov)
        if 120.0 <= day_of_year <= 330.0:
            phase = math.pi * (day_of_year - 120.0) / 210.0
            return 1.0 + math.sin(phase) * 0.30   # up to 30% slower at peak (Sept)
        return 1.0

    def get_transit_time(self):
        base = self.base_transit_hours / self.status
        congestion = self.queue_length * 0.5   # 0.5 h penalty per queued ship
        noise = abs(random.gauss(0, base * 0.05))
        return (base + congestion + noise) * self._seasonal_multiplier()

    def transit(self, tanker_name):
        queue_on_arrival = self.queue_length
        with self._resource.request() as req:
            yield req
            t = self.get_transit_time()
            self._transit_log.append({
                'time': self.env.now,
                'tanker': tanker_name,
                'transit_hours': t,
                'queue_on_arrival': queue_on_arrival,
                'status': self.status,
                'seasonal_multiplier': self._seasonal_multiplier(),
            })
            yield self.env.timeout(t)

    def get_transit_log(self):
        return list(self._transit_log)
