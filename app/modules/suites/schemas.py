"""Bentuk request dan response modul suites.

Schema di sini yang menjadi sumber kontrak OpenAPI. Kalau file ini
berubah, kontrak API ikut berubah, jadi wajib diumumkan ke tim dan
frontend perlu regenerate tipenya.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200, description="Nama suite, harus unik")
    description: str | None = Field(
        default=None, max_length=1000, description="Tema atau deskripsi singkat suite"
    )


class SuiteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)


class SuiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: str
    case_count: int = Field(default=0, description="Jumlah kasus di dalam suite ini")
    created_at: datetime
    updated_at: datetime
