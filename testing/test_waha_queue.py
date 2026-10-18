"""Durable delivery invariants, using disposable PostgreSQL and mocked transports."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.admin import store
from app.integrations import waha, waha_queue
from testing.test_waha_integration import client, event, signed_post


def incoming(identifier, sender="123@lid"):
    store.enqueue_inbox("asia-chatbot", identifier, sender, "Synthetic question")


def test_unrelated_writes_share_maintenance_gate(pg_live):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with store._connection("execution"):
            pending = executor.submit(store.record_conversation, "other-chat", "whatsapp", "q", "a")
            pending.result(timeout=1)


def test_chat_order_and_owner_fencing(pg_live):
    incoming("first")
    incoming("second")
    assert store.claim_inbox("asia-chatbot", "second") is None
    first = store.claim_inbox("asia-chatbot", "first")
    assert first
    assert store.claim_inbox("asia-chatbot", "first") is None
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.whatsapp_inbox SET lease_expires_at=CURRENT_TIMESTAMP-interval '1 second' WHERE message_id='first'")
    replacement = store.claim_inbox("asia-chatbot", "first")
    assert replacement["lease_token"] != first["lease_token"]
    store.update_inbox("asia-chatbot", "first", {"answer": "Stale worker"}, first["lease_token"])
    assert store.get_inbox("asia-chatbot", "first")["answer"] is None
    assert not store.begin_inbox_send("asia-chatbot", "first", first["lease_token"])
    assert store.begin_inbox_send("asia-chatbot", "first", replacement["lease_token"])
    assert store.claim_inbox("asia-chatbot", "second") is None


def test_expired_send_becomes_uncertain_without_replay(pg_live):
    incoming("sending")
    claimed = store.claim_inbox("asia-chatbot", "sending")
    assert store.begin_inbox_send("asia-chatbot", "sending", claimed["lease_token"])
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.whatsapp_inbox SET lease_expires_at=CURRENT_TIMESTAMP-interval '1 second'")
    assert store.claim_inbox("asia-chatbot", "sending") is None
    assert store.get_inbox("asia-chatbot", "sending")["status"] == "uncertain"


def test_legacy_stalls_and_expired_queue_do_not_block_fresh_message(pg_live):
    incoming("legacy")
    incoming("old")
    incoming("fresh")
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.whatsapp_inbox SET status='generating',updated_at=(CURRENT_TIMESTAMP-interval '1 hour')::text WHERE message_id='legacy'")
        db.execute("UPDATE chatbot.whatsapp_inbox SET created_at=(CURRENT_TIMESTAMP-interval '1 hour')::text WHERE message_id='old'")
    assert store.claim_inbox("asia-chatbot", "fresh")["message_id"] == "fresh"
    assert store.get_inbox("asia-chatbot", "legacy")["status"] == "failed"
    assert store.get_inbox("asia-chatbot", "old")["status"] == "failed"


def test_consumer_deduplicates_delivery_without_local_worker(pg_live, monkeypatch):
    incoming("one")
    store.update_inbox("asia-chatbot", "one", {"answer": "Prepared answer"})
    sends = []
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: sends.append(args[1]) or {"id": "synthetic-reply"})
    payload = {"session": "asia-chatbot", "message_id": "one"}
    waha_queue.consume(payload)
    waha_queue.consume(payload)
    assert sends == ["/api/sendText"]
    result = store.get_inbox("asia-chatbot", "one")
    assert result["status"] == "sent"
    assert result["generation_started_at"] and result["sent_at"]


def test_queue_failure_retries_notification_for_existing_inbox(client, monkeypatch):
    monkeypatch.setattr(waha_queue, "enabled", lambda: True)
    calls = []
    async def unavailable(session, identifier):
        calls.append(identifier)
        raise RuntimeError("Synthetic queue outage")
    monkeypatch.setattr(waha_queue, "notify", unavailable)
    assert signed_post(client, event()).status_code == 503
    assert signed_post(client, event()).status_code == 503
    assert calls == ["test-message-1", "test-message-1"]
    assert store.get_inbox("asia-chatbot", "test-message-1")["status"] == "queued"


def test_vercel_lifespan_never_starts_polling_thread(monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_API_KEY", "test-only")
    monkeypatch.setenv("WAHA_WEBHOOK_SECRET", "test-only")
    get_settings.cache_clear()
    monkeypatch.setattr(waha, "initialize", lambda: pytest.fail("Started database polling on Vercel"))
    try:
        waha.start()
    finally:
        get_settings.cache_clear()


def test_out_of_order_queue_callbacks_retry_until_previous_reply_finishes(pg_live, monkeypatch):
    incoming("earlier")
    incoming("later")
    for identifier in ("earlier", "later"):
        store.update_inbox("asia-chatbot", identifier, {"answer": identifier})
    sends = []
    monkeypatch.setattr(waha, "api", lambda method, path, payload, **kwargs: sends.append(payload["text"]) or {"id": "reply-"+payload["text"]})
    with pytest.raises(RuntimeError, match="pending"):
        waha_queue.consume({"session": "asia-chatbot", "message_id": "later"})
    for identifier in ("earlier", "later"):
        waha_queue.consume({"session": "asia-chatbot", "message_id": identifier})
    assert sends == ["earlier", "later"]


def test_bot_off_never_publishes_a_reply_callback(client, monkeypatch):
    store.set_bot_replies(False)
    monkeypatch.setattr(waha_queue, "enabled", lambda: True)
    async def unexpected(*args):
        pytest.fail("Bot-off message published a reply callback")
    monkeypatch.setattr(waha_queue, "notify", unexpected)
    assert signed_post(client, event()).status_code == 200
    assert store.get_inbox("asia-chatbot", "test-message-1")["status"] == "skipped"
