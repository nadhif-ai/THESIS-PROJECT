import hashlib
import json
import shutil
import threading
import uuid
import tarfile
import re
from pathlib import Path
from langchain_core.documents import Document
from app.admin import store
from app.admin.chunking import Chunking, LEGACY, PREPROCESSING, split_document, token_statistics
from app.backend.loader import _load_csv_file
from app.backend.models import get_embedding_model, embedding_identity
from app.config.settings import get_settings
from app.backend.vectorstore import ingest_records

_lock = threading.RLock()
BASELINE = Path(__file__).resolve().parents[2] / "testing/baselines/2026-10-12-chroma"
ALLOWED = {".txt", ".md", ".pdf", ".csv"}


def valid_name(name):
    if (
        not name
        or Path(name).name != name
        or "\\" in name
        or name.startswith(".")
        or Path(name).suffix.lower() not in ALLOWED
    ):
        raise ValueError("Use a plain filename ending in .txt, .md, .pdf or .csv.")
    return name


def path_for(item):
    return store.data_path() / "knowledge" / item["id"] / "knowledge_base"


def bootstrap():
    if store.get_setting("published_version"):
        return
    with _lock:
        existing = next(
            (v for v in store.versions() if v["manifest"].get("baseline")), None
        )
        if existing:
            item = existing
        else:
            records = json.loads((BASELINE / "index_snapshot.json").read_text())
            identifier = "baseline-" + uuid.uuid4().hex[:12]
            item = {
                "id": identifier,
                "namespace": "avg-" + identifier,
                "status": "indexing",
                "created_at": store.now(),
                "manifest": {"baseline": True, "files": [], "chunking": LEGACY},
                "records": records,
                "error": None,
            }
            path_for(item).mkdir(parents=True, exist_ok=True)
            with tarfile.open(BASELINE / "source_snapshot.tar.gz") as archive:
                for member in archive.getmembers():
                    relative = Path(member.name)
                    if member.isfile() and relative.parent == Path(
                        "dataset/knowledge_base"
                    ):
                        name = valid_name(relative.name)
                        (path_for(item) / name).write_bytes(
                            archive.extractfile(member).read()
                        )
                        item["manifest"]["files"].append(name)
            store.save_version(item)
        try:
            ingest_records(item["records"], item["namespace"])
            item["status"] = "ready"
            item["error"] = None
            store.save_version(item)
            store.publish(item["id"])
        except Exception:
            item["status"] = "failed"
            item["error"] = "Initial migration failed; check provider connectivity."
            store.save_version(item)
            raise


def new_draft(base_id=None):
    with _lock:
        source = store.version(base_id)
        identifier = "draft-" + uuid.uuid4().hex[:12]
        draft = {
            "id": identifier,
            "namespace": "avg-" + identifier,
            "status": "draft",
            "created_at": store.now(),
            "manifest": {
                "files": list(source["manifest"]["files"]),
                **({"menu_text": source["manifest"]["menu_text"]} if "menu_text" in source["manifest"] else {}),
                "base": source["id"],
                "embedding": source["manifest"].get("embedding"),
                "vector_index": source["manifest"].get("vector_index"),
                "chunking": dict(
                    Chunking(
                        **(
                            source["manifest"].get("chunking", {})
                            if source["manifest"]
                            .get("chunking", {})
                            .get("preprocessing")
                            in ("sections-v1", PREPROCESSING)
                            else {}
                        )
                    ).model_dump(),
                    preprocessing=PREPROCESSING,
                ),
            },
            "records": source["records"],
            "error": None,
        }
        shutil.copytree(path_for(source), path_for(draft))
        store.save_version(draft)
        return draft


def editable(version_id):
    item = store.version(version_id)
    if item["manifest"].get("archived"):
        raise ValueError("Historical versions are read-only. Create a new draft to edit this knowledge.")
    if item["status"] not in ("draft", "failed"):
        raise ValueError("Create a new draft to edit an indexed or published version.")
    return item


def configure_chunking(version_id, config):
    with _lock:
        item = editable(version_id)
        item["manifest"]["chunking"] = dict(
            config.model_dump(), preprocessing=PREPROCESSING
        )
        item["status"] = "draft"
        item["error"] = None
        store.save_version(item)


