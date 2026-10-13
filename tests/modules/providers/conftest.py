from collections.abc import Callable

import httpx
import pytest
from cryptography.fernet import Fernet

from app.modules.providers.adapters import http as provider_http
from app.shared.config import get_settings

ProviderHandler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", key)
    get_settings.cache_clear()
    yield key
    get_settings.cache_clear()


@pytest.fixture
def provider_replies(monkeypatch) -> Callable[[ProviderHandler], None]:
    real_client = httpx.Client

    def install(handler: ProviderHandler) -> None:
        def client_with_fake_transport(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_client(*args, **kwargs)

        monkeypatch.setattr(provider_http.httpx, "Client", client_with_fake_transport)

    return install
