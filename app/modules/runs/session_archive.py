"""Arsipkan sesi pengukuran dari daftar. PBI-11 AC10, SCRUM-210.

Arsip hanya mengisi archived_at dan archived_by. Status dan datanya tetap,
karena sesi tidak pernah dihapus. Catatan audit ditulis listener audit dari
perubahan archived_at (MeasurementSessionTracker).
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.runs import repository
from app.modules.runs.schemas import SessionArchiveResponse
from app.modules.runs.session_rules import ensure_archivable
from app.shared.exceptions import NotFoundError


def archive_session(
    db: Session, session_id: uuid.UUID, *, archived_by: uuid.UUID, now: datetime
) -> SessionArchiveResponse:
    session = repository.get_session_for_update(db, session_id)
    if session is None:
        raise NotFoundError("Pengukuran tidak ditemukan.", code="MEASUREMENT_NOT_FOUND")
    ensure_archivable(session.status.value, archived_at=session.archived_at)
    session.archived_at = now
    session.archived_by = archived_by
    db.commit()
    return SessionArchiveResponse(
        id=session.id, archived_at=session.archived_at, archived_by=session.archived_by
    )
