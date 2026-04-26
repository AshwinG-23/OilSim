import logging

logger = logging.getLogger(__name__)


class SPR:
    def __init__(self, env, capacity, initial_level, daily_release_rate):
        self.env = env
        self.capacity = float(capacity)
        self.level = float(initial_level)
        self.daily_release_rate = float(daily_release_rate)
        self._hourly_release = daily_release_rate / 24.0
        self.total_released = 0.0
        self.total_refilled = 0.0
        self.is_releasing = False
        self._level_log = []

    def monitor_and_release(self, port, critical_threshold):
        while True:
            yield self.env.timeout(1)
            if port.inventory < critical_threshold and self.level > 0:
                if not self.is_releasing:
                    logger.info(
                        "[%.0fh] SPR release triggered. Port=%.2fM bbl",
                        self.env.now, port.inventory / 1e6,
                    )
                    self.is_releasing = True
                release = min(self._hourly_release, self.level)
                self.level -= release
                self.total_released += release
                port.receive_delivery(release)
                self._level_log.append({'time': self.env.now, 'level': self.level,
                                        'event': 'release'})
            else:
                if self.is_releasing:
                    logger.info("[%.0fh] SPR release stopped.", self.env.now)
                    self.is_releasing = False

    def refill_process(self, port, target_inventory, refill_rate_per_day=500_000):
        """Refill SPR daily when port inventory is healthy and SPR is not full."""
        hourly_refill = refill_rate_per_day / 24.0
        while True:
            yield self.env.timeout(24)
            if (self.level < self.capacity * 0.95
                    and port.inventory > target_inventory * 0.9
                    and not self.is_releasing):
                space = self.capacity - self.level
                refill = min(hourly_refill * 24, space)
                self.level += refill
                self.total_refilled += refill
                self._level_log.append({'time': self.env.now, 'level': self.level,
                                        'event': 'refill'})
                logger.info(
                    "[%.0fh] SPR refill +%.2fM bbl → level %.2fM bbl",
                    self.env.now, refill / 1e6, self.level / 1e6,
                )

    def get_level_log(self):
        return list(self._level_log)
