from app.core.cache import TTLCache


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_ttl_expiry_and_eviction():
    clock = Clock()
    cache = TTLCache[int](ttl_seconds=10, max_items=2, timer=clock)
    cache.set("a", 1)
    assert cache.get("a") == 1
    clock.t = 10
    assert cache.get("a") is None

    cache.set("a", 1); cache.set("b", 2); cache.set("c", 3)  # noqa: E702
    assert cache.get("a") is None and cache.get("b") == 2 and cache.get("c") == 3
    assert len(cache) == 2


def test_zero_ttl_disables_cache():
    cache = TTLCache[int](ttl_seconds=0)
    cache.set("a", 1)
    assert cache.get("a") is None
