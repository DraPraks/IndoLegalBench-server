"""Endpoint HTTP modul audit.

PBI-18 Jejak audit menyeluruh.

Cakupan modul ini:
- Belum dikerjakan di Sprint 1
- Catatan append-only, tidak bisa diubah atau dihapus

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-18): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/audit", tags=["audit"])
