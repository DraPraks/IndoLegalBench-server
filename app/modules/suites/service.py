"""Logika bisnis modul suites.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain.
Service tidak boleh menyentuh HTTP (tidak ada Request, Response, atau
HTTPException di sini). Kalau ada aturan bisnis yang dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-2): lengkapi seluruh fungsi sesuai acceptance criteria PBI-2.
"""

import uuid

from sqlalchemy.orm import Session

from app.modules.suites import repository
from app.modules.suites.models import Suite, SuiteStatus
from app.modules.suites.schemas import SuiteCreate, SuiteUpdate
from app.shared.exceptions import ConflictError, NotFoundError


def create_suite(db: Session, payload: SuiteCreate) -> Suite:
    """AC: nama suite yang sudah dipakai tidak bisa dipakai ulang."""
    if repository.get_by_name(db, payload.name):
        raise ConflictError(f"Nama suite '{payload.name}' sudah dipakai")

    suite = Suite(name=payload.name, description=payload.description)
    return repository.create(db, suite)


def get_suite(db: Session, suite_id: uuid.UUID) -> Suite:
    suite = repository.get_by_id(db, suite_id)
    if suite is None:
        raise NotFoundError("Suite tidak ditemukan")
    return suite


def update_suite(db: Session, suite_id: uuid.UUID, payload: SuiteUpdate) -> Suite:
    suite = get_suite(db, suite_id)

    if payload.name and payload.name != suite.name:
        if repository.get_by_name(db, payload.name):
            raise ConflictError(f"Nama suite '{payload.name}' sudah dipakai")
        suite.name = payload.name

    if payload.description is not None:
        suite.description = payload.description

    return repository.save(db, suite)


def delete_suite(db: Session, suite_id: uuid.UUID) -> None:
    """AC: suite yang berisi kasus approved tidak boleh dihapus, hanya diarsipkan.

    TODO(PBI-2): panggil cases.service untuk mengecek apakah ada kasus
    berstatus approved di dalam suite ini. JANGAN query tabel cases
    langsung dari sini, itu melanggar batas modul.
    """
    suite = get_suite(db, suite_id)
    repository.delete(db, suite)


def archive_suite(db: Session, suite_id: uuid.UUID) -> Suite:
    """AC: suite yang diarsipkan tidak muncul di daftar aktif dan tidak bisa
    dipilih untuk pengukuran baru, tapi seluruh isinya tetap tersimpan."""
    suite = get_suite(db, suite_id)
    suite.status = SuiteStatus.ARCHIVED
    return repository.save(db, suite)


def is_exportable(db: Session, suite_id: uuid.UUID) -> bool:
    """AC: suite kosong tidak bisa ikut proses ekspor atau pengukuran.

    Dipakai modul lain (runs, reports) lewat service ini, bukan dengan
    mengecek tabel suites sendiri.

    TODO(PBI-2): kembalikan False kalau suite kosong atau berstatus archived.
    """
    suite = get_suite(db, suite_id)
    return suite.status == SuiteStatus.ACTIVE
