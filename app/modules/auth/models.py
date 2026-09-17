"""Tabel database milik modul auth.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/auth/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-1): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
