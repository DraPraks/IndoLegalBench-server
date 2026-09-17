"""Endpoint HTTP modul providers.

PBI-10 Registri produk AI yang akan diukur.

Cakupan modul ini:
- Pendaftaran produk AI beserta batas pemakaian
- Kredensial terenkripsi, tidak pernah ditampilkan ulang
- Uji koneksi ke produk AI
- Aktifkan dan nonaktifkan produk
- Pencatatan versi model per pengukuran

Router hanya menerjemahkan HTTP ke pemanggilan service. Tidak ada
logika bisnis dan tidak ada query database di file ini.

TODO(PBI-10): tambahkan endpoint sesuai acceptance criteria.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/providers", tags=["providers"])
