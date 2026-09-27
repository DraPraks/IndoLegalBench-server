"""Tabel database milik modul cases.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/cases/.

Bentuk kolom ini placeholder. Kontrak OpenAPI Case (SCRUM-103) dan
migrasi resmi (SCRUM-105) masih berjalan, jadi nama kolom mengikuti
uraian tiket itu dan boleh berubah kalau kontrak finalnya beda.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class SplitTag(StrEnum):
    DEV = "dev"
    TEST = "test"


class CaseStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"


def _enum(kelas: type[StrEnum], nama: str) -> Enum:
    return Enum(
        kelas,
        name=nama,
        values_callable=lambda members: [member.value for member in members],
    )


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_suite_id", "suite_id"),
        Index("ix_cases_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    suite_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("suites.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # JSON portable. SCRUM-105 yang akan menguncinya sebagai JSONB.
    legal_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    answer_criteria: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    traps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    split_tag: Mapped[SplitTag] = mapped_column(
        _enum(SplitTag, "case_split_tag_enum"), nullable=False
    )
    status: Mapped[CaseStatus] = mapped_column(
        _enum(CaseStatus, "case_status_enum"),
        nullable=False,
        default=CaseStatus.DRAFT,
    )
    completeness: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
