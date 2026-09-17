"""Tabel database milik modul runs.

ATURAN: file ini hanya boleh diimpor dari dalam app/modules/runs/.

Semua model wajib mewarisi Base dari app.shared.database supaya
terdeteksi Alembic.

TODO(PBI-11, PBI-12, PBI-13): definisikan tabel sesuai ERD.
"""

from app.shared.database import Base  # noqa: F401
