"""Logika bisnis modul providers.

PBI-10 Registri produk AI yang akan diukur.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-10): implementasikan sesuai acceptance criteria.
"""
