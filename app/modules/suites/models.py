"""Tabel database milik modul suites.

ATURAN: file ini hanya boleh diimpor oleh file lain di dalam
app/modules/suites/. Modul lain yang butuh data suite memanggil
suites.service, bukan tabel ini langsung.

TODO(PBI-2): lengkapi kolom sesuai ERD pada sub task
"[SA] ERD suite & state diagram".
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class SuiteStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Suite(Base):
    __tablename__ = "suites"

    # Uuid generik SQLAlchemy 2.0, jadi tabel yang sama bisa dipakai
    # PostgreSQL di production dan SQLite saat test.
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SuiteStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
