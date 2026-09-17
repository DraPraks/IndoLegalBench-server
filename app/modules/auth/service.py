"""Logika bisnis modul auth.

PBI-1 Login aman dan manajemen akses tim.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-1): implementasikan sesuai acceptance criteria.
"""
