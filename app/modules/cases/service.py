"""Logika bisnis modul cases.

PBI-3, SCRUM-106. Ini satu-satunya pintu masuk yang boleh dipanggil
modul lain. Service tidak boleh menyentuh HTTP. Aturan isian ada di
validation.py; di sini yang mengunci suite aktif, kode unik, dan siapa
yang boleh mengubah kasus.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.cases import repository, validation
from app.modules.cases.models import Case, CaseStatus, SplitTag
from app.modules.cases.schemas import CaseRead, CaseSummary, CaseWrite
from app.shared.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError

CASE_CODE_TAKEN = "CASE_CODE_TAKEN"
SUITE_NOT_ACTIVE = "SUITE_NOT_ACTIVE"
SPLIT_TAG_LOCKED = "SPLIT_TAG_LOCKED"


def create_case(
    db: Session, suite_id: uuid.UUID, payload: CaseWrite, *, actor_id: uuid.UUID
) -> CaseRead:
    """Simpan kasus baru sebagai draft. Suite yang tidak aktif ditolak."""
    _wajib_suite_aktif(db, suite_id)
    _pastikan_kode_bebas(db, payload.case_code)
    case = Case(
        suite_id=suite_id,
        status=CaseStatus.DRAFT,
        version=1,
        created_by=actor_id,
        updated_by=actor_id,
    )
    _salin(case, payload, actor_id=actor_id)
    try:
        tersimpan = repository.create(db, case)
    except IntegrityError:
        db.rollback()
        raise _bentrok_kode(db, payload.case_code) from None
    return _tampilkan(tersimpan)


def get_case(db: Session, case_id: uuid.UUID) -> CaseRead:
    return _tampilkan(_wajib_ada(db, case_id))


def list_cases(
    db: Session,
    suite_id: uuid.UUID,
    *,
    status: CaseStatus | None = None,
    split_tag: SplitTag | None = None,
) -> list[CaseSummary]:
    _wajib_suite_ada(db, suite_id)
    baris = repository.list_for_suite(db, suite_id, status=status, split_tag=split_tag)
    return [_ringkas(item) for item in baris]


def update_case(
    db: Session,
    case_id: uuid.UUID,
    payload: CaseWrite,
    *,
    actor_id: uuid.UUID,
    is_admin: bool,
) -> CaseRead:
    """Ubah kasus. Selain pembuat dan admin ditolak. split_tag sebelum
    approved hanya boleh diubah pembuatnya.
    """
    case = _wajib_ada(db, case_id)
    _pastikan_boleh_ubah(case, payload, actor_id=actor_id, is_admin=is_admin)
    if payload.case_code != case.case_code:
        _pastikan_kode_bebas(db, payload.case_code)
    _salin(case, payload, actor_id=actor_id)
    case.version += 1
    try:
        tersimpan = repository.save(db, case)
    except IntegrityError:
        db.rollback()
        raise _bentrok_kode(db, payload.case_code) from None
    return _tampilkan(tersimpan)


def count_for_suite(db: Session, suite_id: uuid.UUID) -> int:
    """Jumlah kasus di dalam satu suite. Dipakai modul suites."""
    return repository.count_for_suite(db, suite_id)


def has_approved_case(db: Session, suite_id: uuid.UUID) -> bool:
    """True kalau suite berisi kasus berstatus approved."""
    return repository.has_approved(db, suite_id)


def _salin(case: Case, payload: CaseWrite, *, actor_id: uuid.UUID) -> None:
    data = payload.model_dump(mode="json")
    case.case_code = payload.case_code
    case.title = payload.identity.title
    case.question = payload.identity.question
    case.category = payload.identity.category
    case.legal_refs = data["legal_refs"]
    case.answer_criteria = data["answer_criteria"]
    case.traps = data["traps"]
    case.split_tag = payload.split_tag
    case.completeness = validation.hitung_kelengkapan(data)
    case.updated_by = actor_id


def _tampilkan(case: Case) -> CaseRead:
    return CaseRead(
        id=case.id,
        suite_id=case.suite_id,
        case_code=case.case_code,
        identity={
            "title": case.title,
            "question": case.question,
            "category": case.category,
        },
        legal_refs=case.legal_refs or [],
        answer_criteria=case.answer_criteria or {},
        traps=case.traps or [],
        split_tag=case.split_tag,
        status=case.status,
        completeness_pct=_persen(case),
        version=case.version,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _ringkas(case: Case) -> CaseSummary:
    return CaseSummary(
        id=case.id,
        case_code=case.case_code,
        title=case.title,
        split_tag=case.split_tag,
        status=case.status,
        completeness_pct=_persen(case),
        updated_at=case.updated_at,
    )


def _persen(case: Case) -> int:
    mentah = case.completeness or {}
    try:
        return int(mentah.get("pct", 0))
    except (TypeError, ValueError):
        return 0


def _wajib_ada(db: Session, case_id: uuid.UUID) -> Case:
    case = repository.get_by_id(db, case_id)
    if case is None:
        raise NotFoundError("Kasus tidak ditemukan")
    return case


def _wajib_suite_ada(db: Session, suite_id: uuid.UUID):
    from app.modules.suites import service as suites_service

    return suites_service.get_suite(db, suite_id)


def _wajib_suite_aktif(db: Session, suite_id: uuid.UUID) -> None:
    suite = _wajib_suite_ada(db, suite_id)
    if suite.status != "active":
        raise ValidationError(
            "Kasus hanya bisa ditulis di suite yang aktif",
            code=SUITE_NOT_ACTIVE,
        )


def _pastikan_kode_bebas(db: Session, case_code: str) -> None:
    if repository.get_by_code(db, case_code) is not None:
        raise _bentrok_kode(db, case_code)


def _bentrok_kode(db: Session, case_code: str) -> ConflictError:
    pemilik = repository.get_by_code(db, case_code)
    nama = "suite lain"
    if pemilik is not None:
        nama = _nama_suite(db, pemilik.suite_id)
    return ConflictError(
        f"Kode kasus '{case_code}' sudah dipakai di suite '{nama}'",
        code=CASE_CODE_TAKEN,
    )


def _nama_suite(db: Session, suite_id: uuid.UUID) -> str:
    from app.modules.suites import service as suites_service
    from app.shared.exceptions import NotFoundError as TidakAda

    try:
        return suites_service.get_suite(db, suite_id).name
    except TidakAda:
        return "suite lain"


def _pastikan_boleh_ubah(
    case: Case, payload: CaseWrite, *, actor_id: uuid.UUID, is_admin: bool
) -> None:
    pembuat = case.created_by == actor_id
    if not pembuat and not is_admin:
        raise ForbiddenError("Hanya pembuat kasus atau admin yang boleh mengubah kasus ini")
    if payload.split_tag != case.split_tag and case.status != CaseStatus.APPROVED and not pembuat:
        raise ForbiddenError(
            "Sebelum kasus disetujui, hanya pembuat yang boleh mengubah split_tag",
            code=SPLIT_TAG_LOCKED,
        )
