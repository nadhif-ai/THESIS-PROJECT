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
            embed_documents=lambda texts: [[0.1] * 384 for _ in texts]
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
        lambda: SimpleNamespace(embed_query=lambda text: [0.1] * 384),
    )
    results = vectorstore.similarity_search_with_score(
        "What file?",
        k=3,
        namespace="draft-only",
        filter_dict={"intent_type": "FAQ", "format": "txt"},
    )
    assert results[0][1] == pytest.approx(0.18)
    assert results[0][0].metadata["cosine_similarity"] == 0.82
    assert calls[0]["namespace"] == "draft-only"
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
