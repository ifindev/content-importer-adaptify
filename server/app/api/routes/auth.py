from fastapi import APIRouter, Depends, Response, status

from app.api.auth import SESSION_COOKIE_NAME, SESSION_EXPIRES_IN, create_session
from app.api.deps import get_agency_emails
from app.api.schemas.auth import SessionRequest
from app.api.tags import AUTH

router = APIRouter(tags=[AUTH])


@router.post("/auth/session", status_code=status.HTTP_204_NO_CONTENT)
def create_session_route(
    body: SessionRequest,
    response: Response,
    allowed_emails: frozenset[str] = Depends(get_agency_emails),
) -> None:
    cookie = create_session(body.id_token, allowed_emails)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        cookie,
        max_age=int(SESSION_EXPIRES_IN.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
    )
