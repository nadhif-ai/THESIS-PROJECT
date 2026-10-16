"""Pooler-compatible admin reads against a disposable PostgreSQL database."""

import hashlib
import json
import threading
import time

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin import store
from app.admin.routes import admin_router
from testing.test_admin_workflow import workspace


def test_authenticated_views_use_one_command_and_revoke_immediately(workspace, monkeypatch):
    from app.integrations import waha
    from app.main import admin_timing

    monkeypatch.setattr(waha, "api", lambda *args, **kwargs: {"status": "WORKING"})
    app = FastAPI()
    app.middleware("http")(admin_timing)
    app.include_router(admin_router)
    token = "synthetic-session"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    store.create_session(token_hash, time.time() + 60, "synthetic-csrf")
    executed = []
    original = psycopg.ClientCursor.execute

    def capture(cursor, command, *args, **kwargs):
        executed.append(command)
        return original(cursor, command, *args, **kwargs)

    monkeypatch.setattr(psycopg.ClientCursor, "execute", capture)
    with TestClient(app) as client:
        client.cookies.set("avg_admin", token)
        for path in ("me", "overview", "versions", "settings", "jobs", "conversations?channel=whatsapp", "whatsapp/status"):
            executed.clear()
            response = client.get("/admin/api/" + path)
            assert response.status_code == 200
            assert "db_acquire;dur=" in response.headers["Server-Timing"]
            assert "app;dur=" in response.headers["Server-Timing"]
            assert response.headers["Cache-Control"] == "private, no-store"
            commands = [query for query in executed if "valid_session" in str(query)]
            assert len(commands) == 1
            assert len(executed) == 1
        saved = client.put("/admin/api/settings", headers={"X-CSRF-Token": "synthetic-csrf"}, json={
            "openrouter_model": "synthetic/answer", "eval_model": "synthetic/judge", "semantic_top_k": 3,
        })
        assert saved.status_code == 200
        assert saved.json() == client.get("/admin/api/settings").json()
        store.delete_session(token_hash)
        assert client.get("/admin/api/versions").status_code == 401


def test_read_timeouts_and_connection_recovery(workspace, monkeypatch):
    store.create_session("session", time.time() + 60, "csrf")
    monkeypatch.setitem(store._ADMIN_READS, "timeouts", "jsonb_build_array(current_setting('statement_timeout'),current_setting('lock_timeout'))")
    assert store.admin_snapshot("session", time.time(), "timeouts")["data"] == ["30s", "5s"]
    monkeypatch.setitem(store._ADMIN_READS, "invalid", "(SELECT 'private-value'::integer)")
    with pytest.raises(store.StateUnavailable) as error:
        store.admin_snapshot("session", time.time(), "invalid")
    assert "private-value" not in str(error.value)
    assert store.admin_snapshot("session", time.time(), "me")["data"] == {}
    assert store.admin_snapshot("session", time.time() + 120, "versions") is None


def test_login_reports_phase_timings(workspace):
    app = FastAPI()
    app.include_router(admin_router)
    with TestClient(app) as client:
        response = client.post("/admin/api/login", json={
            "username": "admin", "password": "local-test-password",
        })
        assert response.status_code == 200
        for phase in ("db_login", "password", "db_session"):
            assert phase + ";dur=" in response.headers["Server-Timing"]


def test_metadata_backfill_is_idempotent_and_preserves_records(workspace, pg_live):
    records = [{"text": "synthetic", "metadata": {}}]
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.versions SET manifest=%s,records=%s WHERE id=%s", (
            json.dumps({"files": ["policy.txt"], "retained": True}), json.dumps(records), workspace["id"],
        ))
    assert store.backfill_version_counts() == 1
    assert store.backfill_version_counts() == 0
    item = store.version(workspace["id"])
    assert item["manifest"] == {"files": ["policy.txt"], "retained": True, "chunk_count": 1}
    assert item["records"] == records and item["namespace"] == workspace["namespace"]


def test_write_transaction_rolls_back_with_client_cursor(workspace):
    with pytest.raises(ValueError):
        with store._connection("administration") as db:
            db.execute("INSERT INTO chatbot.settings VALUES('rollback-check','true')")
            raise ValueError("synthetic failure")
    assert store.get_setting("rollback-check") is None


def test_admin_session_recovers_after_network_outage_fills_pool_queue(workspace, monkeypatch):
    from app.main import state_unavailable

    token = "outage-test-session"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    store.create_session(token_hash, time.time() + 60, "retained-csrf")
    store.close_pool()
    online = threading.Event()
    retry_exhausted = threading.Event()
    original_init = store.ConnectionPool.__init__
    original_connect = store.ConnectionPool._connect

    def test_pool(pool, *args, **kwargs):
        callback = kwargs.get("reconnect_failed")

        def exhausted(current):
            retry_exhausted.set()
            if callback:
                callback(current)

        kwargs.update(timeout=.05, max_waiting=2, reconnect_timeout=.1, reconnect_failed=exhausted)
        original_init(pool, *args, **kwargs)

    def connect(pool, *args, **kwargs):
        if not online.is_set():
            raise psycopg.OperationalError("Simulated network outage")
        return original_connect(pool, *args, **kwargs)

    monkeypatch.setattr(store.ConnectionPool, "__init__", test_pool)
    monkeypatch.setattr(store.ConnectionPool, "_connect", connect)
    app = FastAPI()
    app.include_router(admin_router)
    app.add_exception_handler(store.StateUnavailable, state_unavailable)
    with TestClient(app) as client:
        client.cookies.set("avg_admin", token)
        for _ in range(2):
            response = client.get("/admin/api/me")
            assert response.status_code == 503
            assert "postgresql" not in response.text
        assert retry_exhausted.wait(3), "Connection retry window did not expire"
        online.set()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            response = client.get("/admin/api/me")
            if response.status_code == 200:
                break
            time.sleep(.01)
        assert response.status_code == 200, store.pool_stats()
        assert response.json()["csrf"] == "retained-csrf"
        store.delete_session(token_hash)
        assert client.get("/admin/api/me").status_code == 401


def test_session_waits_for_a_healthy_cold_connection(workspace, monkeypatch):
    from app.main import state_unavailable

    token = "synthetic-cold-session"
    store.create_session(hashlib.sha256(token.encode()).hexdigest(), time.time() + 60, "csrf")
    store.close_pool()
    original_init = store.ConnectionPool.__init__
    original_connect = store.ConnectionPool._connect

    def scaled_pool(pool, *args, **kwargs):
        kwargs["timeout"] *= .01
        original_init(pool, *args, **kwargs)

    def cold_connect(pool, *args, **kwargs):
        # Scale an eight-second handshake below the two-address connect budget to 80 ms.
        time.sleep(.08)
        return original_connect(pool, *args, **kwargs)

    monkeypatch.setattr(store.ConnectionPool, "__init__", scaled_pool)
    monkeypatch.setattr(store.ConnectionPool, "_connect", cold_connect)
    app = FastAPI()
    app.include_router(admin_router)
    app.add_exception_handler(store.StateUnavailable, state_unavailable)
    with TestClient(app) as client:
        client.cookies.set("avg_admin", token)
        assert client.get("/admin/api/me").status_code == 200
