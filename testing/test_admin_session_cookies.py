"""Session cookie migration checks without database or provider requests."""

import hashlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin import store
from app.admin.routes import admin_router


@pytest.mark.parametrize("port", [8000, 5173])
def test_login_replaces_legacy_root_cookie(monkeypatch, port):
    sessions = {}
    salt = "00" * 16
    user = {"salt": salt, "password_hash": store.hash_password("test-password", salt)}
    monkeypatch.setattr(store, "login_candidate", lambda *args: (True, user))

    def create_session(token_hash, expires, csrf, client_hash):
        sessions[token_hash] = {"csrf": csrf, "data": {}, "timing": {}}

    monkeypatch.setattr(store, "create_session", create_session)
    monkeypatch.setattr(
        store, "admin_snapshot", lambda token_hash, *args, **kwargs: sessions.get(token_hash)
    )
    app = FastAPI()
    app.include_router(admin_router)
    with TestClient(app, base_url=f"http://127.0.0.1:{port}") as client:
        client.cookies.set("avg_admin", "stale-root-session", domain="127.0.0.1", path="/")
        login = client.post(
            "/admin/api/login", json={"username": "admin", "password": "test-password"}
        )
        assert login.status_code == 200
        response = client.get("/admin/api/me")
        assert response.status_code == 200
        assert response.json()["csrf"] == login.json()["csrf"]
        cookies = [cookie for cookie in client.cookies.jar if cookie.name == "avg_admin"]
        assert [cookie.path for cookie in cookies] == ["/admin"]
        assert hashlib.sha256(cookies[0].value.encode()).hexdigest() in sessions
