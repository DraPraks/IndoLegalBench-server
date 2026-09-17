"""Tabel database milik modul reports.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/reports/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-15, PBI-16, PBI-17): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