def draft_documents(file, config, *, preprocessing=PREPROCESSING):
    extension = file.suffix.lower()
    if extension in (".txt", ".md"):
        raw = [Document(page_content=file.read_text(encoding="utf-8-sig"))]
    elif extension == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader

        raw = PyPDFLoader(str(file)).load()
    else:
        raw = _load_csv_file(file)
    documents = []
    for document in raw:
        document.metadata.update(
            source=file.name,
            format=extension.lstrip("."),
            answer_source="knowledge_base",
        )
        documents.extend(split_document(document, config, preprocessing=preprocessing))
    for ordinal, document in enumerate(documents):
        document.metadata["chunk_index"] = ordinal
        match = re.search(
            r"\[MEDIA:\s*(https?://[^\s\]]+)\]", document.page_content, re.IGNORECASE
        )
        if match:
            document.metadata["media_url"] = match.group(1).strip()
            document.page_content = re.sub(
                r"\[MEDIA:\s*https?://[^\s\]]+\]", "", document.page_content
            ).strip()
    return documents


def save_file(version_id, name, content):
    with _lock:
        item = editable(version_id)
        name = valid_name(name)
        path_for(item).mkdir(parents=True, exist_ok=True)
        (path_for(item) / name).write_bytes(content)
        if name == "05_daftar_pertanyaan_populer.txt":
            item["manifest"]["menu_text"] = content.decode("utf-8-sig")
        item["manifest"]["files"] = sorted(set(item["manifest"]["files"] + [name]))
        item["status"] = "draft"
        item["error"] = None
        store.save_version(item)


def delete_file(version_id, name):
    with _lock:
        item = editable(version_id)
        name = valid_name(name)
        (path_for(item) / name).unlink(missing_ok=True)
        if name == "05_daftar_pertanyaan_populer.txt":
            item["manifest"]["menu_text"] = ""
        item["manifest"]["files"] = [n for n in item["manifest"]["files"] if n != name]
        item["status"] = "draft"
        store.save_version(item)


def index_version(version_id):
    with _lock:
        item = editable(version_id)
        # A failed partial upsert must not leave stale vectors in the next attempt.
        item["namespace"] = "avg-" + item["id"] + "-" + uuid.uuid4().hex[:8]
        item["status"] = "indexing"
        store.save_version(item)
    try:
        previous = {r["id"]: r for r in item["records"]}
        # Fingerprints allow reuse of frozen vectors even when Chroma used random IDs.
        compatible = (item["manifest"].get("embedding") == embedding_identity() and
                      item["manifest"].get("vector_index") == get_settings().pinecone_index_name)
        reusable = {
            (r["metadata"].get("source"), r["document"]): r.get("embedding")
            for r in previous.values() if compatible
        }
        config = Chunking(**item["manifest"].get("chunking", {}))
        preprocessing = item["manifest"].get("chunking", {}).get("preprocessing")
        if preprocessing not in ("sections-v1", PREPROCESSING):
            preprocessing = PREPROCESSING
        item["manifest"]["chunking"] = dict(
            config.model_dump(), preprocessing=preprocessing
        )
        hashes = {}
        records = []
        pending = []
        documents = []
        for name in item["manifest"]["files"]:
            file = path_for(item) / valid_name(name)
            hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
            if name == "05_daftar_pertanyaan_populer.txt":
                continue
            docs = draft_documents(file, config, preprocessing=preprocessing)
            if not docs:
                raise ValueError(
                    f"{name}: no searchable text; check the file format or use a text-based PDF."
                )
            documents.extend(docs)
            for ordinal, doc in enumerate(docs):
                key = hashlib.sha256(
                    (name + "\0" + str(ordinal) + "\0" + doc.page_content).encode()
                ).hexdigest()
                record = {
                    "id": key,
                    "document": doc.page_content,
                    "metadata": dict(
                        doc.metadata,
                        document_id=hashlib.sha256(name.encode()).hexdigest()[:16],
                    ),
                    "embedding": reusable.get((name, doc.page_content)),
                }
                records.append(record)
                if record["embedding"] is None:
                    pending.append(record)
        statistics = token_statistics(documents)
        if statistics["over_limit"]:
            raise ValueError(
                f"{statistics['over_limit']} passages exceed the conservative embedding input bound. Reduce chunk size before indexing."
            )
        item["manifest"]["index_statistics"] = statistics
        item["manifest"]["file_sha256"] = hashes
        item["manifest"]["corpus_sha256"] = hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest()
        if pending:
            vectors = get_embedding_model().embed_documents(
                [r["document"] for r in pending]
            )
            if len(vectors) != len(pending):
                raise ValueError("Embedding provider returned an incomplete batch.")
            for record, vector in zip(pending, vectors):
                record["embedding"] = vector
        ingest_records(records, item["namespace"])
        item["manifest"]["embedding"] = embedding_identity()
        item["manifest"]["vector_index"] = get_settings().pinecone_index_name
        item["records"] = records
        item["status"] = "ready"
        item["error"] = None
        store.save_version(item)
        return {
            "version_id": version_id,
            "chunks": len(records),
            "new_embeddings": len(pending),
        }
    except Exception as error:
        item["status"] = "failed"
        item["error"] = str(error)
        store.save_version(item)
        raise
