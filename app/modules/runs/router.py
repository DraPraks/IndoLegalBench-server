"""Endpoint HTTP modul runs.

PBI-11, PBI-12, PBI-13 Eksekusi pengukuran ke produk AI.

Cakupan modul ini:
- Belum dikerjakan di Sprint 1
- Dijadwalkan mulai Sprint 3

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-11, PBI-12, PBI-13): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/runs", tags=["runs"])
