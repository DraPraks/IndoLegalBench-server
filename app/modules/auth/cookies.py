"""Platform session cookie (not Zitadel's cookie).

- Value = `sessions.id` (UUID); HttpOnly + SameSite=Lax
- Call from router / get_current_user only; service must not touch HTTP
- max-age follows the absolute cap, not idle. The server owns the idle check:
  if the cookie died with the idle window, an idle user would come back with no
  cookie and get UNAUTHENTICATED instead of SESSION_EXPIRED
"""

from uuid import UUID

from fastapi import Request, Response

from app.shared.config import Settings


def session_id_from_cookie(request: Request, settings: Settings) -> UUID | None:
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def set_session_cookie(response: Response, settings: Settings, session_id: UUID) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=str(session_id),
        httponly=True,
        samesite="lax",
        path="/",
        secure=settings.cookie_secure,  # TODO: false on local HTTP; must be true on HTTPS
        max_age=settings.absolute_session_lifetime_minutes * 60,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
