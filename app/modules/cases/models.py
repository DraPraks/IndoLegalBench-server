"""Tabel database milik modul cases.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/cases/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-3): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
