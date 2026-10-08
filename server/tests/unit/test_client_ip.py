from starlette.requests import Request

from app.api.routes.public_review import _client_ip

SECRET = "s3cret"


def _request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "client": ("10.0.0.5", 1234),
        }
    )


def test_uses_the_web_apps_client_ip_with_the_secret():
    request = _request({"X-Client-IP": "203.0.113.7", "X-Internal-Secret": SECRET})
    assert _client_ip(request, SECRET) == "203.0.113.7"


def test_ignores_the_client_ip_with_a_wrong_or_missing_secret():
    assert _client_ip(_request({"X-Client-IP": "1.1.1.1", "X-Internal-Secret": "x"}), SECRET) == (
        "10.0.0.5"
    )
    assert _client_ip(_request({"X-Client-IP": "1.1.1.1"}), SECRET) == "10.0.0.5"


def test_ignores_a_spoofed_forwarded_for():
    assert _client_ip(_request({"X-Forwarded-For": "1.2.3.4"}), SECRET) == "10.0.0.5"


def test_without_a_configured_secret_only_the_socket_counts():
    request = _request({"X-Client-IP": "1.1.1.1", "X-Internal-Secret": ""})
    assert _client_ip(request, "") == "10.0.0.5"
