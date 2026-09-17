"""Akses database modul suites.

ATURAN: hanya suites/service.py yang boleh memanggil file ini.
Modul lain tidak boleh mengimpor repository milik modul lain.

Isi file ini murni query, tanpa logika bisnis dan tanpa HTTP.

TODO(PBI-2): lengkapi seluruh fungsi di bawah pada sub task
"[BE] Table suites CRUD, archive, delete".
"""

import uuid

from sqlalchemy.orm import Session

from app.modules.suites.models import Suite


def get_by_id(db: Session, suite_id: uuid.UUID) -> Suite | None:
    return db.get(Suite, suite_id)


def get_by_name(db: Session, name: str) -> Suite | None:
    return db.query(Suite).filter(Suite.name == name).first()


def list_all(db: Session, *, offset: int = 0, limit: int = 20) -> list[Suite]:
    return db.query(Suite).offset(offset).limit(limit).all()


def count_all(db: Session) -> int:
    return db.query(Suite).count()


def create(db: Session, suite: Suite) -> Suite:
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


def save(db: Session, suite: Suite) -> Suite:
    db.commit()
    db.refresh(suite)
    return suite


def delete(db: Session, suite: Suite) -> None:
    db.delete(suite)
    db.commit()
