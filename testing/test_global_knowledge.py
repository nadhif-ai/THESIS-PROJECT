import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.admin import global_knowledge as kb, kb_store, store, durable_jobs
from app.backend.models import embedding_identity


def add_source(
    name="policy.txt", text="Alamat toko ada di Jalan Contoh. Jam buka pukul 08.00."
):
    identifier = kb_store.stage_upload(name, len(text.encode()))
    source_id = kb_store.finish_upload(
        identifier, hashlib.sha256(text.encode()).hexdigest(), [{"text": text}]
    )
    return source_id, identifier


def seed_active(identifier="original", empty=False):
    from app.config.settings import get_settings

    store.save_version(
        {
            "id": identifier,
            "namespace": "kb-" + identifier,
            "status": "ready",
            "created_at": store.now(),
            "manifest": {
                "files": ["policy.txt"] if not empty else [],
                "chunking": {"chunk_size": 1000, "chunk_overlap": 100},
                "embedding": embedding_identity(),
                "vector_index": get_settings().pinecone_index_name,
                "empty": empty,
            },
            "records": []
            if empty
            else [
                {
                    "id": "first",
                    "document": "Test policy",
                    "metadata": {"source": "policy.txt"},
                }
            ],
        }
    )
    store.publish(identifier)


class Index:
    def __init__(self):
        self.values = {}
        self.deleted = []

    def upsert(self, namespace, vectors, **kwargs):
        self.values.setdefault(namespace, {}).update({r["id"]: r for r in vectors})

    def list(self, namespace, **kwargs):
        return [list(self.values.get(namespace, {}))]

    def list_paginated(self, namespace, **kwargs):
        return SimpleNamespace(
            vectors=[SimpleNamespace(id=i) for i in self.values.get(namespace, {})],
            pagination=None,
        )

    def query(self, **kwargs):
        return SimpleNamespace(matches=[SimpleNamespace(id="test")])

    def delete(self, namespace, **kwargs):
        self.deleted.append(namespace)


@pytest.fixture
def providers(monkeypatch):
    index = Index()
    monkeypatch.setattr(kb, "get_vectorstore", lambda: index)
    monkeypatch.setattr(
        kb,
        "get_embedding_model",
        lambda: SimpleNamespace(
            embed_documents=lambda texts: [[1.0] * 2048 for t in texts],
            embed_query=lambda text: [1.0] * 2048,
        ),
    )
    return index


def drain(identifier, maximum=100):
    for _ in range(maximum):
        row = kb_store.work(identifier)
        if not durable_jobs.consume(identifier, row["sequence"]):
            return
    pytest.fail("Job did not finish in bounded steps")


def test_configuration_is_staged_and_sync_activates_atomically(pg_live, providers):
    seed_active()
    source_id, blob_id = add_source()
    assert kb_store.catalog()["pending"]
    job = kb_store.start_sync()
    for _ in range(3):
        row = kb_store.work(job)
        durable_jobs.consume(job, row["sequence"])
        assert store.version_info()["id"] == "original"
    with pytest.raises(ValueError, match="locked"):
        kb_store.change_source(source_id, enabled=False)
    drain(job)
    active = store.version_info()
    assert active["id"] == "kb-" + job
    assert active["manifest"]["source_refs"][0]["blob_id"] == blob_id
    assert not kb_store.catalog()["pending"]
    assert kb_store.catalog()["sync_job"] is None
    assert kb_store.work(job)["status"] == "completed"


def test_sync_refuses_embedding_index_drift(pg_live, providers, monkeypatch):
    from app.config.settings import get_settings

    seed_active()
    add_source()
    job = kb_store.start_sync()
    assert durable_jobs.consume(job, 0)
    monkeypatch.setenv("PINECONE_INDEX_NAME", "different-index")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="changed"):
        durable_jobs.consume(job, 1)
    assert store.version_info()["id"] == "original"


def test_cleanup_retries_storage_failure_without_reopening_the_blob(
    pg_live, providers, monkeypatch
):
    identifier = kb_store.stage_upload("orphan.txt", 4)
    with pg_live.admin_connection() as db:
        db.execute(
            "UPDATE chatbot.knowledge_blobs SET created_at=now()-interval '2 days' WHERE id=%s",
            (identifier,),
        )

    def interrupted(path):
        raise RuntimeError("Synthetic storage interruption")

    monkeypatch.setattr(kb.source_storage, "remove", interrupted)
    with pytest.raises(RuntimeError):
        kb.cleanup()
    with pytest.raises(ValueError, match="not found"):
        kb_store.blob(identifier)
    removed = []
    monkeypatch.setattr(kb.source_storage, "remove", removed.append)
    kb.cleanup()
    assert len(removed) == 1
    with pg_live.admin_connection() as db:
        row = db.execute(
            "SELECT removed_at,pages FROM chatbot.knowledge_blobs WHERE id=%s",
            (identifier,),
        ).fetchone()
    assert row[0] is not None and row[1] is None


