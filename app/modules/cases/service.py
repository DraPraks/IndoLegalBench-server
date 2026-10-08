"""Logika bisnis modul cases.

PBI-3, SCRUM-106. SCRUM-136 memindahkan isi kasus ke case_versions.
Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Aturan isian ada di validation.py; di sini
yang mengunci suite aktif, kode unik, versi yang disetujui, dan siapa
yang boleh mengubah kasus.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.cases import completeness, repository, validation
from app.modules.cases.models import Case, CaseStatus, CaseVersion, SplitTag
from app.modules.cases.schemas import CaseCompleteness, CaseRead, CaseSummary, CaseWrite
from app.shared.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError

CASE_CODE_TAKEN = "CASE_CODE_TAKEN"
SUITE_NOT_ACTIVE = "SUITE_NOT_ACTIVE"
SPLIT_TAG_LOCKED = "SPLIT_TAG_LOCKED"
VERSION_LOCKED = "VERSION_LOCKED"


def create_case(
    db: Session, suite_id: uuid.UUID, payload: CaseWrite, *, actor_id: uuid.UUID
) -> CaseRead:
    """Store a new case as draft version 1. An inactive suite is rejected."""
    _require_active_suite(db, suite_id)
    _require_free_code(db, payload.case_code)
    case_id = uuid.uuid4()
    version_id = uuid.uuid4()
    case = Case(
        id=case_id,
        suite_id=suite_id,
        case_code=payload.case_code,
        current_version_id=version_id,
        latest_approved_version_id=None,
        created_by=actor_id,
        updated_by=actor_id,
    )
    version = CaseVersion(
        id=version_id,
        case_id=case_id,
        version_no=1,
        status=CaseStatus.DRAFT,
        split_tag=payload.split_tag,
        content={},
        created_by=actor_id,
        based_on_version_id=None,
    )
    _write_version(case, version, payload, actor_id=actor_id)
    _catat_versi_baru(version)
    try:
        tersimpan = repository.create(db, case, version)
    except IntegrityError:
        db.rollback()
        raise _code_taken(db, payload.case_code) from None
    return _to_read(tersimpan, version)


def get_case(db: Session, case_id: uuid.UUID) -> CaseRead:
    """Return the version that is in effect, or raise when the id does not exist."""
    return _to_read(_require_case(db, case_id))


def get_completeness(db: Session, case_id: uuid.UUID) -> CaseCompleteness:
    """Kelengkapan versi yang sedang dikerjakan, dihitung ulang dari isinya.

    Dihitung dari content versi saat ini, bukan dari salinan completeness
    yang tersimpan, supaya baris lama tetap menjawab dengan formula terbaru.
    """
    case = _require_case(db, case_id)
    return CaseCompleteness(**completeness.from_row(case))


def list_cases(
    db: Session,
    suite_id: uuid.UUID,
    *,
    status: CaseStatus | None = None,
    split_tag: SplitTag | None = None,
) -> list[CaseSummary]:
    """Return the short list for a suite that exists. Filters use the in-effect version."""
    _require_suite(db, suite_id)
    baris = repository.list_for_suite(db, suite_id, status=status, split_tag=split_tag)
    return [_to_summary(case, version) for case, version in baris]


def update_case(
    db: Session,
    case_id: uuid.UUID,
    payload: CaseWrite,
    *,
    actor_id: uuid.UUID,
    is_admin: bool,
) -> CaseRead:
    """Update the current version in place.

    An archived suite is rejected with SUITE_NOT_ACTIVE, same as create.
    """
    case = _require_case(db, case_id)
    _require_active_suite(db, case.suite_id)
    version = case.current_version
    _require_not_approved(version)
    _require_can_update(case, version, payload, actor_id=actor_id, is_admin=is_admin)
    if payload.case_code != case.case_code:
        _require_free_code(db, payload.case_code)
    _write_version(case, version, payload, actor_id=actor_id)
    try:
        tersimpan = repository.save(db, case)
    except IntegrityError:
        db.rollback()
        raise _code_taken(db, payload.case_code) from None
    return _to_read(tersimpan, version)


def count_for_suite(db: Session, suite_id: uuid.UUID) -> int:
    """Count cases in one suite. Called by the suites module."""
    return repository.count_for_suite(db, suite_id)


def has_approved_case(db: Session, suite_id: uuid.UUID) -> bool:
    """True when the suite contains a case that has an approved version."""
    return repository.has_approved(db, suite_id)


def _catat_versi_baru(version: CaseVersion) -> None:
    """TODO(SCRUM-140): record the new-version event in audit_logs.

    The audit table and listener belong to that ticket. This call site is
    the only place a new case_versions row is inserted.
    """
    del version


def _write_version(
    case: Case, version: CaseVersion, payload: CaseWrite, *, actor_id: uuid.UUID
) -> None:
    """Copy the write body onto the version and store the completeness indicator."""
    data = payload.model_dump(mode="json")
    case.case_code = payload.case_code
    case.updated_by = actor_id
    version.split_tag = payload.split_tag
    version.content = {
        "title": payload.identity.title,
        "question": payload.identity.question,
        "category": payload.identity.category,
        "legal_refs": data["legal_refs"],
        "answer_criteria": data["answer_criteria"],
        "traps": data["traps"],
        "completeness": validation.completeness(data),
    }


def _to_read(case: Case, version: CaseVersion | None = None) -> CaseRead:
    """Build the full read model. Status stays server-owned.

    Without an explicit version, the response is the version in effect.
    """
    versi = version if version is not None else _in_effect(case)
    isi = versi.content or {}
    return CaseRead(
        id=case.id,
        suite_id=case.suite_id,
        case_code=case.case_code,
        identity={
            "title": isi.get("title") or "",
            "question": isi.get("question") or "",
            "category": isi.get("category"),
        },
        legal_refs=isi.get("legal_refs") or [],
        answer_criteria=isi.get("answer_criteria") or {},
        traps=isi.get("traps") or [],
        split_tag=versi.split_tag,
        status=versi.status,
        completeness_pct=_completeness_pct(isi.get("completeness")),
        version=versi.version_no,
        created_at=versi.created_at,
        updated_at=versi.updated_at,
    )


def _to_summary(case: Case, version: CaseVersion) -> CaseSummary:
    """Build the short list item from the version that is in effect."""
    isi = version.content or {}
    return CaseSummary(
        id=case.id,
        case_code=case.case_code,
        title=isi.get("title") or "",
        split_tag=version.split_tag,
        status=version.status,
        completeness_pct=_completeness_pct(isi.get("completeness")),
        updated_at=version.updated_at,
    )


def _in_effect(case: Case) -> CaseVersion:
    """The approved wording when one exists, otherwise the only open version."""
    if case.latest_approved_version is not None:
        return case.latest_approved_version
    return case.current_version


def _completeness_pct(mentah: dict | None) -> int:
    """Read completeness.pct, or 0 when the stored value is missing or invalid."""
    if not isinstance(mentah, dict):
        return 0
    try:
        return int(mentah.get("pct", 0))
    except (TypeError, ValueError):
        return 0


def _require_case(db: Session, case_id: uuid.UUID) -> Case:
    """Load a case or raise NotFoundError."""
    case = repository.get_by_id(db, case_id)
    if case is None:
        raise NotFoundError("Kasus tidak ditemukan")
    return case


def _require_not_approved(version: CaseVersion) -> None:
    """An approved version stays as it was stored."""
    if version.status != CaseStatus.APPROVED:
        return
    raise ConflictError(
        "Versi yang sudah disetujui tidak bisa diubah. Buat versi baru.",
        code=VERSION_LOCKED,
    )


def _require_suite(db: Session, suite_id: uuid.UUID):
    """Load the suite through suites.service.

    The import stays inside the function so suites.service can import this
    module at import time without a cycle.
    """
    from app.modules.suites import service as suites_service

    return suites_service.get_suite(db, suite_id)


def _require_active_suite(db: Session, suite_id: uuid.UUID) -> None:
    """Reject writes when the suite is missing or not active."""
    suite = _require_suite(db, suite_id)
    if suite.status != "active":
        raise ValidationError(
            "Kasus hanya bisa ditulis di suite yang aktif",
            code=SUITE_NOT_ACTIVE,
        )


def _require_free_code(db: Session, case_code: str) -> None:
    """Reject a case_code that another suite already owns."""
    if repository.get_by_code(db, case_code) is not None:
        raise _code_taken(db, case_code)


def _code_taken(db: Session, case_code: str) -> ConflictError:
    """Build CASE_CODE_TAKEN. The message names the suite that owns the code."""
    pemilik = repository.get_by_code(db, case_code)
    nama = "suite lain"
    if pemilik is not None:
        nama = _suite_name(db, pemilik.suite_id)
    return ConflictError(
        f"Kode kasus '{case_code}' sudah dipakai di suite '{nama}'",
        code=CASE_CODE_TAKEN,
    )


def _suite_name(db: Session, suite_id: uuid.UUID) -> str:
    """Return the suite name, or a fallback when that suite is already gone."""
    from app.modules.suites import service as suites_service

    try:
        return suites_service.get_suite(db, suite_id).name
    except NotFoundError:
        return "suite lain"


def _require_creator_or_admin(case: Case, *, actor_id: uuid.UUID, is_admin: bool) -> None:
    """Allow the case creator or an admin."""
    if case.created_by == actor_id or is_admin:
        return
    raise ForbiddenError("Hanya pembuat kasus atau admin yang boleh mengubah kasus ini")


def _require_can_update(
    case: Case,
    version: CaseVersion,
    payload: CaseWrite,
    *,
    actor_id: uuid.UUID,
    is_admin: bool,
) -> None:
    """Allow the creator or an admin. Lock split_tag until the case has been approved."""
    _require_creator_or_admin(case, actor_id=actor_id, is_admin=is_admin)
    belum_disetujui = case.latest_approved_version_id is None
    if payload.split_tag != version.split_tag and belum_disetujui and case.created_by != actor_id:
        raise ForbiddenError(
            "Sebelum kasus disetujui, hanya pembuat yang boleh mengubah split_tag",
            code=SPLIT_TAG_LOCKED,
        )
