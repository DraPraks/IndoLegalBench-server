"""Tabel database milik modul audit.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/audit/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-18): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
