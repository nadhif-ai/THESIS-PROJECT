"""Prepare and evaluate Nemotron versions, then explicitly activate during maintenance."""

import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

from app.admin import store, knowledge
from app.admin.chunking import Chunking, token_statistics
from app.backend.models import NEMOTRON, embedding_identity, get_embedding_model
from app.backend.vectorstore import ingest_records, require_compatible_version
from app.config.settings import get_settings
from langchain_core.documents import Document


def configure():
    os.environ.update(EMBEDDING_MODEL=NEMOTRON, EMBEDDING_DIMENSIONS="2048",
                      PINECONE_INDEX_NAME="chatbot-nadhif")
    get_settings.cache_clear()
    get_embedding_model.cache_clear()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    temporary = path.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, ensure_ascii=False)
    os.replace(temporary, path)


def root():
    return store.data_path() / "migrations" / "nemotron-20261016"


def prepare():
    ledger_path = root() / "migration.json"
    cache_path = root() / "passage-cache.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
    else:
        with store._connection() as db:
            rows = db.execute("SELECT id,status FROM chatbot.versions ORDER BY created_at,id").fetchall()
        ledger = {"embedding": embedding_identity(), "index": get_settings().pinecone_index_name,
                  "source_published": store.get_setting("published_version"),
                  "versions": [{"source": row["id"], "source_status": row["status"],
                      "target": "nemotron-" + hashlib.sha256(row["id"].encode()).hexdigest()[:12]}
                      for row in rows]}
        save(ledger_path, ledger)
    if ledger["embedding"] != embedding_identity() or ledger["index"] != get_settings().pinecone_index_name:
        raise ValueError("Migration checkpoint belongs to another embedding configuration.")
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for entry in ledger["versions"]:
        if entry.get("prepared"):
            require_compatible_version(store.version_info(entry["target"]))
            continue
        source_path = root() / (entry["source"] + ".json")
        if source_path.exists():
            source = json.loads(source_path.read_text())
        else:
            source = store.version(entry["source"])
            save(source_path, source)
        target = dict(source, id=entry["target"], namespace="avg-" + entry["target"],
                      status="draft", created_at=store.now(), error=None)
        target["manifest"] = dict(source["manifest"], migrated_from=source["id"],
            source_status=entry["source_status"], embedding=embedding_identity(),
            vector_index=get_settings().pinecone_index_name)
        shutil.copytree(knowledge.path_for(source), knowledge.path_for(target), dirs_exist_ok=True)
        if entry["source_status"] in ("ready", "published"):
            records = [dict(r, embedding=None) for r in source["records"]]
        else:
            config = Chunking(**source["manifest"].get("chunking", {}))
            records = []
            for name in source["manifest"]["files"]:
                if name == "05_daftar_pertanyaan_populer.txt":
                    continue
                for i, doc in enumerate(knowledge.draft_documents(knowledge.path_for(source) / name, config)):
                    identifier = hashlib.sha256((name + "\0" + str(i) + "\0" + doc.page_content).encode()).hexdigest()
                    records.append({"id": identifier, "document": doc.page_content,
                                    "metadata": doc.metadata, "embedding": None})
            target["manifest"]["chunking"] = dict(config.model_dump(), preprocessing="sections-v1")
        if not records:
            raise ValueError("Migration source contains no searchable passages.")
        for start in range(0, len(records), 32):
            batch = records[start:start + 32]
            missing = {hashlib.sha256(r["document"].encode()).hexdigest(): r["document"]
                       for r in batch if hashlib.sha256(r["document"].encode()).hexdigest() not in cache}
            if missing:
                vectors = get_embedding_model().embed_documents(list(missing.values()))
                if len(vectors) != len(missing):
                    raise ValueError("Incomplete embedding batch.")
                cache.update(zip(missing, vectors))
                save(cache_path, cache)
            for record in batch:
                record["embedding"] = cache[hashlib.sha256(record["document"].encode()).hexdigest()]
            print(json.dumps({"phase": "embedding", "version": entry["target"],
                              "completed": min(start + 32, len(records)), "total": len(records)}), flush=True)
        ingest_records(records, target["namespace"])
        target["records"] = records
        target["manifest"]["index_statistics"] = token_statistics([Document(page_content=r["document"]) for r in records])
        target["status"] = "ready" if entry["source_status"] in ("ready", "published") else "draft"
        store.save_version(target)
        entry.update(prepared=True, chunks=len(records), namespace=target["namespace"])
        save(ledger_path, ledger)
        print(json.dumps({"phase": "prepared", "version": target["id"], "chunks": len(records), "status": target["status"]}), flush=True)
    assert store.get_setting("published_version") == ledger["source_published"], "Published selection changed during preparation"
    return ledger


