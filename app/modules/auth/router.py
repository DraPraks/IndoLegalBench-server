"""Endpoint HTTP modul auth.

PBI-1 Login aman dan manajemen akses tim.

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.modules.auth import service
from app.modules.auth.cookies import clear_session_cookie, set_session_cookie
from app.modules.auth.schemas import MeResponse
from app.shared.config import get_settings
from app.shared.database import get_db
from app.shared.exceptions import UnauthenticatedError

router = APIRouter(tags=["auth"])


def _session_id_from_cookie(request: Request) -> UUID | None:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


@router.get("/auth/login", status_code=302, summary="Mulai login OIDC")
def login(sub: str | None = None) -> RedirectResponse:
    result = service.start_login(sub=sub)
    return RedirectResponse(url=result.authorization_url, status_code=302)


@router.get("/auth/callback", status_code=302, summary="Callback OIDC")
def callback(
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    result = service.complete_login(db, code=code, state=state)
    response = RedirectResponse(url=result.redirect_url, status_code=302)
    set_session_cookie(response, settings, result.session_id)
    return response


@router.post("/auth/logout", status_code=302, summary="Hapus sesi dan logout IdP")
def logout(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    url = service.logout(db, session_id=_session_id_from_cookie(request))
    response = RedirectResponse(url=url, status_code=302)
    clear_session_cookie(response, settings)
    return response


@router.get("/me", response_model=MeResponse, summary="Profil pengguna yang sedang login")
def me(request: Request, db: Session = Depends(get_db)) -> MeResponse:
    session_id = _session_id_from_cookie(request)
    if session_id is None:
        raise UnauthenticatedError("Authentication required.")
    return service.get_me(db, session_id=session_id)
