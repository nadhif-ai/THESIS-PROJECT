"""Boundary checks that do not call providers or modify the business dataset."""

from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.admin import store, knowledge
from app.admin.routes import admin_router


@pytest.fixture
def workspace(tmp_path, monkeypatch, pg_live):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ADMIN_PASSWORD", "local-test-password")
    get_settings.cache_clear()
    with pg_live.admin_connection() as db:
        db.execute("INSERT INTO chatbot.users VALUES(%s,%s,%s)", ("admin", "00"*16, store.hash_password("local-test-password", "00"*16)))
    item = {
        "id": "original",
        "namespace": "original-only",
        "status": "ready",
        "created_at": store.now(),
        "manifest": {"files": ["policy.txt"]},
        "records": [],
        "error": None,
    }
    from app.backend.models import embedding_identity
    item["manifest"].update(embedding=embedding_identity(), vector_index=get_settings().pinecone_index_name)
    knowledge.path_for(item).mkdir(parents=True)
    (knowledge.path_for(item) / "policy.txt").write_text(
        "Files should be supplied as print-ready PDF."
    )
    store.save_version(item)
    store.publish(item["id"])
    yield item
    get_settings.cache_clear()


def test_api_authentication_and_csrf(workspace):
    app = FastAPI()
    app.include_router(admin_router)
    with TestClient(app) as client:
        assert client.get("/admin/api/settings").status_code == 401
        assert client.get("/admin/api/conversations").status_code == 401
        login = client.post(
            "/admin/api/login",
            json={"username": "admin", "password": "local-test-password"},
        )
        assert login.status_code == 200
        assert client.get("/admin/api/settings").status_code == 200
        assert client.post("/admin/api/versions", json={}).status_code == 403
        token = login.json()["csrf"]
        assert (
            client.post(
                "/admin/api/versions",
                json={},
                headers={"x-csrf-token": token, "origin": "https://untrusted.example"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/admin/api/versions", json={}, headers={"x-csrf-token": token}
            ).status_code
            == 200
        )
        assert all(
            isinstance(value, bool)
            for value in client.get("/admin/api/settings").json()["providers"].values()
        )
        assert client.get("/admin/api/file/policy.txt").status_code == 404


def test_draft_failure_cannot_change_published_knowledge(workspace, monkeypatch):
    draft = knowledge.new_draft()
    knowledge.save_file(draft["id"], "policy.txt", b"Updated print-ready PDF guidance.")
    assert (
        knowledge.path_for(store.version()) / "policy.txt"
    ).read_text() == "Files should be supplied as print-ready PDF."
    with pytest.raises(ValueError):
        store.publish(draft["id"])

    def failure(records, namespace):
        raise TimeoutError("Indexing not ready")

    monkeypatch.setattr(
        knowledge,
        "get_embedding_model",
        lambda: SimpleNamespace(
            embed_documents=lambda texts: [[0.1] * 2048 for _ in texts]
        ),
    )
    monkeypatch.setattr(knowledge, "ingest_records", failure)
    with pytest.raises(TimeoutError):
        knowledge.index_version(draft["id"])
    assert store.version()["id"] == "original"
    failed_namespace = store.version(draft["id"])["namespace"]
    monkeypatch.setattr(
        knowledge, "ingest_records", lambda records, namespace: len(records)
    )
    knowledge.index_version(draft["id"])
    assert store.version(draft["id"])["namespace"] != failed_namespace
    store.publish(draft["id"])
    assert store.version()["id"] == draft["id"]


def test_dashboard_summaries_and_lazy_results(workspace, monkeypatch):
    store.record_conversation("synthetic", "whatsapp", "question", "answer", latency=2)
    store.create_job_row("saved", "evaluate", {})
    result = {"id": "syntheticevaluation", "cases": [], "reporting_error": "offline"}
    store.set_job_state("saved", "completed", result=result)
    store.save_evaluation_result(result["id"], result | {
        "reporting_error": None, "experiment_url": "https://example.test/report",
    })
    def read_only():
        raise PermissionError("Read-only deployment filesystem")
    monkeypatch.setattr(store, "data_path", read_only)

    app = FastAPI()
    app.include_router(admin_router)
    with TestClient(app) as client:
        assert client.get("/admin/api/jobs/saved").status_code == 401
        login = client.post("/admin/api/login", json={
            "username": "admin", "password": "local-test-password",
        })
        assert login.status_code == 200
        catalog = client.get("/admin/api/versions").json()
        version = next(v for v in catalog["versions"] if v["id"] == workspace["id"])
        assert "records" not in version and version["chunk_count"] == 0
        assert catalog["published"] == workspace["id"]

        job = client.get("/admin/api/jobs").json()[0]
        assert "result" not in job
        assert job["has_result"] is True and job["result_case_count"] == 0
        detail = client.get("/admin/api/jobs/saved").json()["result"]
        assert detail["cases"] == [] and detail["reporting_error"] is None
        assert detail["experiment_url"] == "https://example.test/report"
        exported = client.get(f"/admin/api/evaluations/{result['id']}/export")
        assert exported.status_code == 200 and exported.json() == detail
        assert client.get("/admin/api/jobs/missing").status_code == 404

        overview = client.get("/admin/api/overview").json()
        assert overview["conversations"] == overview["whatsapp_messages"] == 1
        assert overview["average_latency"] == 2
        assert "result" not in overview["jobs"][0]
        assert "records" not in overview["published"]


@pytest.mark.parametrize(
    "name",
    [
        "../outside.txt",
        "nested/file.txt",
        "..\\outside.txt",
        ".hidden.txt",
        "file.exe",
        "",
    ],
)
def test_upload_paths_are_rejected(workspace, name):
    with pytest.raises(ValueError):
        knowledge.valid_name(name)


def test_pinecone_scores_filters_and_namespace(workspace, monkeypatch):
    from app.backend import vectorstore

    calls = []

    def query(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            matches=[
                SimpleNamespace(
                    id="chunk-1",
                    score=0.82,
                    metadata={"source": "policy.txt", "text": "Print-ready PDF"},
                )
            ]
        )

    monkeypatch.setattr(
        vectorstore, "get_vectorstore", lambda: SimpleNamespace(query=query)
    )
    monkeypatch.setattr(
        vectorstore,
        "get_embedding_model",
        lambda: SimpleNamespace(embed_query=lambda text: [0.1] * 2048),
    )
    results = vectorstore.similarity_search_with_score(
        "What file?",
        k=3,
        namespace=workspace["namespace"],
        filter_dict={"intent_type": "FAQ", "format": "txt"},
    )
    assert results[0][1] == pytest.approx(0.18)
    assert results[0][0].metadata["cosine_similarity"] == 0.82
    assert calls[0]["namespace"] == workspace["namespace"]
    assert calls[0]["filter"] == {
        "$and": [{"intent_type": {"$eq": "FAQ"}}, {"format": {"$eq": "txt"}}]
    }


def test_metric_names_and_failures_remain_distinct(workspace):
    from testing.evals.runner import _metric_results

    class Metric:
        __name__ = "Faithfulness"
        threshold = 0.7

        def measure(self, case):
            self.score = 0.9
            self.reason = "Grounded"

        def is_successful(self):
            return True

    class Failed(Metric):
        def measure(self, case):
            raise ValueError("Missing context")

    rows = _metric_results(None, [Metric(), Failed()])
    assert rows[0]["name"] == "Faithfulness"
    assert rows[0]["score"] == 0.9
    assert rows[1]["score"] is None and rows[1]["passed"] is None


def test_reset_keeps_audit_history_but_clears_prompt(workspace):
    store.record_conversation("playground-test", "playground", "Question", "Answer")
    assert store.prompt_turns("playground-test")
    store.clear_session("playground-test")
    assert store.prompt_turns("playground-test") == []
    assert store.conversations("playground")


def test_menu_uses_selected_knowledge_version(workspace, monkeypatch):
    from app.backend import chain as chain_module

    monkeypatch.setattr(chain_module, "get_llm", lambda: SimpleNamespace())
    draft = knowledge.new_draft()
    knowledge.save_file(
        draft["id"],
        "05_daftar_pertanyaan_populer.txt",
        b"[KATEGORI_1]\nDraft material question\n[KATEGORI_2]\nFile question\n",
    )
    response = chain_module.RAGChain().run(
        "1", "menu-test", namespace=draft["namespace"], channel="playground"
    )
    assert "Draft material question" in response.answer
    assert store.version()["id"] == "original"


@pytest.mark.parametrize("output", ["", "  ", None])
def test_empty_provider_answer_is_not_saved_as_a_success(workspace, monkeypatch, output):
    from app.backend import chain as chain_module, vectorstore
    from langchain_core.documents import Document
    monkeypatch.setattr(chain_module, "get_llm", lambda *args: SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=output)))
    monkeypatch.setattr(vectorstore, "similarity_search_with_score", lambda **kwargs: [(Document(page_content="Print-ready PDF", metadata={"source": "policy.txt"}), 0.1)])
    response = chain_module.RAGChain().run("What file should I send?", "empty-output", channel="playground")
    assert response.error and response.answer.strip()
    assert not store.conversations("playground")


