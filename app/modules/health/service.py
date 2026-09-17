"""Logika untuk pemeriksaan kesehatan aplikasi.

Modul ini sengaja dibuat lengkap sebagai CONTOH POLA. Perhatikan bahwa
service tidak menyentuh HTTP sama sekali, dan router tidak menyentuh
database sama sekali. Ikuti pola yang sama untuk modul lain.

Catatan desain: endpoint ini sengaja TIDAK memakai dependency get_db.
Kalau database mati, health harus tetap menjawab 200 dengan
database: "unreachable", bukan 500. Dengan begitu monitoring bisa
membedakan "aplikasi mati" dari "aplikasi hidup tapi database mati".
"""

from sqlalchemy import text

from app.modules.health.schemas import HealthResponse
from app.shared.config import get_settings
from app.shared.database import get_engine


def check_health() -> HealthResponse:
    settings = get_settings()

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:  # noqa: BLE001
        database_status = "unreachable"

    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        database=database_status,
    )
