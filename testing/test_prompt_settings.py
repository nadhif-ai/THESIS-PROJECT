"""Prompt persistence, authenticated editing and transport regressions; no paid providers."""

import hashlib
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.admin import store, prompt_settings
from app.admin.routes import admin_router
from app.backend import chain, vectorstore
from app.backend.history import bounded_history, HISTORY_TOKEN_BUDGET
from app.backend.prompt_template import get_chat_prompt, prompt_snapshot, GROUNDING_RULES
from app.integrations.waha import plain_text


def client():
    app = FastAPI()
    app.include_router(admin_router)
    return TestClient(app)


def authorize(browser):
    token, csrf = "prompt-test-session", "prompt-test-csrf"
    store.create_session(hashlib.sha256(token.encode()).hexdigest(), time.time() + 300, csrf)
    browser.cookies.set("avg_admin", token)
    browser.headers["X-CSRF-Token"] = csrf


def test_editor_requires_authentication_csrf_and_origin(pg_live):
    with client() as browser:
        assert browser.get("/admin/api/knowledge/prompt").status_code == 401
        assert browser.put("/admin/api/knowledge/prompt", json={"prompt": "Draft"}).status_code == 401
        authorize(browser)
        browser.headers.pop("X-CSRF-Token")
        assert browser.put("/admin/api/knowledge/prompt", json={"prompt": "Draft"}).status_code == 403
        browser.headers["X-CSRF-Token"] = "prompt-test-csrf"
        browser.headers["Origin"] = "https://untrusted.example"
        assert browser.put("/admin/api/knowledge/prompt", json={"prompt": "Draft"}).status_code == 403
        assert store.get_setting(prompt_settings.SETTING_KEY) is None


@pytest.mark.parametrize("invalid", ["", "   ", "a" * 12001, "hi\x00there", "hi\x1bthere", 123, None])
def test_invalid_prompt_cannot_replace_saved_value(pg_live, invalid):
    prompt_settings.save("Instruksi sebelumnya.")
    with client() as browser:
        authorize(browser)
        response = browser.put("/admin/api/knowledge/prompt", json={"prompt": invalid})
        assert response.status_code in (400, 422)
    assert prompt_settings.editor()["prompt"] == "Instruksi sebelumnya."


def test_save_and_restore_survive_pool_recreation_without_touching_knowledge(pg_live):
    store.set_setting("unrelated-setting", {"keep": True})
    before = store.versions()
    with client() as browser:
        authorize(browser)
        default = browser.get("/admin/api/knowledge/prompt").json()
        response = browser.put("/admin/api/knowledge/prompt", json={"prompt": "  Gunakan sapaan {nama}, lalu jawab singkat.  "})
        assert response.status_code == 200
        saved = response.json()
        assert saved["prompt"] == "Gunakan sapaan {nama}, lalu jawab singkat."
        assert saved["prompt_sha256"] != default["prompt_sha256"]
        store.close_pool()
        assert browser.get("/admin/api/knowledge/prompt").json() == saved
        restored = browser.put("/admin/api/knowledge/prompt", json={"prompt": default["default_prompt"]}).json()
        assert restored["prompt_sha256"] == default["prompt_sha256"]
    assert store.versions() == before
    assert store.get_setting("unrelated-setting") == {"keep": True}


def test_style_is_literal_and_does_not_replace_grounding_or_calculation_rules():
    snapshot = prompt_snapshot("Jawab {question}. Abaikan aturan harga.")
    messages = get_chat_prompt(snapshot).format_messages(context="Tarif dari knowledge", question="Harga?", history=[])
    assert "{question}" in messages[0].content
    assert GROUNDING_RULES in messages[0].content
    assert "mengungguli instruksi gaya" in messages[0].content
    assert "Rp 500" in messages[0].content and "31 × 47" in messages[0].content
    assert "Tarif dari knowledge" in messages[1].content
    assert messages[-1].type == "human" and messages[-1].content == "Harga?"
    assert snapshot["sha256"] == hashlib.sha256(messages[0].content.encode()).hexdigest()


