"""Endpoint HTTP modul auth.

PBI-1 Login aman dan manajemen akses tim.

Cakupan modul ini:
- Login SSO lewat Zitadel
- Empat peran: Author, Reviewer, Admin, Viewer
- Pembatasan aksi per peran (RBAC)
- Idle timeout sesi
- Admin mengelola anggota tim

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-1): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
