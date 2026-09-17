"""Modul validasi terpusat untuk kasus hukum.

PBI-3, sub task "[BE] Case endpoint & satu modul validasi terpusat".

INI FILE PALING PENTING DI SELURUH SPRINT 1.

Aturan validasi kasus hukum ditulis SEKALI di sini, diturunkan dari
schema OpenAPI Case. Jangan menulis ulang aturan yang sama di frontend
secara manual. Frontend memakai tipe hasil generate dari kontrak yang
sama, sehingga backend dan frontend tidak akan pernah berbeda aturan.

Satu definisi dipakai untuk empat hal:
1. Validasi di backend saat kasus disimpan
2. Validasi real-time di frontend saat Author mengetik
3. Format ekspor cases.json yang dibaca AiYU
4. Dokumentasi API otomatis

Aturan yang harus ditegakkan, sesuai acceptance criteria PBI-3:
- Bagian wajib: identitas pertanyaan, rujukan hukum, kriteria jawaban, tag dev/test
- Kesalahan format dan field wajib kosong terdeteksi sebelum kasus disimpan
- ID kasus unik di seluruh suite, bukan hanya di dalam satu suite
- Rujukan hukum wajib sampai level pasal, bukan hanya nama peraturan
- Kasus wajib punya minimal satu jebakan sebelum bisa diajukan review
- Indikator kelengkapan dihitung dari bagian mana saja yang sudah terisi

TODO(PBI-3): implementasikan setelah sub task
"[SA] Case schema contract (ERD)" selesai dan kontraknya disepakati.
"""
