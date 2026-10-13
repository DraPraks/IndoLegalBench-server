"""SCRUM-135: re-test of the SCRUM-133 registry fixes, scenario by scenario."""

import httpx
import pytest

from app.modules.auth.seeds import ADMIN_SUB
from tests.login import complete_login

_SECRET = "retest-provider-token-6hVd"  # pragma: allowlist secret
_BASE = "https://provider.example.test/v1/endpoint"
_PROVIDER_TYPES = ["openai_compatible", "gemini_interactions", "anthropic_messages"]


def _wrong_key(request: httpx.Request) -> httpx.Response:
    return httpx.Response(401, json={"error": "invalid api key"})


def _wrong_model(request: httpx.Request) -> httpx.Response:
    return httpx.Response(404, json={"error": "model not found"})


def _host_down(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("name or service not known", request=request)


def _slow_server(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("read timed out", request=request)


_SCENARIOS = [
    pytest.param(_wrong_key, "access_denied", id="api-key-salah"),
    pytest.param(_wrong_model, "model_not_found", id="model-salah"),
    pytest.param(_host_down, "unreachable", id="url-host-mati"),
    pytest.param(_slow_server, "timeout", id="server-lambat"),
]


def _register(client, provider_type: str) -> str:
    created = client.post(
        "/admin/providers",
        json={
            "name": f"Retest {provider_type}",
            "provider_type": provider_type,
            "base_url": _BASE,
            "model_name": "retest-model",
            "credential": _SECRET,
            "rate_limit_per_minute": 30,
            "monthly_budget_idr": "1500000.00",
        },
    )
    assert created.status_code == 201
    return created.json()["id"]


@pytest.mark.parametrize("provider_type", _PROVIDER_TYPES)
@pytest.mark.parametrize(("provider_reply", "category"), _SCENARIOS)
def test_failed_connection_test_reports_the_scenario_category(
    client, db_session, encryption_key, provider_replies, provider_type, provider_reply, category
):
    provider_replies(provider_reply)
    complete_login(client, db_session, ADMIN_SUB)
    product_id = _register(client, provider_type)

    tested = client.post(f"/admin/providers/{product_id}/test-connection")
    reopened = client.get(f"/admin/providers/{product_id}")

    assert tested.status_code == 200
    assert tested.json()["status"] == "failed"
    assert tested.json()["error_category"] == category
    assert reopened.json()["last_test_status"] == "failed"
    assert reopened.json()["last_test_error_category"] == category
