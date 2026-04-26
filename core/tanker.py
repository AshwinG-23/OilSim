import simpy


class Tanker:
    def __init__(self, name, capacity_bbl):
        self.name = name
        self.capacity_bbl = capacity_bbl
        self.state = 'idle'
        self.voyages_completed = 0


class Fleet:
    def __init__(self, env, num_tankers, tanker_capacity_bbl):
        self.env = env
        self._store = simpy.Store(env)
        self._tankers = [Tanker(f"T{i:02d}", tanker_capacity_bbl) for i in range(num_tankers)]
        for t in self._tankers:
            self._store.put(t)

    def request(self):
        return self._store.get()

    def release(self, tanker):
        tanker.state = 'idle'
        self._store.put(tanker)

    def remove_tankers(self, count):
        """Permanently remove up to `count` idle tankers (fleet shock / missile strike)."""
        removed = 0
        while removed < count and self._store.items:
            tanker = self._store.items.pop(0)
            tanker.state = 'lost'
            if tanker in self._tankers:
                self._tankers.remove(tanker)
            removed += 1
        return removed

    @property
    def available_count(self):
        return len(self._store.items)

    @property
    def total_count(self):
        return len(self._tankers)