def test_cleanup_rechecks_a_blob_registered_after_candidate_selection(pg_live):
    identifier = kb_store.stage_upload("late.txt", 4)
    kb_store.finish_upload(identifier, "synthetic-sha", [{"text": "Late"}])
    assert not kb_store.claim_blob_deletion(identifier)
    assert kb_store.blob(identifier)["removed_at"] is None


@pytest.mark.parametrize("message", ["Namespace not found", "Index not found"])
def test_cleanup_only_accepts_an_already_missing_namespace(monkeypatch, message):
    from pinecone.exceptions import NotFoundException

    error = NotFoundException(status=404, reason="Not Found")
    error.body = json.dumps({"code": 5, "message": message})

    def missing(**kwargs):
        raise error

    finished = []
    monkeypatch.setattr(kb, "get_vectorstore", lambda: SimpleNamespace(delete=missing))
    monkeypatch.setattr(
        kb_store,
        "garbage_candidates",
        lambda _: ([{"id": "old-empty", "namespace": "kb-old-empty"}], []),
    )
    monkeypatch.setattr(kb_store, "finish_deletion", lambda **kw: finished.append(kw))
    if message == "Namespace not found":
        assert kb.cleanup()
        assert finished == [{"snapshot_id": "old-empty"}]
    else:
        with pytest.raises(NotFoundException):
            kb.cleanup()
        assert not finished


def test_failed_sync_keeps_active_and_can_resume_without_reembedding(
    pg_live, providers, monkeypatch
):
    seed_active()
    add_source()
    job = kb_store.start_sync()
    durable_jobs.consume(job, 0)
    durable_jobs.consume(job, 1)
    original = providers.list_paginated
    providers.list_paginated = lambda **kw: SimpleNamespace(vectors=[], pagination=None)
    for _ in range(3):
        with pytest.raises(RuntimeError, match="visible"):
            durable_jobs.consume(job, 2)
    assert kb_store.work(job)["status"] == "failed"
    assert store.version_info()["id"] == "original"
    assert kb_store.catalog()["sync_job"] is None
    providers.list_paginated = original
    monkeypatch.setattr(
        kb,
        "get_embedding_model",
        lambda: SimpleNamespace(
            embed_query=lambda text: [1.0] * 2048,
            embed_documents=lambda texts: pytest.fail(
                "Completed embedding batch repeated"
            ),
        ),
    )
    kb_store.retry(job)
    drain(job)
    assert store.version_info()["id"] == "kb-" + job


def test_changed_configuration_prevents_resuming_old_failed_sync(pg_live):
    add_source()
    job = kb_store.start_sync()
    for _ in range(3):
        row = kb_store.claim(job, 0)
        kb_store.release_error(job, row["lease_token"], "failed")
    kb_store.configure({"chunk_size": 800, "chunk_overlap": 80})
    with pytest.raises(ValueError, match="changed"):
        kb_store.retry(job)


def test_source_replacement_toggle_delete_and_duplicate_validation(pg_live):
    source, blob_id = add_source()
    duplicate = kb_store.stage_upload("other.txt", 4)
    with pytest.raises(ValueError, match="identical"):
        kb_store.finish_upload(
            duplicate, kb_store.blob(blob_id)["sha256"], [{"text": "test"}]
        )
    replacement = kb_store.stage_upload("replacement.txt", 7, source)
    kb_store.finish_upload(replacement, "new-sha", [{"text": "Updated"}], source)
    assert kb_store.source(source)["id"] == replacement
    kb_store.change_source(source, enabled=False)
    assert kb_store.source(source)["enabled"] is False
    kb_store.change_source(source, delete=True)
    assert kb_store.catalog()["sources"] == []
    assert kb_store.blob(blob_id)["removed_at"] is None


def test_empty_sync_and_empty_reply_do_not_call_provider(
    pg_live, providers, monkeypatch
):
    from app.backend.chain import RAGChain

    seed_active()
    source, _ = add_source()
    kb_store.change_source(source, enabled=False)
    drain(kb_store.start_sync())
    assert store.version_info()["manifest"]["empty"] is True
    rag = RAGChain()
    monkeypatch.setattr(
        kb, "get_embedding_model", lambda: pytest.fail("Empty KB embedded a query")
    )
    for question in ("Harga stiker berapa?", "2"):
        answer = rag.run(question, "empty-test", langsmith_extra={"enabled": False})
        assert answer.answer == kb.EMPTY_ANSWER
        assert answer.error is None
    assert (
        rag.run("hi", "empty-test", langsmith_extra={"enabled": False}).answer_source
        == "Greeting"
    )
    assert (
        rag.run("reset", "empty-test", langsmith_extra={"enabled": False}).answer_source
        == "Reset"
    )
    with pytest.raises(ValueError, match="searchable"):
        kb_store.create_evaluation({"dataset": "legacy"}, {})
    store.check_ready()


