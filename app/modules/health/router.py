"""Endpoint kesehatan aplikasi.

Dipakai oleh CI, monitoring, dan untuk memastikan deployment berhasil.
Tidak butuh autentikasi.
"""

from fastapi import APIRouter

from app.modules.health import service
from app.modules.health.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Cek kesehatan aplikasi")
def get_health() -> HealthResponse:
    return service.check_health()
