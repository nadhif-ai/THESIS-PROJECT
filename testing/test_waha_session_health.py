"""Connection diagnostics replay the disconnected GOWS response from the incident."""

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
def session_client(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_SESSION", "asia-chatbot")
    monkeypatch.setenv("WAHA_API_KEY", "synthetic-api-key")
    monkeypatch.setenv("WAHA_WEBHOOK_SECRET", "synthetic-webhook-secret")
    monkeypatch.setenv("WAHA_WEBHOOK_URL", "https://callback.example.test/chat/waha/webhook")
    get_settings.cache_clear()
    recorded = []
    monkeypatch.setattr(store, "record_waha_session_event", lambda *args: recorded.append(args) or True, raising=False)
    monkeypatch.setattr(store, "enqueue_inbox", lambda *args: pytest.fail("A session event enqueued a customer reply"))
    app = FastAPI()
    app.include_router(waha.router)
    with TestClient(app) as client:
        yield client, recorded
    get_settings.cache_clear()


def signed_post(client, payload):
    raw = json.dumps(payload).encode()
    signature = hmac.new(b"synthetic-webhook-secret", raw, hashlib.sha512).hexdigest()
    return client.post("/chat/waha/webhook", content=raw, headers={
        "content-type": "application/json",
        "x-webhook-hmac": signature,
        "x-webhook-hmac-algorithm": "sha512",
    })


def session_event(status="FAILED", **changes):
    return {
        "event": "session.status", "session": "asia-chatbot", "timestamp": 1793880000000,
        "payload": {"status": status}, **changes,
    }


def test_disconnected_gows_is_diagnosed_even_when_gateway_and_grpc_are_ready(session_client, monkeypatch):
    # Redacted fields from GET /api/sessions/asia-chatbot on 2026-11-05.
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: {
        "name": "asia-chatbot", "status": "FAILED", "me": None,
        "engine": {"engine": "GOWS", "grpc": {"client": "READY", "stream": "READY"},
                   "gows": {"found": True, "connected": False}},
    })
    observed = waha.status(observations={})
    assert observed["session_status"] == "FAILED"
    assert observed["gateway_reachable"] is True
    assert observed["session_connected"] is False
    assert observed["session_ready"] is False
    assert "restart" in observed["session_hint"].lower()


def test_failure_event_preserves_safe_reason_without_logging_provider_payload(session_client, caplog):
    client, recorded = session_client
    event = session_event(payload={"status": "FAILED", "data": {"reason": {
        "event": "LoggedOut", "Reason": 401, "Message": "private-provider-detail",
        "Raw": {"token": "private-auth-token"},
    }}}, me={"id": "628111111111@c.us"})
    response = signed_post(client, event)
    assert response.status_code == 200
    assert response.json()["status"] == "session_status_recorded"
    assert recorded[0][0] == "asia-chatbot"
    saved = recorded[0][1]
    assert saved["status"] == "FAILED"
    assert saved["reason"] == "LoggedOut"
    assert saved["reason_code"] == 401
    assert saved["timestamp"] == event["timestamp"]
    assert "phase=session_status" in caplog.text
    assert "LoggedOut" in caplog.text
    for secret in ("private-provider-detail", "private-auth-token", "628111111111"):
        assert secret not in json.dumps(saved) + caplog.text + response.text


def test_session_events_require_hmac_and_the_configured_session(session_client):
    client, recorded = session_client
    assert client.post("/chat/waha/webhook", json=session_event()).status_code == 401
    response = signed_post(client, session_event(session="another-session"))
    assert response.json() == {"status": "ignored", "reason": "other_session"}
    assert not recorded


@pytest.mark.parametrize("payload", [None, [], {"status": "invented-state"}, {"status": []}])
def test_malformed_session_events_are_rejected(session_client, payload):
    client, recorded = session_client
    response = signed_post(client, session_event(payload=payload))
    assert response.status_code == 400
    assert not recorded


@pytest.mark.parametrize("timestamp", [True, -1, float("nan"), float("inf"), "not-a-timestamp"])
def test_invalid_event_timestamps_cannot_poison_durable_diagnostics(session_client, timestamp):
    client, recorded = session_client
    response = signed_post(client, session_event(timestamp=timestamp))
    assert response.status_code == 400
    assert not recorded


@pytest.mark.parametrize("response", [{}, [], {"status": "FAILED", "engine": None}, {"status": []}])
def test_bad_session_response_never_crashes_the_dashboard(session_client, monkeypatch, response):
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: response)
    observed = waha.status(observations={})
    assert observed["session_ready"] is False
    assert observed["session_status"] in ("FAILED", "unreachable")


def test_unknown_reason_is_not_persisted_or_logged_as_free_text(session_client, caplog):
    client, recorded = session_client
    response = signed_post(client, session_event(payload={
        "status": "FAILED", "data": {"reason": {"event": "private-provider-secret", "Reason": "private-code"}},
    }))
    assert response.status_code == 200
    assert recorded[0][1]["reason"] is None
    assert recorded[0][1]["reason_code"] is None
    assert "private-provider" not in caplog.text + json.dumps(recorded)


def test_missing_session_is_distinguished_from_an_unreachable_gateway(session_client, monkeypatch):
    def missing(*args, **kwargs):
        raise waha.WahaAPIError(404)
    monkeypatch.setattr(waha, "api", missing)
    observed = waha.status(observations={})
    assert observed["session_ready"] is False
    assert observed["gateway_reachable"] is True
    assert observed["gateway_http_status"] == 404
    assert "exact WAHA_SESSION name" in observed["session_hint"]


@pytest.mark.parametrize("callback_matches", [False, True])
def test_dashboard_checks_actual_signed_message_callbacks_not_just_env_vars(session_client, monkeypatch, callback_matches):
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: {
        "status": "WORKING", "engine": {"engine": "GOWS", "gows": {"connected": True}},
        "config": {"webhooks": [{
            "url": get_settings().waha_webhook_url if callback_matches else "https://example.test/sample-callback",
            "events": ["message", "message.ack", "session.status"],
            "hmac": {"key": get_settings().waha_webhook_secret},
        }]},
    })
    observed = waha.status(observations={})
    assert observed["credentials_configured"] is True
    assert observed["session_ready"] is True
    assert observed["webhook_configured"] is callback_matches
    assert observed["status_events_configured"] is callback_matches
    if not callback_matches:
        assert "Configure the production webhook" in observed["session_hint"]
