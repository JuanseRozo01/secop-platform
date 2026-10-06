import time
from collections import OrderedDict
from collections.abc import Callable, Hashable
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Caché en memoria con expiración y tamaño máximo (por proceso).

    ttl_seconds <= 0 desactiva la caché. Para varios workers/instancias
    habrá que migrar a Redis (ver ROADMAP).
    """

    def __init__(
        self,
        ttl_seconds: float,
        max_items: int = 512,
        timer: Callable[[], float] = time.monotonic,
    ):
        self._ttl = ttl_seconds
        self._max = max_items
        self._timer = timer
        self._data: OrderedDict[Hashable, tuple[float, T]] = OrderedDict()

    def get(self, key: Hashable) -> T | None:
        if self._ttl <= 0:
            return None
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._timer() >= expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: Hashable, value: T) -> None:
        if self._ttl <= 0:
            return
        self._data[key] = (self._timer() + self._ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self._max:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)
