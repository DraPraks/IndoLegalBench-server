"""Bentuk request dan response modul cases.

Schema di sini yang menjadi sumber kontrak OpenAPI. Aturan isian
didelegasikan ke validation.py supaya POST, PUT, dan kelengkapan
memakai definisi yang sama.

Bentuk Case ini placeholder sampai SCRUM-103 selesai. Pola case_code
juga placeholder Klarifikasi #7.
"""

import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.cases.models import CaseStatus, SplitTag
from app.modules.cases.validation import PLACEHOLDER_CASE_CODE_PATTERN, periksa_isian


def _rapikan(nilai: str) -> str:
    return nilai.strip()


class CaseIdentity(BaseModel):
    title: str = Field(min_length=1, max_length=300, description="Judul pertanyaan")
    question: str = Field(min_length=1, max_length=20000, description="Pertanyaan hukum")
    category: str | None = Field(default=None, max_length=120)

    @field_validator("title", "question")
    @classmethod
    def wajib_berisi(cls, nilai: str) -> str:
        return _rapikan(nilai)

    @field_validator("category")
    @classmethod
    def kategori_rapi(cls, nilai: str | None) -> str | None:
        if nilai is None:
            return None
        bersih = nilai.strip()
        return bersih or None


class LegalRef(BaseModel):
    """Satu rujukan. regulation_type, regulation_number, dan pasal wajib."""

    regulation_type: str = Field(min_length=1, max_length=40)
    regulation_number: str = Field(min_length=1, max_length=40)
    year: int | None = Field(default=None, ge=1, le=9999)
    pasal: str = Field(min_length=1, max_length=40)
    ayat: str | None = Field(default=None, max_length=20)
    huruf: str | None = Field(default=None, max_length=8)

    @field_validator("regulation_type", "regulation_number", "pasal")
    @classmethod
    def wajib_berisi(cls, nilai: str) -> str:
        return _rapikan(nilai)

    @field_validator("ayat", "huruf")
    @classmethod
    def opsional_rapi(cls, nilai: str | None) -> str | None:
        if nilai is None:
            return None
        bersih = nilai.strip()
        return bersih or None


class AnswerCriteria(BaseModel):
    must_contain: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    expected_conclusion: str | None = None


class Trap(BaseModel):
    description: str = Field(min_length=1, max_length=2000)
    expected_model_behavior: str | None = Field(default=None, max_length=2000)

    @field_validator("description")
    @classmethod
    def wajib_berisi(cls, nilai: str) -> str:
        return _rapikan(nilai)


class CaseWrite(BaseModel):
    """Badan POST dan PUT. Status tidak diterima dari klien; server yang mengunci draft."""

    case_code: str = Field(
        min_length=2,
        max_length=64,
        pattern=PLACEHOLDER_CASE_CODE_PATTERN,
        description=(
            "PLACEHOLDER Klarifikasi #7. Pola sementara, bukan pola final: "
            "diawali huruf atau angka, lalu huruf, angka, titik, garis bawah, "
            "atau tanda hubung."
        ),
    )
    identity: CaseIdentity
    legal_refs: list[LegalRef] = Field(
        min_length=1,
        description="Minimal satu rujukan, masing-masing sampai level pasal.",
    )
    answer_criteria: AnswerCriteria = Field(default_factory=AnswerCriteria)
    traps: list[Trap] = Field(default_factory=list)
    split_tag: SplitTag

    @field_validator("case_code", mode="before")
    @classmethod
    def kode_rapi(cls, nilai: Any) -> Any:
        if isinstance(nilai, str):
            return nilai.strip()
        return nilai

    @model_validator(mode="after")
    def aturan_terpusat(self) -> Self:
        periksa_isian(self.model_dump(mode="json"))
        return self


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    suite_id: uuid.UUID
    case_code: str
    identity: CaseIdentity
    legal_refs: list[LegalRef]
    answer_criteria: AnswerCriteria
    traps: list[Trap]
    split_tag: SplitTag
    status: CaseStatus
    completeness_pct: int = Field(ge=0, le=100)
    version: int
    created_at: datetime
    updated_at: datetime


class CaseSummary(BaseModel):
    id: uuid.UUID
    case_code: str
    title: str
    split_tag: SplitTag
    status: CaseStatus
    completeness_pct: int = Field(ge=0, le=100)
    updated_at: datetime
