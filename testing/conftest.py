"""Disposable PostgreSQL databases; never use the configured production DSN."""

import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import psycopg
from psycopg import sql
import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ADMIN = "postgresql://postgres@127.0.0.1:54585/postgres?sslmode=disable"


@pytest.fixture
def pg_workspace(tmp_path, monkeypatch):
    name = "chatbot_test_" + uuid.uuid4().hex
    with psycopg.connect(LOCAL_ADMIN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    admin_dsn = LOCAL_ADMIN.replace("/postgres?", f"/{name}?")
    runtime_dsn = admin_dsn.replace("//postgres@", "//chatbot_app@")
    with psycopg.connect(admin_dsn) as db:
        for role in ("anon", "authenticated"):
            if not db.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                db.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
        files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
        assert files, "PostgreSQL administration schema has not been implemented"
        for path in files:
            db.execute(path.read_text())
    monkeypatch.setenv("DATABASE_URL", runtime_dsn)
    monkeypatch.setenv("DATABASE_MIGRATION_URL", admin_dsn)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ADMIN_PASSWORD", "local-test-password")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    yield SimpleNamespace(
        admin_dsn=admin_dsn, runtime_dsn=runtime_dsn, root=tmp_path,
        admin_connection=lambda: psycopg.connect(admin_dsn),
    )
    from app.admin import store

    if hasattr(store, "close_pool"):
        store.close_pool()
    get_settings.cache_clear()
    with psycopg.connect(LOCAL_ADMIN, autocommit=True) as db:
        db.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