def test_playground_and_whatsapp_do_not_download_embedding_snapshots(workspace, monkeypatch):
    import psycopg
    from app import dependencies
    from app.backend import chain as chain_module
    from app.integrations import waha
    from app.main import state_unavailable

    monkeypatch.setattr(chain_module, "get_llm", lambda *args: SimpleNamespace())
    rag = chain_module.RAGChain()
    monkeypatch.setattr(dependencies, "get_rag_chain", lambda: rag)
    app = FastAPI()
    app.include_router(admin_router)
    app.add_exception_handler(store.StateUnavailable, state_unavailable)
    execute = psycopg.ClientCursor.execute

    def limited_transfer(cursor, query, *args, **kwargs):
        # Reproduce the slow snapshot transfer without a real network outage.
        if "SELECT * FROM chatbot.versions" in str(query):
            raise psycopg.OperationalError("Embedding snapshot transfer timed out")
        return execute(cursor, query, *args, **kwargs)

    with TestClient(app) as client:
        login = client.post("/admin/api/login", json={
            "username": "admin", "password": "local-test-password",
        })
        monkeypatch.setattr(psycopg.ClientCursor, "execute", limited_transfer)
        response = client.post("/admin/api/playground", json={
            "question": "Hi admin", "session_id": "snapshot-regression",
        }, headers={"X-CSRF-Token": login.json()["csrf"]})
        assert response.status_code == 200
        assert response.json()["answer_source"] == "Greeting"

        sent = []
        monkeypatch.setattr(waha, "api", lambda *args, **kwargs: sent.append(args) or {"id": "synthetic-reply"})
        store.enqueue_inbox("synthetic", "greeting", "123@lid", "Hi admin")
        row = store.claim_inbox("synthetic")
        waha.process(dict(row))
        assert store.get_inbox("synthetic", "greeting")["status"] == "sent"
        assert len(sent) == 1 and sent[0][1] == "/api/sendText"


