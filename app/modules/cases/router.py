"""Endpoint HTTP modul cases.

PBI-3 Menulis kasus hukum terstruktur.

Cakupan modul ini:
- Editor kasus terstruktur
- Validasi real-time dari kontrak OpenAPI
- ID kasus unik lintas suite
- Rujukan hukum sampai level pasal
- Minimal satu jebakan sebelum bisa diajukan review
- Status draft dan indikator kelengkapan

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-3): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/cases", tags=["cases"])
