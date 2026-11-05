"""Session observations survive cold starts and tolerate webhook redelivery."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.admin import store
from testing.test_waha_integration import client, signed_post


def event(timestamp, status="FAILED"):
    return {"timestamp": timestamp, "status": status, "reason": "LoggedOut" if status == "FAILED" else None,
            "reason_code": 401 if status == "FAILED" else None, "received_at": store.now()}


def test_session_reason_survives_pool_restart_and_is_scoped_to_session(pg_live):
    failed = event(10)
    assert store.record_waha_session_event("asia-chatbot", failed)
    store.close_pool()
    data = store.whatsapp_observations("asia-chatbot")
    assert data["last_session_event"] == failed
    assert data["last_session_failure"] == failed
    assert store.whatsapp_observations("another-session")["last_session_event"] is None


def test_out_of_order_and_duplicate_callbacks_cannot_replace_current_state(pg_live):
    failed = event(10)
    working = event(20, "WORKING")
    assert store.record_waha_session_event("asia-chatbot", failed)
    assert store.record_waha_session_event("asia-chatbot", working)
    assert not store.record_waha_session_event("asia-chatbot", failed)
    assert not store.record_waha_session_event("asia-chatbot", working)
    observed = store.whatsapp_observations("asia-chatbot")
    assert observed["last_session_event"] == working
    assert observed["last_session_failure"] == failed


def test_concurrent_callback_order_keeps_newest_state(pg_live):
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda at: store.record_waha_session_event("asia-chatbot", event(at)), [30, 10, 40, 20]))
    assert store.whatsapp_observations("asia-chatbot")["last_session_event"]["timestamp"] == 40


def test_session_diagnostics_follow_the_intake_maintenance_boundary(pg_workspace):
    with pytest.raises(store.MaintenanceError):
        store.record_waha_session_event("asia-chatbot", event(10))
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.runtime_control SET mode='intake' WHERE id=1")
    assert store.record_waha_session_event("asia-chatbot", event(10))


def test_signed_callback_reaches_durable_diagnostics_without_enqueuing_a_reply(client, caplog):
    callback = {
        "event": "session.status", "session": "asia-chatbot", "timestamp": 1793880000000,
        "payload": {"status": "FAILED", "data": {"reason": {"event": "ClientOutdated", "Reason": 405}}},
    }
    for _ in range(2):
        response = signed_post(client, callback)
        assert response.status_code == 200
        assert response.json() == {"status": "session_status_recorded"}
    store.close_pool()
    observed = store.whatsapp_observations("asia-chatbot")
    assert observed["last_session_event"]["reason"] == "ClientOutdated"
    assert observed["last_session_failure"]["reason_code"] == 405
    assert observed["queue"] == {}
    assert caplog.text.count("phase=session_status") == 1
