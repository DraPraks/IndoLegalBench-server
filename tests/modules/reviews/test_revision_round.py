"""Pengajuan ulang setelah revisi. PBI-6 AC9, SCRUM-146.

Satu approval dibawa ke round berikutnya. Hanya reviewer yang meminta
revisi ditugaskan lagi. Komentar revisi di round lama tidak diubah.
"""

import uuid
from unittest.mock import patch

import pytest

from app.modules.audit.models import AuditLog
from app.modules.cases import service as cases_service
from app.modules.cases.models import Case, CaseStatus
from app.modules.reviews import service as reviews_service
from app.modules.reviews.models import (
    AssignmentSource,
    AssignmentStatus,
    ReviewAssignment,
    ReviewRound,
    ReviewVerdict,
    RoundDecision,
    RoundStatus,
    VerdictDecision,
)
from app.modules.reviews.ports import NoopNotifier
from app.shared import request_context
from app.shared.exceptions import ConflictError
from app.shared.security import Role
from tests.modules.cases.test_submit_assigns_reviewers import _kasus, _user

KOMENTAR = "Perbaiki rujukan pasal 151."


def _putaran(
    db, kasus, keputusan: list[tuple[uuid.UUID, VerdictDecision, str | None]]
) -> ReviewRound:
    ronde = ReviewRound(
        case_id=kasus.id,
        case_version_id=kasus.current_version_id,
        round_no=1,
        status=RoundStatus.DECIDED,
        decision=RoundDecision.REVISE,
    )
    db.add(ronde)
    db.flush()
    for reviewer_id, decision, komentar in keputusan:
        tugas = ReviewAssignment(
            review_round_id=ronde.id,
            reviewer_id=reviewer_id,
            source=AssignmentSource.SYSTEM,
            status=AssignmentStatus.ACTIVE,
        )
        db.add(tugas)
        db.flush()
        db.add(
            ReviewVerdict(
                assignment_id=tugas.id,
                decision=decision,
                comment=komentar,
            )
        )
    db.commit()
    return ronde


def _ajukan(db, kasus, penulis: uuid.UUID):
    request_context.bind(db, user_id=penulis, role=Role.AUTHOR)
    with (
        patch.object(
            cases_service.reviews_service,
            "assign_on_submit",
            wraps=reviews_service.assign_on_submit,
        ) as assign,
        patch.object(NoopNotifier, "notify") as notify,
    ):
        hasil = cases_service.submit_for_review(db, kasus.id, actor_id=penulis)
    return hasil, assign, notify


def _tugas(db, ronde: ReviewRound) -> list[ReviewAssignment]:
    return db.query(ReviewAssignment).filter_by(review_round_id=ronde.id).all()


def _verdict(db, tugas: ReviewAssignment) -> ReviewVerdict | None:
    return db.query(ReviewVerdict).filter_by(assignment_id=tugas.id).one_or_none()


def test_pengajuan_ulang_membawa_approve_dan_hanya_menugaskan_perevisi(db_session):
    """AC9: approval tetap, hanya yang meminta revisi meninjau lagi."""
    # Arrange
    penulis = _user(db_session, 1, Role.AUTHOR)
    penyetuju = _user(db_session, 2, Role.REVIEWER)
    perevisi = _user(db_session, 3, Role.REVIEWER)
    ketiga = _user(db_session, 4, Role.REVIEWER)
    kasus = _kasus(db_session, penulis, status=CaseStatus.NEEDS_REVISION)
    _putaran(
        db_session,
        kasus,
        [
            (penyetuju, VerdictDecision.APPROVE, None),
            (perevisi, VerdictDecision.REVISE, KOMENTAR),
        ],
    )
    lama = db_session.query(ReviewVerdict).filter_by(comment=KOMENTAR).one()

    # Act
    hasil, assign, notify = _ajukan(db_session, kasus, penulis)

    # Assert
    assert hasil.round_no == 2
    assert hasil.round_status == RoundStatus.OPEN
    baru = (
        db_session.query(ReviewRound)
        .filter_by(case_version_id=kasus.current_version_id, round_no=2)
        .one()
    )
    assert baru.status == RoundStatus.OPEN
    tugas = _tugas(db_session, baru)
    tanpa_verdict = [baris for baris in tugas if _verdict(db_session, baris) is None]
    assert [baris.reviewer_id for baris in tanpa_verdict] == [perevisi]
    assert tanpa_verdict[0].source == AssignmentSource.SYSTEM
    assert tanpa_verdict[0].status == AssignmentStatus.ACTIVE
    dibawa = [verdict for baris in tugas if (verdict := _verdict(db_session, baris)) is not None]
    assert len(dibawa) == 1
    assert dibawa[0].decision == VerdictDecision.APPROVE
    assert dibawa[0].carried_from_verdict_id == (
        db_session.query(ReviewVerdict)
        .filter_by(decision=VerdictDecision.APPROVE, carried_from_verdict_id=None)
        .one()
        .id
    )
    assert {baris.reviewer_id for baris in tugas} == {penyetuju, perevisi}
    assert ketiga not in {baris.reviewer_id for baris in tugas}
    db_session.refresh(lama)
    assert lama.comment == KOMENTAR
    assert lama.decision == VerdictDecision.REVISE
    assert assign.call_count == 0
    assert notify.call_count == 1
    diberitahu = next(arg for arg in notify.call_args.args if isinstance(arg, list))
    assert diberitahu == [perevisi]
    pengajuan = [
        baris
        for baris in db_session.query(AuditLog).filter_by(action="case.submitted")
        if (baris.after or {}).get("round_no") == 2
    ]
    assert len(pengajuan) == 1
    assert pengajuan[0].actor_user_id == penulis
    assert pengajuan[0].actor_role == "author"
    assert pengajuan[0].case_id == kasus.id


