"""Provider settings persistence and live model selection without paid calls."""

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.admin import store
from app.backend import models, chain, product_intent, vectorstore
from app.config.settings import get_settings
from testing.test_global_knowledge import seed_active
from testing.test_prompt_settings import client, authorize


def test_model_settings_persist_and_legacy_clients_preserve_intent(pg_live):
    payload = {
        "openrouter_model": "openai/gpt-6-luna",
        "eval_model": "deepseek/deepseek-v4.1-flash",
        "product_intent_model": "z-ai/glm-5.3-flash",
        "semantic_top_k": 5,
    }
    with client() as browser:
        assert browser.put("/admin/api/settings", json=payload).status_code == 401
        authorize(browser)
        assert browser.get("/admin/api/settings").json()["product_intent_model"] == get_settings().product_intent_model
        assert browser.put("/admin/api/settings", json=payload).status_code == 200
        store.close_pool()
        saved = browser.get("/admin/api/settings").json()
        assert all(saved[key] == value for key, value in payload.items())
        del payload["product_intent_model"]
        assert browser.put("/admin/api/settings", json=payload).json()["product_intent_model"] == "z-ai/glm-5.3-flash"
        for invalid in ("", "model with spaces", "x" * 161):
            assert browser.put("/admin/api/settings", json={**payload, "product_intent_model": invalid}).status_code == 422
        assert store.get_setting("product_intent_model") == "z-ai/glm-5.3-flash"


def test_saved_intent_model_reaches_classification_and_provenance(pg_live, monkeypatch):
    seed_active()
    store.set_setting("product_intent_model", "openai/gpt-oss-20b")
    observed = []

    def extract(*args, **kwargs):
        observed.append(kwargs["model"])
        return product_intent.failed_intent()

    monkeypatch.setattr(product_intent, "extract", extract)
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [])
    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Konfirmasi ke admin, Kak.")))
    result = chain.RAGChain().run("Tanya produk", "provider-model-test", channel="playground")
    assert observed == ["openai/gpt-oss-20b"]
    assert result.media_decision["intent_model"] == "openai/gpt-oss-20b"


@pytest.mark.parametrize("selected", ["z-ai/glm-5.3-flash", "openai/gpt-oss-20b"])
def test_structured_client_uses_saved_model_without_process_restart(pg_live, monkeypatch, selected):
    store.set_setting("product_intent_model", selected)
    calls = []

    def llm(model, **kwargs):
        calls.append(model)

        async def invoke(messages):
            return {
                "parsed": {"consistent": True},
                "raw": SimpleNamespace(usage_metadata={}, response_metadata={}),
            }

        fake = SimpleNamespace(
            openai_api_key=SecretStr("offline-test-key"),
            openai_api_base="https://provider.test/api/v1", openai_organization=None,
            max_retries=0, default_headers=None, default_query=None,
            with_structured_output=lambda *args, **kwargs: SimpleNamespace(ainvoke=invoke),
        )
        fake.model_copy = lambda **kwargs: fake
        return fake

    monkeypatch.setattr(models, "get_llm", llm)
    result, _ = models.structured_response({}, [], timeout=15)
    assert result == {"consistent": True}
    assert calls == [selected]
