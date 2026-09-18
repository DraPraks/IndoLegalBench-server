"""OIDC port used by auth service (IdP-agnostic).

- Implementors: `ZitadelOidcClient`, `FakeOidcClient` (`authorization_url`, `exchange_code`, `end_session_url`)
- Factory: `get_oidc_client()` from `AUTH_OIDC_MODE`
- `TokenResult`: `sub`, `nonce`, optional `sid`, raw `id_token` (logout)
"""

from typing import Protocol

from pydantic import BaseModel


class TokenResult(BaseModel):
    sub: str
    nonce: str
    sid: str | None = None
    email: str | None = None
    name: str | None = None
    raw_id_token: str


class OidcClient(Protocol):
    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
        extra_params: dict[str, str] | None = None,
    ) -> str: ...

    def exchange_code(self, *, code: str, code_verifier: str, expected_nonce: str) -> TokenResult: ...

    def end_session_url(self, *, id_token_hint: str | None = None) -> str: ...


def get_oidc_client() -> OidcClient:
    from app.modules.auth.oidc_fake import get_fake_oidc_client
    from app.modules.auth.oidc_zitadel import ZitadelOidcClient
    from app.shared.config import get_settings

    settings = get_settings()
    if settings.auth_oidc_mode == "zitadel":
        return ZitadelOidcClient(settings)
    return get_fake_oidc_client()