def test_dua_perevisi_keduanya_ditugaskan_lagi_tanpa_approval_dibawa(db_session):
    """Kalau keduanya meminta revisi, tidak ada yang dibawa dan keduanya meninjau lagi."""
    # Arrange
    penulis = _user(db_session, 1, Role.AUTHOR)
    pertama = _user(db_session, 2, Role.REVIEWER)
    kedua = _user(db_session, 3, Role.REVIEWER)
    kasus = _kasus(db_session, penulis, status=CaseStatus.NEEDS_REVISION)
    _putaran(
        db_session,
        kasus,
        [
            (pertama, VerdictDecision.REVISE, "Jelaskan unsur pertama."),
            (kedua, VerdictDecision.REVISE, "Jelaskan unsur kedua."),
        ],
    )

    # Act
    _hasil, _assign, notify = _ajukan(db_session, kasus, penulis)

    # Assert
    baru = (
        db_session.query(ReviewRound)
        .filter_by(case_version_id=kasus.current_version_id, round_no=2)
        .one()
    )
    tugas = _tugas(db_session, baru)
    assert {baris.reviewer_id for baris in tugas} == {pertama, kedua}
    assert all(_verdict(db_session, baris) is None for baris in tugas)
    assert (
        db_session.query(ReviewVerdict)
        .filter(ReviewVerdict.carried_from_verdict_id.is_not(None))
        .count()
        == 0
    )
    assert notify.call_count == 1
    diberitahu = next(arg for arg in notify.call_args.args if isinstance(arg, list))
    assert set(diberitahu) == {pertama, kedua}
    assert db_session.query(ReviewVerdict).filter_by(comment="Jelaskan unsur pertama.").one()
    assert db_session.query(ReviewVerdict).filter_by(comment="Jelaskan unsur kedua.").one()


@pytest.mark.parametrize(
    ("status_round", "keputusan"),
    [
        (RoundStatus.AWAITING_ASSIGNMENT, None),
        (RoundStatus.OPEN, None),
        (RoundStatus.DECIDED, RoundDecision.APPROVED),
    ],
)
def test_pengajuan_ulang_ditolak_bila_bukan_keputusan_revisi(db_session, status_round, keputusan):
    """Round terakhir harus decided dengan keputusan revise."""
    # Arrange
    penulis = _user(db_session, 1, Role.AUTHOR)
    kasus = _kasus(db_session, penulis, status=CaseStatus.NEEDS_REVISION)
    db_session.add(
        ReviewRound(
            case_id=kasus.id,
            case_version_id=kasus.current_version_id,
            round_no=1,
            status=status_round,
            decision=keputusan,
        )
    )
    db_session.commit()

    # Act
    with pytest.raises(ConflictError):
        _ajukan(db_session, kasus, penulis)

    # Assert
    assert db_session.query(ReviewRound).filter_by(round_no=2).count() == 0
    db_session.rollback()
    assert db_session.get(Case, kasus.id).current_version.status == CaseStatus.NEEDS_REVISION


def test_pengajuan_ulang_ditolak_bila_belum_ada_round(db_session):
    # Arrange
    penulis = _user(db_session, 1, Role.AUTHOR)
    kasus = _kasus(db_session, penulis, status=CaseStatus.NEEDS_REVISION)

    # Act
    with pytest.raises(ConflictError):
        _ajukan(db_session, kasus, penulis)

    # Assert
    assert db_session.query(ReviewRound).count() == 0
    db_session.rollback()
    assert db_session.get(Case, kasus.id).current_version.status == CaseStatus.NEEDS_REVISION
