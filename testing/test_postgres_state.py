from app.admin import store
import pytest


def test_application_role_and_schema_are_private(pg_workspace):
    with pg_workspace.admin_connection() as db:
        assert (
            db.execute(
                "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='chatbot_app'"
            ).fetchone()[0]
            is False
        )
        for role in ("anon", "authenticated"):
            assert (
                db.execute(
                    "SELECT has_schema_privilege(%s,'chatbot','USAGE')", (role,)
                ).fetchone()[0]
                is False
            )
        assert (
            db.execute(
                "SELECT count(*) FROM pg_tables WHERE schemaname='chatbot' AND NOT rowsecurity"
            ).fetchone()[0]
            == 0
        )


def test_expired_session_is_not_extended(pg_live):
    store.create_session("old-token-hash", 1.0, "synthetic-csrf")
    assert store.get_session("old-token-hash", 2.0) is None


def test_reset_retains_audit_rows(pg_live):
    store.record_conversation("wa-test", "whatsapp", "question", "answer")
    assert store.clear_session("wa-test") is True
    assert store.prompt_turns("wa-test") == []
    assert len(store.conversations(channel="whatsapp")) == 1


def test_failed_publish_preserves_selection(pg_live):
    item = dict(
        id="original",
        namespace="original",
        status="ready",
        created_at=store.now(),
        manifest={},
        records=[],
        error=None,
    )
    store.save_version(item)
    store.publish("original")
    store.save_version(dict(item, id="draft", namespace="draft", status="draft"))
    with pytest.raises(ValueError):
        store.publish("draft")
    assert store.version()["id"] == "original"


def test_login_failure_limit_is_shared(pg_live):
    for i in range(10):
        store.record_login_failure("client-hash", 1000.0 + i)
    assert store.login_allowed("client-hash", 1011.0) is False
    assert store.login_allowed("client-hash", 1400.0) is True


def test_concurrent_publish_has_one_consistent_selection(pg_live):
    from concurrent.futures import ThreadPoolExecutor

    for name in ("a", "b"):
        store.save_version(
            dict(
                id=name,
                namespace=name,
                status="ready",
                created_at=store.now(),
                manifest={},
                records=[],
                error=None,
            )
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(store.publish, ["a", "b"]))
    assert sum(v["status"] == "published" for v in store.versions()) == 1
    assert store.version()["status"] == "published"


def test_password_hash_and_nonconsecutive_ids_survive(pg_live):
    salt = "ab" * 16
    digest = store.hash_password("test-only", salt)
    with pg_live.admin_connection() as db:
        db.execute("INSERT INTO chatbot.users VALUES(%s,%s,%s)", ("test", salt, digest))
        db.execute(
            "INSERT INTO chatbot.conversations(id,session_id,channel,question,answer) VALUES(41,'gap','api','q','a')"
        )
    assert store.get_user("test")["password_hash"] == digest
    store.clear_session("gap")
    assert store.prompt_turns("gap") == []
