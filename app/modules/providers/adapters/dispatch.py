"""Pilih adapter dari nilai string provider_type, bukan dari anggota enum.

gemini_interactions dan anthropic_messages belum ada di enum cabang ini.
Dispatch lewat string supaya tetap jalan setelah enum itu menggantikan custom_http.
"""

from app.modules.providers.adapters.anthropic_messages import AnthropicMessagesAdapter
from app.modules.providers.adapters.base import ConnectionTestResult, ProviderAdapter
from app.modules.providers.adapters.gemini_interactions import GeminiInteractionsAdapter
from app.modules.providers.adapters.openai_compatible import OpenAICompatibleAdapter

_ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "openai_compatible": OpenAICompatibleAdapter,
    "gemini_interactions": GeminiInteractionsAdapter,
    "anthropic_messages": AnthropicMessagesAdapter,
}

UNSUPPORTED = "connection test is not available for this provider type"


def run_connection_test(
    *,
    provider_type: str,
    base_url: str,
    model_name: str,
    api_key: str,
) -> ConnectionTestResult:
    adapter_cls = _ADAPTERS.get(provider_type)
    if adapter_cls is None:
        return ConnectionTestResult(status="failed", message=UNSUPPORTED)
    return adapter_cls(base_url=base_url, model_name=model_name, api_key=api_key).test_connection()
