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

    # Zitadel. AUTH_OIDC_MODE=mock until PBI 89 ready.
    auth_oidc_mode: str = "fake"  # fake | zitadel
    public_base_url: str = "http://localhost:8000"
    zitadel_issuer: str = ""
    zitadel_client_id: str = "fake-client"
    zitadel_audience: str = ""
    zitadel_client_secret: str = ""
    zitadel_redirect_uri: str = ""
    fake_oidc_issuer: str = "http://fake-oidc"
    fake_oidc_signing_secret: str = "fake-oidc-hs256-secret-not-for-prod"

    # Sesi
    idle_timeout_minutes: int = 30
    session_cookie_name: str = "veritask_session"
    cookie_secure: bool = False

    # Kunci enkripsi kredensial provider, dipakai PBI-10
    # Jangan pernah di-commit. Isi lewat .env atau secret manager.
    credential_encryption_key: str = ""

    @property
    def frontend_origin(self) -> str:
        if self.cors_origins:
            return self.cors_origins[0].rstrip("/")
        return "http://localhost:3000"

    @property
    def redirect_uri(self) -> str:
        if self.zitadel_redirect_uri:
            return self.zitadel_redirect_uri.rstrip("/")
        return f"{self.public_base_url.rstrip('/')}/auth/callback"

    @property
    def post_logout_redirect_uri(self) -> str:
        return f"{self.frontend_origin}/login"

    @property
    def auth_done_url(self) -> str:
        return f"{self.frontend_origin}/auth/done"


@lru_cache
def get_settings() -> Settings:
    """Dipakai sebagai dependency FastAPI, hasilnya di-cache."""
    return Settings()
