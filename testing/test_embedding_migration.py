from types import SimpleNamespace
import json

import pytest

from app.admin import store
from scripts import migrate_embeddings
from testing.test_admin_workflow import workspace


def test_remote_vectors_live_in_pinecone_not_postgres_snapshots(workspace):
    item = store.version()
    item["records"] = [{"id": "remote", "document": "A passage", "metadata": {}, "embedding": [0.1] * 2048}]
    store.save_version(item)
    assert store.version()["records"] == [{"id": "remote", "document": "A passage", "metadata": {}}]


def test_all_version_migration_preserves_sources_chunks_draft_and_resume(workspace, monkeypatch, tmp_path):
    from app.admin import knowledge

    source = store.version()
    source["manifest"]["embedding"] = {"model": "intfloat/multilingual-e5-small", "dimensions": 384}
    source["manifest"]["vector_index"] = "chatbot-avg"
    source["records"] = [{"id": "frozen-chunk", "document": "Frozen original passage.",
                          "metadata": {"source": "policy.txt"}, "embedding": [0.1] * 384}]
    store.save_version(source)
    draft = knowledge.new_draft(source["id"])
    calls, upserts = [], []
    def embed(texts):
        calls.extend(texts)
        return [[0.1] * 2048 for _ in texts]
    monkeypatch.setattr(migrate_embeddings, "root", lambda: tmp_path / "migration")
    monkeypatch.setattr(migrate_embeddings, "get_embedding_model", lambda: SimpleNamespace(embed_documents=embed))
    monkeypatch.setattr(migrate_embeddings, "ingest_records", lambda rows, namespace: upserts.append((rows, namespace)))
    ledger = migrate_embeddings.prepare()
    assert len(ledger["versions"]) == 2
    targets = {e["source"]: store.version(e["target"]) for e in ledger["versions"]}
    assert targets[source["id"]]["status"] == "ready"
    assert targets[draft["id"]]["status"] == "draft"
    assert targets[source["id"]]["records"][0]["document"] == "Frozen original passage."
    assert all(len(r["embedding"]) == 2048 for rows, _ in upserts for r in rows)
    assert store.get_setting("published_version") == source["id"]
    assert store.version(source["id"])["records"][0]["embedding"] == [0.1] * 384
    assert len(calls) == 2
    migrate_embeddings.prepare()
    assert len(calls) == 2 and len(upserts) == 2
    with pytest.raises(ValueError, match="historical E5"):
        store.publish(source["id"])


def test_evaluation_uses_one_frozen_configuration(workspace, monkeypatch, tmp_path):
    from app.backend import chain
    from testing.evals import runner

    directory = tmp_path / "migration"
    frozen = {"openrouter_model": "frozen-answer", "eval_model": "frozen-judge", "semantic_top_k": 7}
    ledger = {"evaluation_configuration": frozen, "versions": [
        {"target": f"target-{i}", "source_status": "ready", "prepared": True} for i in range(2)
    ]}
    migrate_embeddings.save(directory / "migration.json", ledger)
    monkeypatch.setattr(migrate_embeddings, "root", lambda: directory)
    monkeypatch.setattr(chain, "RAGChain", lambda: SimpleNamespace())
    observed = []
    def evaluate(**kwargs):
        observed.append(kwargs["configuration"])
        return {"cases": [], "averages": {}}
    monkeypatch.setattr(runner, "run_evaluation", evaluate)
    migrate_embeddings.evaluate()
    assert observed == [frozen, frozen]
    assert len(json.loads((directory / "migration.json").read_text())["versions"]) == 2
    migrate_embeddings.evaluate()
    assert len(observed) == 2


def test_activation_requires_maintenance_and_keeps_archive(workspace, pg_live, monkeypatch, tmp_path):
    source = store.version()
    target = dict(source, id="nemotron-replacement", status="ready", namespace="nemotron-replacement")
    store.save_version(target)
    directory = tmp_path / "migration"
    migrate_embeddings.save(directory / "migration.json", {
        "source_published": source["id"], "versions": [{"source": source["id"],
            "target": target["id"], "source_status": "published", "prepared": True, "evaluation_id": "evaluated"}]
    })
    monkeypatch.setattr(migrate_embeddings, "root", lambda: directory)
    monkeypatch.setattr(store, "job", lambda identifier: {"status": "completed", "result": {
        "cases": [{"metrics": [{"score": 0.9}] * 5}] * 10}})
    with pytest.raises(ValueError, match="intake maintenance"):
        migrate_embeddings.activate()
    assert store.get_setting("published_version") == source["id"]
    with pg_live.admin_connection() as db:
        db.execute("UPDATE chatbot.runtime_control SET mode='intake' WHERE id=1")
    migrate_embeddings.activate()
    assert store.version_info()["id"] == target["id"]
    assert store.version_info(source["id"])["status"] == "ready"
    assert store.version_info(source["id"])["manifest"]["archived"] is True


def test_archived_draft_requires_a_new_copy_to_edit(workspace):
    from app.admin import knowledge
    draft = knowledge.new_draft()
    draft["manifest"]["archived"] = True
    store.save_version(draft)
    with pytest.raises(ValueError, match="read-only"):
        knowledge.save_file(draft["id"], "policy.txt", b"replacement")
    copy = knowledge.new_draft(draft["id"])
    knowledge.save_file(copy["id"], "policy.txt", b"Editable copy")
    assert not copy["manifest"].get("archived")


def test_evaluation_reloads_job_reservations_between_versions(workspace, monkeypatch, tmp_path):
    from app.backend import chain
    from testing.evals import runner
    directory = tmp_path / "migration"
    path = directory / "migration.json"
    migrate_embeddings.save(path, {"evaluation_configuration": {}, "versions": [
        {"target": f"target-{i}", "source_status": "ready", "prepared": True} for i in range(2)]})
    monkeypatch.setattr(migrate_embeddings, "root", lambda: directory)
    monkeypatch.setattr(chain, "RAGChain", lambda: SimpleNamespace())
    calls = []
    def evaluate(**kwargs):
        calls.append(kwargs["version_id"])
        store.create_job_row("other-operator", "evaluate", {})
        store.set_job_state("other-operator", "completed", result={"cases": []})
        ledger = json.loads(path.read_text())
        ledger["versions"][1]["evaluation_id"] = "other-operator"
        migrate_embeddings.save(path, ledger)
        return {"cases": []}
    monkeypatch.setattr(runner, "run_evaluation", evaluate)
    migrate_embeddings.evaluate()
    assert calls == ["target-0"]
    assert json.loads(path.read_text())["versions"][1]["evaluation_id"] == "other-operator"
