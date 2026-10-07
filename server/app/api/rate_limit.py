import time

_CAPACITY = 20.0
_REFILL_PER_SEC = 0.5

# ponytail: single-process dict, fine for one Cloud Run instance with no autoscaling;
# move to a shared store (e.g. Redis) if the API ever scales to multiple instances.
_buckets: dict[str, tuple[float, float]] = {}


class RateLimitedError(Exception):
    pass


def check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    tokens, last = _buckets.get(ip, (_CAPACITY, now))
    tokens = min(_CAPACITY, tokens + (now - last) * _REFILL_PER_SEC)
    if tokens < 1:
        _buckets[ip] = (tokens, now)
        raise RateLimitedError
    _buckets[ip] = (tokens - 1, now)
