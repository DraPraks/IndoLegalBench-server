"""Logika bisnis modul reports.

PBI-15, PBI-16, PBI-17 Laporan perbandingan antar produk.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-15, PBI-16, PBI-17): implementasikan sesuai acceptance criteria.
"""
