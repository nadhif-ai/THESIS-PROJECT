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


@pytest.fixture(autouse=True)
def offline_boundary(monkeypatch, request):
    if os.getenv("RUN_PAID_EVALS") == "1" and request.node.path.parent.name == "evals":
        yield
        return
    from app.admin import store
    from app.backend import product_intent, attachment_answer
    monkeypatch.setattr(product_intent, 'extract', lambda *a, **kw: product_intent.ProductIntent(action='none', product_ids=[], view='hero', attributes=[], exact_visual=False, resolution='resolved', clarification='', changes_product=False))
    monkeypatch.setattr(attachment_answer, 'consistent', lambda *a, **kw: True)
    from app.config.settings import get_settings
    from psycopg.conninfo import conninfo_to_dict

    store.close_pool()
    for name, value in {
        "DATABASE_URL": LOCAL_ADMIN.replace("/postgres?", "/fixture_required?"),
        "DATABASE_MIGRATION_URL": LOCAL_ADMIN,
        "OPENROUTER_API_KEY": "offline-test-key",
        "OPENAI_API_KEY": "offline-test-key",
        "OPENAI_ENDPOINT": "",
        "PINECONE_API_KEY": "",
        "SUPABASE_SECRET_KEY": "",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "LANGSMITH_API_KEY": "",
        "LANGSMITH_TRACING": "false",
        "VERCEL": "0",
    }.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    real_pool = store.ConnectionPool

    class LocalTestPool(real_pool):
        def __init__(self, conninfo, **kwargs):
            options = conninfo_to_dict(conninfo)
            if options.get("host") not in (
                "127.0.0.1",
                "localhost",
                "::1",
            ) or not options.get("dbname", "").startswith("chatbot_test_"):
                raise ValueError(
                    "Offline database tests require the disposable pg_workspace fixture."
                )
            super().__init__(conninfo, **kwargs)

    monkeypatch.setattr(store, "ConnectionPool", LocalTestPool)
    real_connect = psycopg.connect

    def local_connect(conninfo="", **kwargs):
        options = conninfo_to_dict(conninfo)
        if kwargs.get("host", options.get("host")) not in (
            "127.0.0.1",
            "localhost",
            "::1",
        ):
            raise psycopg.OperationalError(
                "Offline tests prohibit external PostgreSQL connections."
            )
        return real_connect(conninfo, **kwargs)

    monkeypatch.setattr(psycopg, "connect", local_connect)
    yield
    store.close_pool()
    get_settings.cache_clear()


@pytest.fixture
def pg_workspace(tmp_path, monkeypatch):
    name = "chatbot_test_" + uuid.uuid4().hex
    with psycopg.connect(LOCAL_ADMIN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    admin_dsn = LOCAL_ADMIN.replace("/postgres?", f"/{name}?")
    runtime_dsn = admin_dsn.replace("//postgres@", "//chatbot_app@")
    with psycopg.connect(admin_dsn) as db:
        for role in ("anon", "authenticated"):
            if not db.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
            ).fetchone():
                db.execute(
                    sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role))
                )
        files = sorted((ROOT / "supabase/migrations").glob("*.sql"))
        assert files, "PostgreSQL administration schema has not been implemented"
        for path in files:
            db.execute(path.read_text())
    monkeypatch.setenv("DATABASE_URL", runtime_dsn)
    monkeypatch.setenv("DATABASE_MIGRATION_URL", admin_dsn)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "2048")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "chatbot-nadhif")
    monkeypatch.setenv("ADMIN_PASSWORD", "local-test-password")
    monkeypatch.setenv("WAHA_TYPING_ENABLED", "false")
    monkeypatch.setenv("VERCEL", "0")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    yield SimpleNamespace(
        admin_dsn=admin_dsn,
        runtime_dsn=runtime_dsn,
        root=tmp_path,
        admin_connection=lambda: psycopg.connect(admin_dsn),
    )
    from app.admin import store

    if hasattr(store, "close_pool"):
        store.close_pool()
    get_settings.cache_clear()
    with psycopg.connect(LOCAL_ADMIN, autocommit=True) as db:
        db.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
        )


@pytest.fixture
def pg_live(pg_workspace):
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.runtime_control SET mode='live' WHERE id=1")
    from app.admin import store

    store.open_pool()
    return pg_workspace
