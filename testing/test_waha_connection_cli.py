"""Operator recovery cannot log out a phone or repeatedly restart a healthy session."""

from copy import deepcopy
import json

import pytest
import requests

from app.config.settings import get_settings
from app.integrations import waha
from scripts import waha_connection as connection


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PROVIDER", "waha")
    monkeypatch.setenv("WAHA_SESSION", "asia-chatbot")
    monkeypatch.setenv("WAHA_WEBHOOK_URL", "https://callback.example.test/chat/waha/webhook")
    monkeypatch.setenv("WAHA_WEBHOOK_SECRET", "synthetic-hmac-key")
    get_settings.cache_clear()


@pytest.mark.parametrize("status", ["WORKING", "STARTING", "SCAN_QR_CODE", "PASSKEY_REQUIRED"])
def test_restart_does_not_interrupt_pairing_or_a_running_session(monkeypatch, status):
    calls = []
    def api(method, path, *args, **kwargs):
        calls.append((method, path))
        return {"status": status}
    monkeypatch.setattr(waha, "api", api)
    assert connection.restart_session()["status"] == status
    assert calls == [("GET", "/api/sessions/asia-chatbot")]


def test_failed_session_is_restarted_once_then_reports_pairing(monkeypatch, capsys):
    states = iter(["FAILED", "SCAN_QR_CODE"])
    calls = []
    def api(method, path, *args, **kwargs):
        calls.append((method, path))
        return {"status": next(states)} if method == "GET" else {}
    monkeypatch.setattr(waha, "api", api)
    assert connection.main(["restart"]) == 3
    assert calls == [("GET", "/api/sessions/asia-chatbot"), ("POST", "/api/sessions/asia-chatbot/restart"), ("GET", "/api/sessions/asia-chatbot")]
    assert json.loads(capsys.readouterr().out)["session_status"] == "SCAN_QR_CODE"


def test_subscribing_preserves_private_configuration_and_other_webhooks(monkeypatch):
    original = {"status": "WORKING", "config": {
        "metadata": {"retained": "synthetic"}, "proxy": {"password": "synthetic-proxy-secret"},
        "webhooks": [{"url": "https://callback.example.test/chat/waha/webhook", "events": ["message", "message.ack"],
                      "hmac": {"key": "synthetic-hmac-key"}, "retries": {"policy": "constant", "attempts": 5}},
                     {"url": "https://another.example.test/hook", "events": ["message"]}],
    }}
    calls = []
    updated = deepcopy(original)
    def api(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        if method == "PUT":
            updated["config"] = payload["config"]
        return deepcopy(updated)
    monkeypatch.setattr(waha, "api", api)
    result = connection.configure_webhook()
    expected = deepcopy(original["config"])
    expected["webhooks"][0]["events"].append("session.status")
    assert result["config"] == expected
    assert original["config"]["webhooks"][0]["events"] == ["message", "message.ack"]
    assert sum(method == "PUT" for method, *_ in calls) == 1
    calls.clear()
    connection.configure_webhook()
    assert all(method == "GET" for method, *_ in calls)


def test_configuration_mismatch_cannot_overwrite_another_apps_webhook(monkeypatch):
    def api(method, *args, **kwargs):
        assert method == "GET"
        return {"status": "WORKING", "config": {"webhooks": [{"url": "https://another.example.test"}]}}
    monkeypatch.setattr(waha, "api", api)
    with pytest.raises(ValueError):
        connection.configure_webhook()


def test_recreated_session_gets_signed_production_callbacks_without_losing_engine_config(monkeypatch):
    session = {"status": "WORKING", "config": {"gows": {"retained": True}, "webhooks": []}}
    calls = []
    def api(method, path, payload=None, **kwargs):
        calls.append(method)
        if method == "PUT":
            session["config"] = payload["config"]
        return deepcopy(session)
    monkeypatch.setattr(waha, "api", api)
    configured = connection.configure_webhook()
    assert configured["config"]["gows"] == {"retained": True}
    hook = configured["config"]["webhooks"][0]
    assert hook["url"] == get_settings().waha_webhook_url
    assert hook["events"] == ["message", "message.ack", "session.status"]
    assert hook["hmac"] == {"key": get_settings().waha_webhook_secret}
    assert hook["retries"] == {"policy": "constant", "delaySeconds": 2, "attempts": 5}
    assert calls == ["GET", "PUT", "GET"]


def test_check_uses_session_readiness_instead_of_server_health(monkeypatch, capsys):
    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: {"status": "FAILED", "engine": {"engine": "GOWS", "gows": {"connected": False}}})
    assert connection.main(["check"]) == 1
    assert json.loads(capsys.readouterr().out)["gateway_reachable"] is True


def test_connection_error_output_never_contains_private_url_or_key(monkeypatch, capsys):
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("https://private.example?api_key=private-key")
    monkeypatch.setattr(waha, "api", unavailable)
    assert connection.main(["check"]) == 1
    output = capsys.readouterr().out
    assert "ConnectionError" in output
    assert "private" not in output
