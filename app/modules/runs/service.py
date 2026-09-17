"""Logika bisnis modul runs.

PBI-11, PBI-12, PBI-13 Eksekusi pengukuran ke produk AI.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-11, PBI-12, PBI-13): implementasikan sesuai acceptance criteria.
"""
