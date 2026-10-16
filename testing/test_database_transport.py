"""Real PostgreSQL traffic with an isolated proxy that can drop response packets."""

import hashlib
import select
import socket
import socketserver
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import psycopg
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from app.admin import store
from app.admin.routes import admin_router
from app.config.settings import get_settings
from testing.test_admin_workflow import workspace


@pytest.fixture
def database_proxy(pg_live, monkeypatch):
    blocked = threading.Event()
    sockets = []

    class Relay(socketserver.BaseRequestHandler):
        def handle(self):
            with socket.create_connection(("127.0.0.1", 54585)) as upstream:
                sockets.extend((self.request, upstream))
                try:
                    while True:
                        ready, _, _ = select.select((self.request, upstream), (), (), .05)
                        for source in ready:
                            data = source.recv(65536)
                            if not data:
                                return
                            if not blocked.is_set():
                                (upstream if source is self.request else self.request).sendall(data)
                except OSError:
                    return

    def disconnect():
        for connection in sockets[:]:
            try:
                connection.shutdown(socket.SHUT_RDWR)
                connection.close()
            except OSError:
                pass

    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Relay)
    server.daemon_threads = True
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.05), daemon=True)
    thread.start()
    store.close_pool()
    monkeypatch.setenv("DATABASE_URL", make_conninfo(pg_live.runtime_dsn, port=server.server_address[1]))
    get_settings.cache_clear()
    try:
        yield SimpleNamespace(blocked=blocked, disconnect=disconnect)
    finally:
        disconnect()
        store.close_pool()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        get_settings.cache_clear()


@pytest.mark.parametrize("io_timeout", [.15, None], ids=["fast", "production-deadline"])
def test_session_releases_blackholed_connection_and_recovers(workspace, database_proxy, monkeypatch, io_timeout):
    from app.main import state_unavailable

    if io_timeout is not None:
        monkeypatch.setattr(store, "_IO_TIMEOUT", io_timeout)
    token = "synthetic-transport-session"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    store.create_session(token_hash, time.time() + 60, "retained-csrf")
    app = FastAPI()
    app.include_router(admin_router)
    app.add_exception_handler(store.StateUnavailable, state_unavailable)
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as executor:
        client.cookies.set("avg_admin", token)
        assert client.get("/admin/api/me").status_code == 200
        database_proxy.blocked.set()
        pending = executor.submit(client.get, "/admin/api/me")
        try:
            response = pending.result(timeout=(io_timeout or 35) + 1)
            assert response.status_code == 503
        finally:
            database_proxy.blocked.clear()
            database_proxy.disconnect()
        assert client.get("/admin/api/me").status_code == 200
        store.delete_session(token_hash)
        assert client.get("/admin/api/me").status_code == 401


def test_abandoned_transactions_have_a_server_deadline(workspace):
    with store._connection("administration") as db:
        assert db.execute("SHOW idle_in_transaction_session_timeout").fetchone()["idle_in_transaction_session_timeout"] == "35s"


def test_server_releases_an_abandoned_maintenance_lock(workspace, pg_live, monkeypatch):
    monkeypatch.setattr(store, "_TRANSACTION_SETUP", store._TRANSACTION_SETUP.replace("'35s'", "'100ms'"))
    acquired = False
    with pytest.raises(store.StateUnavailable):
        with store._connection("administration"):
            with psycopg.connect(pg_live.runtime_dsn) as contender:
                contender.execute("SET LOCAL lock_timeout='1s'")
                row = contender.execute("SELECT id FROM chatbot.runtime_control WHERE id=1 FOR UPDATE").fetchone()
                acquired = row[0] == 1
    assert acquired, "An abandoned connection kept the shared maintenance lock"
