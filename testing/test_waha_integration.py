"""Offline verification of webhook authentication, deduplication and delivery fallback."""

import hashlib
import hmac
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin import store
from app.config.settings import get_settings
from app.integrations import waha


@pytest.fixture
def client(tmp_path, monkeypatch, pg_live):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ADMIN_PASSWORD", "test-only")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_SESSION", "asia-chatbot")
    monkeypatch.setenv("WAHA_WEBHOOK_SECRET", "test-webhook-secret")
    get_settings.cache_clear()
    waha.initialize()
    app = FastAPI()
    app.include_router(waha.router)
    with TestClient(app) as instance:
        instance.pg = pg_live
        yield instance
    get_settings.cache_clear()


def event(**changes):
    payload = {
        "id": "test-message-1",
        "from": "628111111111@c.us",
        "fromMe": False,
        "body": "Min, format file cetak apa?",
    }
    payload.update(changes)
    return {"event": "message", "session": "asia-chatbot", "payload": payload}


def signed_post(client, data):
    raw = json.dumps(data, ensure_ascii=False).encode()
    digest = hmac.new(b"test-webhook-secret", raw, hashlib.sha512).hexdigest()
    return client.post(
        "/chat/waha/webhook",
        content=raw,
        headers={
            "content-type": "application/json",
            "x-webhook-hmac": digest,
            "x-webhook-hmac-algorithm": "sha512",
        },
    )


def test_unsigned_requests_cannot_enqueue(client):
    assert client.post("/chat/waha/webhook", json=event()).status_code == 401
    with client.pg.admin_connection() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM chatbot.whatsapp_inbox").fetchone()[0] == 0
        )


def test_signed_retry_is_deduplicated_and_lid_is_preserved(client):
    incoming = event(**{"from": "123456789@lid"})
    assert signed_post(client, incoming).json()["status"] == "queued"
    assert signed_post(client, incoming).json()["status"] == "duplicate"
    with client.pg.admin_connection() as db:
        rows = db.execute("SELECT * FROM chatbot.whatsapp_inbox").fetchall()
        assert len(rows) == 1 and rows[0][2] == "123456789@lid"


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"fromMe": True}, "from_me"),
        ({"from": "12345@g.us"}, "not_a_private_chat"),
        ({"body": ""}, "no_text"),
    ],
)
def test_non_customer_events_are_ignored(client, changes, reason):
    assert signed_post(client, event(**changes)).json()["reason"] == reason


def test_ack_events_never_enqueue_answers(client):
    data = {
        "event": "message.ack",
        "session": "asia-chatbot",
        "payload": {"id": "reply-1", "ack": 2},
    }
    assert signed_post(client, data).json()["status"] == "ack_recorded"
    with client.pg.admin_connection() as db:
        assert (
            db.execute("SELECT ack FROM chatbot.whatsapp_receipts").fetchone()[0] == 2
        )
        assert (
            db.execute("SELECT COUNT(*) FROM chatbot.whatsapp_inbox").fetchone()[0] == 0
        )


def test_failed_image_still_sends_text(client, monkeypatch):
    signed_post(client, event())
    calls = []

    def api(method, path, payload, **kwargs):
        calls.append((path, payload))
        if path == "/api/sendImage":
            raise ValueError("WAHA returned HTTP 422.")
        return {"id": "reply-1"}

    monkeypatch.setattr(waha, "api", api)
    with client.pg.admin_connection() as db:
        row = store.get_inbox("asia-chatbot", "test-message-1")
    row.update(answer="File PDF Print.", media_url="https://example.com/sample.png")
    waha.send_reply(row)
    assert [path for path, _ in calls] == ["/api/sendImage", "/api/sendText"]
    assert calls[0][1]["file"]["mimetype"] == "image/png"
    assert calls[1][1]["chatId"] == row["sender"]
    with client.pg.admin_connection() as db:
        assert (
            db.execute("SELECT status FROM chatbot.whatsapp_inbox").fetchone()[0]
            == "sent"
        )


def test_startup_does_not_mutate_inflight_delivery(client):
    signed_post(client, event())
    with client.pg.admin_connection() as db:
        db.execute("UPDATE chatbot.whatsapp_inbox SET status='sending'")
    waha.initialize()
    with client.pg.admin_connection() as db:
        assert (
            db.execute("SELECT status FROM chatbot.whatsapp_inbox").fetchone()[0]
            == "sending"
        )


def test_image_timeout_retains_uncertainty_after_text_success(client,monkeypatch):
    import requests
    signed_post(client,event())
    row=store.get_inbox('asia-chatbot','test-message-1')
    row.update(answer='Prepared answer.',media_url='https://example.com/image.png')
    calls=[]
    def api(method,path,payload,**kwargs):
        calls.append(path)
        if path=='/api/sendImage': raise requests.Timeout()
        return {'id':'known-text-reply'}
    monkeypatch.setattr(waha,'api',api)
    waha.send_reply(row)
    persisted=store.get_inbox('asia-chatbot','test-message-1')
    assert persisted['status']=='uncertain'
    assert json.loads(persisted['reply_ids'])==['known-text-reply']
    assert calls==['/api/sendImage','/api/sendText']


def test_missing_send_response_identity_is_uncertain(client,monkeypatch):
    signed_post(client,event())
    store.update_inbox('asia-chatbot','test-message-1',{'answer':'Prepared answer.'})
    row=store.claim_inbox('asia-chatbot')
    monkeypatch.setattr(waha,'api',lambda *a,**k:{})
    waha.process(row)
    assert store.get_inbox('asia-chatbot','test-message-1')['status']=='uncertain'
