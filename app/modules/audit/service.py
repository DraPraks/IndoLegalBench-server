"""Logika bisnis modul audit.

PBI-18 Jejak audit menyeluruh.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.

TODO(PBI-18): implementasikan sesuai acceptance criteria.
"""
