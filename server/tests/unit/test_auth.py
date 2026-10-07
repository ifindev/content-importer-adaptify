from unittest.mock import patch

import pytest
from fastapi import Request
from firebase_admin.auth import RevokedSessionCookieError

from app.api.auth import InvalidSessionError, create_session, require_session


def _request(cookie: str | None) -> Request:
    cookies = f"session={cookie}".encode() if cookie else b""
    scope = {
        "type": "http",
        "headers": [(b"cookie", cookies)] if cookie else [],
    }
    return Request(scope)


def test_create_session_returns_cookie():
    with (
        patch("app.api.auth.auth.verify_id_token", return_value={"uid": "u1"}),
        patch("app.api.auth.auth.create_session_cookie", return_value="cookie-value"),
    ):
        assert create_session("valid-id-token") == "cookie-value"


def test_create_session_rejects_invalid_token():
    with patch("app.api.auth.auth.verify_id_token", side_effect=ValueError("bad token")):
        with pytest.raises(InvalidSessionError):
            create_session("bad-id-token")


def test_require_session_sets_uid_for_valid_cookie():
    request = _request("valid-cookie")
    with patch("app.api.auth.auth.verify_session_cookie", return_value={"uid": "u1"}):
        assert require_session(request) == "u1"
    assert request.state.uid == "u1"


def test_require_session_rejects_missing_cookie():
    with pytest.raises(InvalidSessionError):
        require_session(_request(None))


def test_require_session_rejects_revoked_cookie():
    request = _request("revoked-cookie")
    with patch(
        "app.api.auth.auth.verify_session_cookie",
        side_effect=RevokedSessionCookieError("revoked"),
    ):
        with pytest.raises(InvalidSessionError):
            require_session(request)
