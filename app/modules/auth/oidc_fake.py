"""Fake OIDC IdP for local/test (`AUTH_OIDC_MODE=fake`).

- Mimics authorize, code exchange, end_session (no Zitadel Cloud)
- `GET /_fake/oidc/authorize` redirects to `/auth/callback`; `?sub=` picks seed `zitadel_sub`
- Not for production; switch to `zitadel` when issuer + client id exist
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from jose import jwt

from app.modules.auth.oidc import TokenResult
from app.modules.auth.pkce import code_challenge_s256
from app.shared.config import Settings, get_settings
from app.shared.exceptions import OidcExchangeFailedError

DEFAULT_SUB = "111111111111111111"


class FakeOidcClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # TODO: process-local codes; not a real token endpoint / JWKS
        self._codes: dict[str, dict[str, str]] = {}

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
        extra_params: dict[str, str] | None = None,
    ) -> str:
        params = {
            "client_id": self.settings.zitadel_client_id,
            "redirect_uri": self.settings.redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if extra_params:
            params.update(extra_params)
        return f"/_fake/oidc/authorize?{urlencode(params)}"

    def issue_code(
        self,
        *,
        sub: str,
        nonce: str,
        code_challenge: str,
        redirect_uri: str,
    ) -> str:
        code = uuid4().hex
        self._codes[code] = {
            "sub": sub,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "redirect_uri": redirect_uri,
        }
        return code

    def exchange_code(self, *, code: str, code_verifier: str, expected_nonce: str) -> TokenResult:
        record = self._codes.pop(code, None)
        if record is None:
            raise OidcExchangeFailedError("Authorization code is invalid or already used.")
        if code_challenge_s256(code_verifier) != record["code_challenge"]:
            raise OidcExchangeFailedError("PKCE verification failed.")
        if expected_nonce != record["nonce"]:
            raise OidcExchangeFailedError("Nonce mismatch.")

        now = datetime.now(timezone.utc)
        payload = {
            "iss": self.settings.fake_oidc_issuer,
            "sub": record["sub"],
            "aud": self.settings.zitadel_client_id,
            "nonce": record["nonce"],
            "sid": f"fake-sid-{record['sub'][-6:]}",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
        # TODO: HS256 + shared secret; Zitadel uses RS256 + JWKS
        raw = jwt.encode(payload, self.settings.fake_oidc_signing_secret, algorithm="HS256")
        return TokenResult(
            sub=record["sub"],
            nonce=record["nonce"],
            sid=payload["sid"],
            raw_id_token=raw,
        )

    def end_session_url(self, *, id_token_hint: str | None = None) -> str:
        params = {
            "client_id": self.settings.zitadel_client_id,
            "post_logout_redirect_uri": self.settings.post_logout_redirect_uri,
        }
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        return f"/_fake/oidc/end_session?{urlencode(params)}"


_fake_client: FakeOidcClient | None = None


def get_fake_oidc_client() -> FakeOidcClient:
    global _fake_client
    if _fake_client is None:
        _fake_client = FakeOidcClient(get_settings())
    return _fake_client


fake_router = APIRouter(tags=["fake-oidc"])


@fake_router.get("/_fake/oidc/authorize")
def fake_authorize(request: Request) -> RedirectResponse:
    settings = get_settings()
    client = get_fake_oidc_client()
    query = request.query_params
    if query.get("client_id") != settings.zitadel_client_id:
        raise OidcExchangeFailedError("Unknown client_id.")
    redirect_uri = query.get("redirect_uri")
    state = query.get("state")
    nonce = query.get("nonce")
    challenge = query.get("code_challenge")
    if not redirect_uri or not state or not nonce or not challenge:
        raise OidcExchangeFailedError("Missing OIDC authorize parameters.")
    if redirect_uri != settings.redirect_uri:
        raise OidcExchangeFailedError("redirect_uri mismatch.")
    # TODO: auto-approves with no login UI; `sub` is attacker-chosen if fake is left on
    sub = query.get("sub") or query.get("login_hint") or DEFAULT_SUB
    code = client.issue_code(
        sub=sub,
        nonce=nonce,
        code_challenge=challenge,
        redirect_uri=redirect_uri,
    )
    location = f"/auth/callback?{urlencode({'code': code, 'state': state})}"
    return RedirectResponse(url=location, status_code=302)


@fake_router.get("/_fake/oidc/end_session")
def fake_end_session(post_logout_redirect_uri: str | None = None) -> RedirectResponse:
    # TODO: ignores id_token_hint; Zitadel end_session will not
    settings = get_settings()
    target = post_logout_redirect_uri or settings.post_logout_redirect_uri
    return RedirectResponse(url=target, status_code=302)
