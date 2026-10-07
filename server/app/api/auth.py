import logging
from datetime import timedelta

import firebase_admin
from fastapi import Request
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "session"
SESSION_EXPIRES_IN = timedelta(days=5)

if not firebase_admin._apps:
    firebase_admin.initialize_app()


class InvalidSessionError(Exception):
    pass


def create_session(id_token: str) -> str:
    try:
        decoded = auth.verify_id_token(id_token)
        cookie = auth.create_session_cookie(id_token, expires_in=SESSION_EXPIRES_IN)
    except (FirebaseError, ValueError) as exc:
        logger.info("Firebase session creation failed: %s", exc)
        raise InvalidSessionError from exc
    logger.info("Firebase session created for uid=%s", decoded["uid"])
    return cookie


def require_session(request: Request) -> str:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        raise InvalidSessionError
    try:
        decoded = auth.verify_session_cookie(cookie, check_revoked=True)
    except (FirebaseError, ValueError) as exc:
        logger.info("Firebase session verification failed: %s", exc)
        raise InvalidSessionError from exc
    uid = decoded["uid"]
    request.state.uid = uid
    return uid