def test_evaluation_pins_snapshot_while_sync_is_allowed(pg_live, providers):
    seed_active()
    add_source()
    identifier = kb_store.create_evaluation(
        {"dataset": "legacy"}, {"rows": [{"id": "a"}], "configuration": {}}
    )
    drain(kb_store.start_sync())
    row = kb_store.work(identifier)
    assert json.loads(row["payload"])["version_id"] == "original"
    assert row["checkpoint"]["snapshot"]["namespace"] == "kb-original"
    assert store.version_info()["id"] != "original"


def test_lease_is_exclusive_stale_completion_rejected_and_redelivery_safe(
    pg_live, providers
):
    add_source()
    identifier = kb_store.start_sync()
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: kb_store.claim(identifier, 0), range(2)))
    assert sum(c is not None for c in claims) == 1
    owner = next(c for c in claims if c)
    with pg_live.admin_connection() as db:
        db.execute(
            "UPDATE chatbot.admin_work SET lease_until=now()-interval '1 second' WHERE job_id=%s",
            (identifier,),
        )
    replacement = kb_store.claim(identifier, 0)
    with pytest.raises(RuntimeError, match="lease expired"):
        kb_store.checkpoint(identifier, owner["lease_token"], {}, {})
    kb_store.release_error(identifier, replacement["lease_token"], "retry")
    assert durable_jobs.consume(identifier, 0)
    before = kb_store.work(identifier)["sequence"]
    assert durable_jobs.consume(identifier, 0)
    assert kb_store.work(identifier)["sequence"] == before


@pytest.mark.parametrize(
    "name",
    ["../a.txt", "a.csv", "a.md", ".hidden.pdf", "a\x00.txt", "a/b.pdf", "a\\b.txt"],
)
def test_reject_unsafe_and_unsupported_files(name):
    with pytest.raises(ValueError):
        kb.valid_name(name)


def test_extract_txt_and_reject_empty_binary_and_scanned_pdf():
    assert (
        kb.extract(b"\xef\xbb\xbfHarga stiker 35 pcs", "policy.txt")[0]["text"]
        == "Harga stiker 35 pcs"
    )
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    out = io.BytesIO()
    writer.write(out)
    for content, name in [
        (b"", "a.txt"),
        (b"\xff", "a.txt"),
        (b"a\x00b", "a.txt"),
        (b"fake pdf", "a.pdf"),
        (out.getvalue(), "scan.pdf"),
    ]:
        with pytest.raises((ValueError, UnicodeDecodeError)):
            kb.extract(content, name)


def test_private_storage_urls_require_admin_and_csrf(pg_live, monkeypatch):
    from app.main import app

    source, _ = add_source()
    monkeypatch.setattr(
        kb.source_storage, "signed_download", lambda p: "https://storage.invalid/scoped"
    )
    client = TestClient(app)
    assert (
        client.get(f"/admin/api/knowledge/sources/{source}/preview").status_code == 401
    )
    salt = "00" * 16
    with pg_live.admin_connection() as db:
        db.execute(
            "INSERT INTO chatbot.users VALUES(%s,%s,%s)",
            ("admin", salt, store.hash_password("local-test-password", salt)),
        )
    login = client.post(
        "/admin/api/login",
        json={"username": "admin", "password": "local-test-password"},
    )
    assert login.status_code == 200
    assert (
        client.patch(
            f"/admin/api/knowledge/sources/{source}", json={"enabled": False}
        ).status_code
        == 403
    )
    preview = client.get(f"/admin/api/knowledge/sources/{source}/preview")
    assert preview.status_code == 200
    assert preview.json()["url"] == "https://storage.invalid/scoped"
    assert "secret" not in json.dumps(preview.json()).lower()
    assert (
        client.post(
            "/admin/api/playground",
            headers={"x-csrf-token": login.json()["csrf"]},
            json={"question": "hi", "session_id": "x", "version_id": "old"},
        ).status_code
        == 422
    )


def test_cleanup_preserves_current_inactive_sources_and_pinned_evaluations(
    pg_live, providers, monkeypatch
):
    seed_active()
    source, blob_id = add_source()
    evaluation = kb_store.create_evaluation({"dataset": "legacy"}, {})
    drain(kb_store.start_sync())
    with pg_live.admin_connection() as db:
        db.execute(
            "UPDATE chatbot.versions SET retired_at=now()-interval '2 days' WHERE id='original'"
        )
        db.execute(
            "UPDATE chatbot.knowledge_blobs SET created_at=now()-interval '2 days'"
        )
    removed = []
    monkeypatch.setattr(kb.source_storage, "remove", removed.append)
    kb.cleanup()
    assert "kb-original" not in providers.deleted
    kb_store.change_source(source, enabled=False)
    drain(kb_store.start_sync())
    kb.cleanup()
    assert not removed
    with pg_live.admin_connection() as db:
        db.execute(
            "UPDATE chatbot.jobs SET status='completed' WHERE id=%s", (evaluation,)
        )
    kb.cleanup()
    assert "kb-original" in providers.deleted
    assert kb_store.blob(blob_id)["removed_at"] is None
