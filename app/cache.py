import time
from collections import OrderedDict
from typing import Any, Hashable


class TTLCache:
    def __init__(self, maxsize: int = 256, ttl_seconds: int = 60):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._store: "OrderedDict[Hashable, tuple[float, Any]]" = OrderedDict()

    def get(self, key: Hashable) -> Any | None:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if now - ts > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        # refresh LRU order
        self._store.move_to_end(key)
        return value

    def set(self, key: Hashable, value: Any) -> None:
        now = time.time()
        self._store[key] = (now, value)
        self._store.move_to_end(key)
        while len(self._store) > self.maxsize:
            self._store.popitem(last=False)



