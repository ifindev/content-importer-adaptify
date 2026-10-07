import pytest

from app.api import rate_limit
from app.api.rate_limit import RateLimitedError, check_rate_limit


@pytest.fixture(autouse=True)
def _clear_buckets():
    rate_limit._buckets.clear()
    yield
    rate_limit._buckets.clear()


def test_allows_requests_up_to_capacity():
    for _ in range(int(rate_limit._CAPACITY)):
        check_rate_limit("1.2.3.4")


def test_rejects_requests_past_capacity():
    for _ in range(int(rate_limit._CAPACITY)):
        check_rate_limit("1.2.3.4")
    with pytest.raises(RateLimitedError):
        check_rate_limit("1.2.3.4")


def test_tracks_ips_independently():
    for _ in range(int(rate_limit._CAPACITY)):
        check_rate_limit("1.2.3.4")

    check_rate_limit("5.6.7.8")
