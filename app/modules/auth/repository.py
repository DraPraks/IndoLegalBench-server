"""Akses database modul auth.

ATURAN: hanya auth/service.py yang boleh memanggil file ini. Modul lain
tidak boleh mengimpor repository milik modul lain.

Isi file ini murni query, tanpa logika bisnis.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DbSession

from app.modules.auth.models import Session, User


def get_user_by_sub(db: DbSession, zitadel_sub: str) -> User | None:
    return db.query(User).filter(User.zitadel_sub == zitadel_sub).first()


def get_user_by_id(db: DbSession, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create_session(
    db: DbSession,
    *,
    user_id: uuid.UUID,
    expires_at: datetime,
    zitadel_sid: str | None = None,
    id_token: str | None = None,
    now: datetime | None = None,
) -> Session:
    stamp = now or datetime.now(timezone.utc)
    session = Session(
        user_id=user_id,
        created_at=stamp,
        last_activity_at=stamp,
        expires_at=expires_at,
        zitadel_sid=zitadel_sid,
        id_token=id_token,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: DbSession, session_id: uuid.UUID) -> Session | None:
    session = db.get(Session, session_id)
    if session is None:
        return None
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    # TODO(SCRUM-91): compare last_activity_at + idle window, not only expires_at
    if expires_at <= now:
        db.delete(session)
        db.commit()
        return None
    return session


def delete_session(db: DbSession, session_id: uuid.UUID) -> None:
    session = db.get(Session, session_id)
    if session is None:
        return
    db.delete(session)
    db.commit()


def touch_session(db: DbSession, session_id: uuid.UUID, *, now: datetime | None = None) -> Session | None:
    session = get_session(db, session_id)
    if session is None:
        return None
    session.last_activity_at = now or datetime.now(timezone.utc)
    # TODO(SCRUM-91): slide expires_at on activity so idle timeout actually resets
    db.commit()
    db.refresh(session)
    return session
