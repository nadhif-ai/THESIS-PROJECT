"""Provider settings persistence and live model selection without paid calls."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
        "answer_provider": "9router",
        "openrouter_model": "openai/gpt-6-luna",
        "ninerouter_model": "cx/gpt-6-luna[1m]",
        "eval_model": "deepseek/deepseek-v4.1-flash",
        "product_intent_model": "z-ai/glm-5.3-flash",
        "semantic_top_k": 5,
    }
    with client() as browser:
        assert browser.put("/admin/api/settings", json=payload).status_code == 401
        authorize(browser)
        initial = browser.get("/admin/api/settings").json()
        assert initial["answer_provider"] == "openrouter"
        assert initial["providers"]["9router"] is False
        assert initial["product_intent_model"] == get_settings().product_intent_model
        assert browser.put("/admin/api/settings", json=payload).status_code == 200
        store.close_pool()
        saved = browser.get("/admin/api/settings").json()
        assert all(saved[key] == value for key, value in payload.items())
        for model in ("azure/gpt-5.6-terra-20260709-global", "azure/gpt-5.6-luna-20260709-global", "cx/gpt-6-luna[1m]", "glm/glm-5.3-flash"):
            assert browser.put("/admin/api/settings", json={**payload, "ninerouter_model": model}).status_code == 200
        del payload["product_intent_model"]
        del payload["answer_provider"]
        del payload["ninerouter_model"]
        saved = browser.put("/admin/api/settings", json=payload).json()
        assert saved["product_intent_model"] == "z-ai/glm-5.3-flash"
        assert saved["answer_provider"] == "9router"
        assert saved["ninerouter_model"] == "glm/glm-5.3-flash"
        assert "offline-test-key" not in json.dumps(saved)
        for invalid in ("", "model with spaces", "x" * 161):
            assert browser.put("/admin/api/settings", json={**payload, "product_intent_model": invalid}).status_code == 422
            assert browser.put("/admin/api/settings", json={**payload, "ninerouter_model": invalid}).status_code == 422
        assert browser.put("/admin/api/settings", json={**payload, "answer_provider": "other"}).status_code == 422
        assert store.get_setting("product_intent_model") == "z-ai/glm-5.3-flash"


def test_saved_answer_provider_is_used_without_restarting(pg_live, monkeypatch):
    seed_active()
    calls = []
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [])

    def llm(*args):
        calls.append(args)
        return SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Konfirmasi ke admin, Kak."))

    monkeypatch.setattr(chain, "get_llm", llm)
    rag = chain.RAGChain()
    store.set_settings({"answer_provider": "9router", "ninerouter_model": "cx/gpt-6-luna[1m]"})
    first = rag.run("Tanya produk", "provider-test", channel="playground")
    store.set_settings({"answer_provider": "openrouter", "openrouter_model": "openai/gpt-6-luna"})
    second = rag.run("Tanya produk lagi", "provider-test", channel="playground")
    pinned = rag.run("Tanya produk berikutnya", "provider-test", channel="playground", model_provider="9router")
    assert calls[-3:] == [("cx/gpt-6-luna[1m]", "9router"), ("openai/gpt-6-luna", "openrouter"), ("cx/gpt-6-luna[1m]", "9router")]
    assert first.error is None and second.error is None and pinned.error is None


def test_intent_and_scoring_accept_provider_qualified_models(pg_live):
    with client() as browser:
        authorize(browser)
        for model in ("azure/gpt-5.6-terra-20260709-global", "azure/gpt-5.6-luna-20260709-global", "cx/gpt-6-luna[1m]", "glm/glm-5.3-flash"):
            payload = {"openrouter_model": "openai/gpt-6-luna", "semantic_top_k": 5,
                       "product_intent_model": "9router::" + model, "eval_model": "9router::" + model}
            response = browser.put("/admin/api/settings", json=payload)
            assert response.status_code == 200
            store.close_pool()
            saved = browser.get("/admin/api/settings").json()
            assert saved["product_intent_model"] == payload["product_intent_model"]
            assert saved["eval_model"] == payload["eval_model"]


def test_9router_uses_openai_chat_completions_and_its_own_credentials(monkeypatch):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, self.headers.get("Authorization"), body))
            response = {"id": "offline", "object": "chat.completion", "created": 1,
                        "model": body["model"], "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "OK"}}]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/v1"
    monkeypatch.setattr(models, "get_settings", lambda: SimpleNamespace(
        openai_api_key="9router-test", openai_endpoint=endpoint,
        openrouter_api_key="openrouter-test", openrouter_base_url=endpoint,
        openrouter_model="openrouter/default", ninerouter_model="cx/gpt-6-luna[1m]",
    ))
    models.get_llm.cache_clear()
    try:
        model = "cx/gpt-6-luna[1m]"
        assert models.get_llm(model, "9router").invoke("Hello").content == "OK"
        assert models.get_llm(model, "openrouter").invoke("Hello").content == "OK"
        assert [row[:2] for row in requests] == [
            ("/v1/chat/completions", "Bearer 9router-test"),
            ("/v1/chat/completions", "Bearer openrouter-test"),
        ]
        assert all(row[2]["model"] == model for row in requests)
        assert "provider" not in requests[0][2]
    finally:
        models.get_llm.cache_clear()
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


@pytest.mark.parametrize("key, endpoint", [("", "https://example.test/v1"), ("test-key", "")])
def test_9router_requires_both_its_key_and_endpoint(monkeypatch, key, endpoint):
    monkeypatch.setattr(models, "get_settings", lambda: SimpleNamespace(openai_api_key=key, openai_endpoint=endpoint))
    models.get_llm.cache_clear()
    with pytest.raises(ValueError, match="OPENAI_API_KEY and OPENAI_ENDPOINT"):
        models.get_llm("cx/gpt-6-luna[1m]", "9router")


def test_saved_intent_model_reaches_classification_and_provenance(pg_live, monkeypatch):
    seed_active()
    store.set_setting("product_intent_model", "9router::cx/gpt-6-luna[1m]")
    observed = []

    def extract(*args, **kwargs):
        observed.append(kwargs["model"])
        return product_intent.failed_intent()

    monkeypatch.setattr(product_intent, "extract", extract)
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [])
    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="Konfirmasi ke admin, Kak.")))
    result = chain.RAGChain().run("Tanya produk", "provider-model-test", channel="playground")
    assert observed == ["9router::cx/gpt-6-luna[1m]"]
    assert result.media_decision["intent_model"] == "9router::cx/gpt-6-luna[1m]"


@pytest.mark.parametrize("selected", ["z-ai/glm-5.3-flash", "openai/gpt-oss-20b", "9router::cx/gpt-6-luna[1m]"])
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
