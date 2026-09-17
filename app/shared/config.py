"""Konfigurasi aplikasi, dibaca dari environment variable.

Semua setelan aplikasi masuk ke sini. Jangan membaca os.environ langsung
dari dalam modul, selalu lewat get_settings() supaya sumbernya satu.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Aplikasi
    app_name: str = "IndoLegalBench API"
    app_env: str = "local"  # local | staging | production
    debug: bool = True

    # Database
    database_url: str = (
        "postgresql+psycopg://indolegalbench:indolegalbench@localhost:5432/indolegalbench"
    )

    # CORS, diisi dengan origin frontend
    cors_origins: list[str] = ["http://localhost:3000"]

    # Zitadel, diisi saat PBI-1 dikerjakan
    zitadel_issuer: str = ""
    zitadel_client_id: str = ""
    zitadel_audience: str = ""

    # Sesi
    idle_timeout_minutes: int = 30

    # Kunci enkripsi kredensial provider, dipakai PBI-10
    # Jangan pernah di-commit. Isi lewat .env atau secret manager.
    credential_encryption_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Dipakai sebagai dependency FastAPI, hasilnya di-cache."""
    return Settings()