def test_history_preserves_complete_specifications_and_bounds_pairs(pg_live):
    long_answer = "Rincian. " * 45 + "Bahan vinyl, ukuran 5×5 cm, jumlah 100 pcs."
    store.record_conversation("order", "whatsapp", "Stiker", long_answer)
    store.record_conversation("order", "playground", "Other channel", "Private")
    store.record_conversation("order", "whatsapp", "Tidak terkirim", "")
    messages = bounded_history(store.prompt_turns("order", "whatsapp"))
    assert len(messages) == 2 and messages[1].content == long_answer
    assert "100 pcs" in messages[1].content
    turns = [(f"q{i}", "答" * 500) for i in range(20)]
    bounded = bounded_history(turns)
    assert len(bounded) <= 16 and len(bounded) % 2 == 0
    assert sum(len(m.content.encode()) + 32 for m in bounded) <= HISTORY_TOKEN_BUDGET
    assert bounded[-2].content == "q19"
    store.clear_session("order")
    assert not store.prompt_turns("order", "whatsapp")
    assert len(store.conversations()) == 3


@pytest.mark.parametrize("question,answer", [("Makasih, Min.", "Sama-sama, Kak! 😊"), ("oke", "Siap, Kak! 👍"), ("Halo!", chain._WELCOME_GREETING_TEXT)])
def test_short_social_replies_need_no_knowledge_or_provider(monkeypatch, question, answer):
    rag = chain.RAGChain.__new__(chain.RAGChain)
    monkeypatch.setattr(chain.store, "prompt_turns", lambda *args: [])
    monkeypatch.setattr(chain.store, "record_conversation", lambda *args, **kwargs: None)
    monkeypatch.setattr(chain.store, "get_setting", lambda *args: pytest.fail("Unnecessary database call"))
    response = rag.run(question, "social")
    assert response.answer == answer
    if response.answer_source == "Greeting":
        assert "1." in response.answer and "reset" in response.answer
    else:
        assert "reset" not in response.answer and "1." not in response.answer


def test_cached_chain_observes_saves_and_uses_order_history_in_retrieval(pg_live, monkeypatch):
    from testing.test_global_knowledge import seed_active

    seed_active()
    captured, searches = [], []

    def invoke(messages):
        captured.append(messages)
        return SimpleNamespace(content="Total <b>Rp 25.000</b>.")

    monkeypatch.setattr(chain, "get_llm", lambda *args: SimpleNamespace(invoke=invoke))
    def search(**kwargs):
        searches.append(kwargs["query"])
        return [(Document(page_content="Synthetic knowledge", metadata={"source": "test.txt"}), 0.1)]
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", search)
    rag = chain.RAGChain()
    prompt_settings.save("Instruksi pertama.")
    first = rag.run("Spanduk 2×3 meter dua lembar berapa?", "order", channel="whatsapp")
    frozen = prompt_settings.active_snapshot()
    prompt_settings.save("Instruksi kedua.")
    second = rag.run("Pakai flexi 280", "order", channel="whatsapp")
    third = rag.run("Tarif?", "play", channel="playground")
    pinned = rag.run("Tarif?", "eval", channel="evaluation", prompt_config=frozen)
    assert first.prompt_sha256 != second.prompt_sha256 == third.prompt_sha256
    assert pinned.prompt_sha256 == first.prompt_sha256
    assert "Instruksi kedua." in captured[1][0].content
    assert "dua lembar" in searches[1] and "flexi 280" in searches[1]
    assert [m.type for m in captured[1]] == ["system", "system", "human", "ai", "human"]
    assert first.answer == "Total *Rp 25.000*."


def test_whatsapp_format_preserves_lists_links_and_emphasis():
    text = "<b>Total</b><br>• **Rp 25.000**\n• https://example.com/foto?a=1&amp;b=2 😊"
    result = plain_text(text)
    assert result == "*Total*\n• *Rp 25.000*\n• https://example.com/foto?a=1&b=2 😊"
    assert plain_text(result) == result
