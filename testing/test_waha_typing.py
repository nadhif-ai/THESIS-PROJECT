"""Presence checks use mocked WAHA calls and never contact a customer."""

from types import SimpleNamespace

import pytest
import requests

from app.integrations import waha


ROW = {"session": "test-session", "sender": "123@lid"}


@pytest.mark.parametrize("enabled", [True, False])
def test_typing_wraps_processing_without_extra_delay(monkeypatch, enabled):
    calls = []
    monkeypatch.setattr(waha, "get_settings", lambda: SimpleNamespace(waha_typing_enabled=enabled))
    monkeypatch.setattr(waha, "api", lambda method, path, payload, **kwargs: calls.append(path))
    with waha.typing_indicator(ROW):
        calls.append("processing")
    assert calls == (["/api/startTyping", "processing", "/api/stopTyping"] if enabled else ["processing"])


def test_typing_is_cleared_if_generation_fails(monkeypatch):
    calls = []
    monkeypatch.setattr(waha, "get_settings", lambda: SimpleNamespace(waha_typing_enabled=True))
    monkeypatch.setattr(waha, "api", lambda method, path, payload, **kwargs: calls.append(path))
    with pytest.raises(RuntimeError, match="Synthetic generation failure"):
        with waha.typing_indicator(ROW):
            raise RuntimeError("Synthetic generation failure")
    assert calls == ["/api/startTyping", "/api/stopTyping"]


def test_presence_failure_does_not_block_answer_processing(monkeypatch):
    calls = []
    monkeypatch.setattr(waha, "get_settings", lambda: SimpleNamespace(waha_typing_enabled=True))
    def unavailable(method, path, payload, **kwargs):
        assert payload == {"session": "test-session", "chatId": "123@lid"}
        assert kwargs["timeout"] == 3
        calls.append(path)
        raise requests.Timeout()
    monkeypatch.setattr(waha, "api", unavailable)
    with waha.typing_indicator(ROW):
        calls.append("answer still processed")
    assert calls == ["/api/startTyping", "answer still processed", "/api/stopTyping"]


def test_empty_presence_response_is_accepted(monkeypatch):
    monkeypatch.setattr(waha, "get_settings", lambda: SimpleNamespace(
        waha_base_url="https://waha.example.test", waha_api_key="test-only",
    ))
    monkeypatch.setattr(waha.requests, "request", lambda *args, **kwargs: SimpleNamespace(ok=True, content=b""))
    assert waha.api("POST", "/api/startTyping", ROW) == {}