def evaluate():
    from app import dependencies
    from app.backend.chain import RAGChain
    from testing.evals.runner import run_evaluation

    ledger_path = root() / "migration.json"
    ledger = json.loads(ledger_path.read_text())
    if not all(entry.get("prepared") for entry in ledger["versions"]):
        raise ValueError("Prepare all versions before evaluating.")
    if "evaluation_configuration" not in ledger:
        settings = get_settings()
        ledger["evaluation_configuration"] = store.get_settings_values({
            "openrouter_model": settings.openrouter_model,
            "eval_model": settings.eval_model,
            "semantic_top_k": settings.semantic_top_k,
        })
        save(ledger_path, ledger)
    dependencies._rag_chain = RAGChain()
    for selected in ledger["versions"]:
        # Another operator may have registered the next job during a long evaluation.
        ledger = json.loads(ledger_path.read_text())
        entry = next(e for e in ledger["versions"] if e["target"] == selected["target"])
        if entry["source_status"] not in ("ready", "published"):
            continue
        if not entry.get("prepared"):
            raise ValueError("Prepare every indexed version before evaluating.")
        job_id = entry.get("evaluation_id")
        if job_id and store.job(job_id)["status"] == "completed":
            continue
        if job_id:
            raise ValueError("An evaluation attempt already exists; inspect its partial result before retrying paid work.")
        job_id = uuid.uuid4().hex
        entry["evaluation_id"] = job_id
        save(ledger_path, ledger)
        payload = {"version_id": entry["target"], "dataset": "legacy", "limit": 10}
        store.create_job_row(job_id, "evaluate", payload)
        store.set_job_state(job_id, "running")
        print(json.dumps({"phase": "evaluating", "version": entry["target"], "job_id": job_id}), flush=True)
        try:
            result = run_evaluation(job_id=job_id, configuration=ledger["evaluation_configuration"], **payload)
            store.set_job_state(job_id, "completed", result=result)
            store.merge_job_progress(job_id, {"phase": "completed", "completed": len(result["cases"])})
        except Exception as error:
            store.set_job_state(job_id, "failed", error=type(error).__name__ + ": inspect the private migration log.")
            raise
        print(json.dumps({"phase": "evaluated", "version": entry["target"], "cases": len(result["cases"]),
                          "averages": result.get("averages"), "errors": sum(bool(c.get("error")) or any(m.get("error") for m in c["metrics"]) for c in result["cases"])}), flush=True)


def activate():
    """Change the published pointer atomically during an explicit intake window."""
    from scripts.migrate_state import admin_db, control_row

    ledger_path = root() / "migration.json"
    ledger = json.loads(ledger_path.read_text())
    for entry in ledger["versions"]:
        if not entry.get("prepared"):
            raise ValueError("Every version must be prepared before activation.")
        if entry["source_status"] not in ("ready", "published"):
            continue
        job = store.job(entry.get("evaluation_id"))
        if not job or job["status"] != "completed":
            raise ValueError("Every ready version requires a completed evaluation.")
        cases = (job.get("result") or {}).get("cases", [])
        if len(cases) != 10 or any(c.get("error") or len(c.get("metrics", [])) != 5 or
            any(m.get("error") or m.get("score") is None for m in c["metrics"]) for c in cases):
            raise ValueError("Inspect incomplete or failed evaluation measurements before activation.")
    candidate = next(e["target"] for e in ledger["versions"] if e["source"] == ledger["source_published"])
    with admin_db(get_settings().database_migration_url) as db:
        if control_row(db)[0] != "intake":
            raise ValueError("Activation requires intake maintenance and a stopped old backend.")
        if db.execute("SELECT EXISTS(SELECT 1 FROM chatbot.jobs WHERE status='running') OR EXISTS(SELECT 1 FROM chatbot.whatsapp_inbox WHERE status IN ('generating','sending'))").fetchone()[0]:
            raise ValueError("Drain active work before activation.")
        current = db.execute("SELECT value FROM chatbot.settings WHERE key='published_version' FOR UPDATE").fetchone()
        if not current or json.loads(current[0]) != ledger["source_published"]:
            raise ValueError("Published source changed; inspect before activation.")
        row = db.execute("SELECT status,manifest FROM chatbot.versions WHERE id=%s FOR UPDATE", (candidate,)).fetchone()
        if not row or row[0] != "ready":
            raise ValueError("Migrated published replacement is not ready.")
        require_compatible_version({"manifest": json.loads(row[1])})
        db.execute("UPDATE chatbot.versions SET manifest=(manifest::jsonb || '{\"archived\":true}'::jsonb)::text WHERE id=ANY(%s)",
                   ([entry["source"] for entry in ledger["versions"]],))
        db.execute("UPDATE chatbot.versions SET status='ready' WHERE status='published'")
        db.execute("UPDATE chatbot.versions SET status='published' WHERE id=%s", (candidate,))
        db.execute("UPDATE chatbot.settings SET value=%s WHERE key='published_version'", (json.dumps(candidate),))
    ledger.update(activated_at=store.now(), published=candidate)
    save(ledger_path, ledger)
    print(json.dumps({"phase": "activated", "published": candidate}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "evaluate", "activate"))
    args = parser.parse_args()
    configure()
    try:
        {"prepare": prepare, "evaluate": evaluate, "activate": activate}[args.phase]()
    finally:
        store.close_pool()


if __name__ == "__main__":
    main()
