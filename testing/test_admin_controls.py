"""Local database checks; no WhatsApp, embedding, or judge API calls."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin import store
from app.admin.routes import admin_router
from app.config.settings import get_settings
from app.integrations import waha


@pytest.fixture
def admin(pg_live, monkeypatch):
    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_SESSION", "controls-test")
    get_settings.cache_clear()
    with pg_live.admin_connection() as db:
        db.execute("INSERT INTO chatbot.users VALUES(%s,%s,%s)", (
            "admin", "00" * 16, store.hash_password("test-password", "00" * 16),
        ))
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: {"status": "WORKING"})
    app = FastAPI()
    app.include_router(admin_router)
    with TestClient(app) as client:
        login = client.post("/admin/api/login", json={"username": "admin", "password": "test-password"})
        assert login.status_code == 200
        client.headers["X-CSRF-Token"] = login.json()["csrf"]
        yield client
    get_settings.cache_clear()


def incoming(identifier):
    return store.enqueue_inbox("controls-test", identifier, "123@lid", "Synthetic question")


def status(client):
    response = client.get("/admin/api/whatsapp/status")
    assert response.status_code == 200
    return response.json()


def toggle(client, enabled):
    response = client.put("/admin/api/whatsapp/replies", json={"enabled": enabled})
    assert response.status_code == 200
    return response.json()


def test_ignore_is_persistent_scoped_and_preserves_deduplication(admin):
    incoming("failed")
    store.update_inbox("controls-test", "failed", {"status": "failed"})
    attention = status(admin)["attention"]
    assert attention["failed"] == 1
    response = admin.post("/admin/api/whatsapp/attention/ignore", json={"items": attention["items"]})
    assert response.status_code == 200 and response.json()["ignored"] == 1
    assert response.json()["attention"]["items"] == []
    assert not incoming("failed")
    assert store.get_inbox("controls-test", "failed")["status"] == "failed"
    store.close_pool()
    assert status(admin)["attention"]["items"] == []
    incoming("new-failure")
    store.update_inbox("controls-test", "new-failure", {"status": "uncertain"})
    assert status(admin)["attention"]["uncertain"] == 1


def test_ignore_does_not_hide_a_newer_failure(admin):
    incoming("changed")
    store.update_inbox("controls-test", "changed", {"status": "failed"})
    stale = status(admin)["attention"]["items"]
    store.update_inbox("controls-test", "changed", {"status": "uncertain"})
    response = admin.post("/admin/api/whatsapp/attention/ignore", json={"items": stale})
    assert response.json()["ignored"] == 0
    assert status(admin)["attention"]["uncertain"] == 1


def test_pause_skips_pending_and_new_messages_without_replaying(admin):
    assert status(admin)["bot_replies_enabled"] is True
    incoming("generating")
    claimed = store.claim_inbox("controls-test")
    assert claimed["message_id"] == "generating"
    incoming("queued")
    assert toggle(admin, False)["bot_replies_enabled"] is False
    assert incoming("while-off")
    assert not incoming("while-off")
    assert store.claim_inbox("controls-test") is None
    store.close_pool()
    assert status(admin)["bot_replies_enabled"] is False
    assert status(admin)["queue"]["skipped"] == 3
    with store._connection() as db:
        history = db.execute("SELECT question,answer FROM chatbot.conversations").fetchall()
        assert history == [{"question": "Synthetic question", "answer": ""}]
    toggle(admin, True)
    store.update_inbox("controls-test", "generating", {"status": "generating"})
    assert not store.begin_inbox_send("controls-test", "generating")
    assert store.claim_inbox("controls-test") is None
    incoming("after-on")
    assert store.claim_inbox("controls-test")["message_id"] == "after-on"
    assert store.begin_inbox_send("controls-test", "after-on")
    toggle(admin, False)
    assert store.get_inbox("controls-test", "after-on")["status"] == "sending"


def test_pause_during_generation_blocks_send_even_if_reenabled(admin, monkeypatch):
    incoming("inflight")
    row = store.claim_inbox("controls-test")
    def generate(**kwargs):
        toggle(admin, False)
        toggle(admin, True)
        return SimpleNamespace(answer="Prepared answer", error=None, media_url=None)
    from app import dependencies
    monkeypatch.setattr(dependencies, "get_rag_chain", lambda: SimpleNamespace(run=generate))
    monkeypatch.setattr(waha, "send_reply", lambda row: pytest.fail("Paused message was sent"))
    waha.process(row)
    assert store.get_inbox("controls-test", "inflight")["status"] == "skipped"


def test_control_writes_require_authentication_csrf_and_boolean(admin):
    assert admin.put("/admin/api/whatsapp/replies", json={"enabled": "false"}).status_code == 422
    admin.headers.pop("X-CSRF-Token")
    assert admin.put("/admin/api/whatsapp/replies", json={"enabled": False}).status_code == 403
    assert admin.post("/admin/api/whatsapp/attention/ignore", json={"items": []}).status_code == 403
    admin.cookies.clear()
    assert admin.put("/admin/api/whatsapp/replies", json={"enabled": False}).status_code == 401
    assert admin.post("/admin/api/whatsapp/attention/ignore", json={"items": []}).status_code == 401


def test_report_retry_updates_database_without_local_files(admin, monkeypatch):
    from testing.evals import runner
    result = {"id": "savedreport", "cases": []}
    store.create_job_row("savedreport", "evaluate", {})
    store.set_job_state("savedreport", "completed", result=result)
    monkeypatch.setattr(store, "data_path", lambda: pytest.fail("Read-only filesystem accessed"))
    monkeypatch.setattr(runner, "Client", lambda: SimpleNamespace())
    updated = runner.retry_report("savedreport")
    assert updated["reporting_error"] == "ValueError"
    assert store.evaluation_result("savedreport") == updated
