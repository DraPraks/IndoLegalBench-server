"""Endpoint HTTP modul reports.

PBI-15, PBI-16, PBI-17 Laporan perbandingan antar produk.

Cakupan modul ini:
- Belum dikerjakan di Sprint 1
- Dijadwalkan mulai Sprint 4

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-15, PBI-16, PBI-17): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])
