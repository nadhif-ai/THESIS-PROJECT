from app.admin import store
from app.backend.models import embedding_identity
from app.config.settings import get_settings
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
        manifest={"embedding": embedding_identity(), "vector_index": get_settings().pinecone_index_name},
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
                manifest={"embedding": embedding_identity(), "vector_index": get_settings().pinecone_index_name},
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


def test_only_one_caller_claims_one_message(pg_live):
    from concurrent.futures import ThreadPoolExecutor

    store.enqueue_inbox("asia-chatbot", "message-1", "123@lid", "question")
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(store.claim_inbox, ["asia-chatbot"] * 2))
    assert sum(row is not None for row in rows) == 1


def test_receipt_does_not_move_backwards(pg_live):
    store.record_ack("reply-1", 3)
    store.record_ack("reply-1", 1)
    with pg_live.admin_connection() as db:
        assert (
            db.execute(
                "SELECT ack FROM chatbot.whatsapp_receipts WHERE message_id='reply-1'"
            ).fetchone()[0]
            == 3
        )


def test_progress_merge_preserves_both_callers_fields(pg_live):
    from concurrent.futures import ThreadPoolExecutor

    store.create_job_row("progress-1", "evaluate", {})
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(
            pool.map(
                lambda fields: store.merge_job_progress("progress-1", fields),
                [{"completed": 1}, {"total": 3}],
            )
        )
    progress = store.list_job_rows()[0]["progress"]
    assert progress["completed"] == 1 and progress["total"] == 3


def test_conflicting_duplicate_and_unknown_fields_are_rejected(pg_live):
    store.enqueue_inbox("s", "id", "123@lid", "body")
    with pytest.raises(ValueError):
        store.enqueue_inbox("s", "id", "123@lid", "different")
    with pytest.raises(ValueError):
        store.update_inbox("s", "id", {"session": "other"})
