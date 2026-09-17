"""Tabel database milik modul providers.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/providers/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-10): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