def test_version_info_selects_only_the_requested_metadata(workspace):
    published = store.version_info()
    assert published["id"] == "original" and "records" not in published
    assert published == store.version_info("original")
    assert published == store.version_info(namespace="original-only")
    assert published["manifest"]["files"] == ["policy.txt"]
    with pytest.raises(ValueError, match="not found"):
        store.version_info(namespace="original-only' OR true --")
    assert store.version()["records"] == []


def test_public_api_sessions_cannot_read_or_reset_whatsapp(workspace, monkeypatch):
    import app.routes as routes

    seen = []

    def run(**kwargs):
        seen.append(kwargs["session_id"])
        return SimpleNamespace(
            answer="Test reply", media_url=None, sources=[], usage={}
        )

    monkeypatch.setattr(routes, "_get_rag_chain", lambda: SimpleNamespace(run=run))
    store.record_conversation(
        "wa_123", "whatsapp", "Private question", "Private answer"
    )
    app = FastAPI()
    app.include_router(routes.chat_router)
    with TestClient(app) as client:
        assert (
            client.post(
                "/chat/faq", json={"session_id": "wa_123", "question": "Question"}
            ).status_code
            == 200
        )
        assert seen == ["api_wa_123"]
        assert (
            client.post("/chat/reset", json={"session_id": "wa_123"}).status_code == 200
        )
        assert store.prompt_turns("wa_123") == [("Private question", "Private answer")]
