"""Source validation and a single staged configuration with atomic synchronization."""

import hashlib
import io
import json
import re
import unicodedata

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.admin import kb_store, source_storage, store
from app.admin.chunking import Chunking, split_document, token_statistics
from app.backend.models import embedding_identity, get_embedding_model
from app.backend.vectorstore import get_vectorstore
from app.config.settings import get_settings

EMPTY_ANSWER = "Maaf Kak, informasi tersebut belum tersedia saat ini."
MENU_FILE = "05_daftar_pertanyaan_populer.txt"


def valid_name(name):
    name = unicodedata.normalize("NFC", name).strip()
    if (
        not name
        or len(name) > 180
        or name.startswith(".")
        or any(c in name for c in "/\\\x00")
        or any(ord(c) < 32 for c in name)
    ):
        raise ValueError(
            "Use a filename without paths or control characters (maximum 180 characters)."
        )
    if name.rsplit(".", 1)[-1].lower() not in ("txt", "pdf"):
        raise ValueError("Upload a UTF-8 TXT file or a PDF with selectable text.")
    stem, extension = name.rsplit(".", 1)
    return stem + "." + extension.lower()


def extract(content, name):
    if not content or len(content) > source_storage.MAX_BYTES:
        raise ValueError("File must contain between 1 byte and 10 MB.")
    try:
        if name.endswith(".txt"):
            text = content.decode("utf-8-sig")
            if "\x00" in text:
                raise ValueError("TXT files must contain UTF-8 text, not binary data.")
            pages = [{"text": text}]
        else:
            if not content.startswith(b"%PDF-"):
                raise ValueError("The uploaded file is not a PDF.")
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise ValueError("Remove the PDF password before uploading.")
            if len(reader.pages) > 300:
                raise ValueError(
                    "Maximum PDF length is 300 pages. Split the document first."
                )
            pages = [
                {"text": page.extract_text() or "", "page": i + 1}
                for i, page in enumerate(reader.pages)
            ]
    except (UnicodeDecodeError, ValueError):
        raise
    except Exception:
        raise ValueError(
            "The PDF could not be read. Upload a valid PDF with selectable text."
        ) from None
    if sum(len(p["text"].encode("utf-8")) for p in pages) > 1_000_000:
        raise ValueError("Extracted text exceeds 1 MB; split the document first.")
    if not any(any(c.isalnum() for c in p["text"]) for p in pages):
        raise ValueError(
            "No searchable text found. Scanned PDFs need OCR before upload."
        )
    return pages


def finish_upload(identifier, source_id=None):
    item = kb_store.blob(identifier)
    content = source_storage.read(item["object_path"])
    if len(content) != item["size_bytes"]:
        raise ValueError(
            "Uploaded size differs from the registered file. Upload it again."
        )
    return kb_store.finish_upload(
        identifier,
        hashlib.sha256(content).hexdigest(),
        extract(content, item["name"]),
        source_id,
    )


def documents(source, configuration):
    result = []
    config = Chunking(**configuration)
    if config.chunk_overlap > config.chunk_size // 2:
        raise ValueError("Knowledge overlap must be at most half the chunk size.")
    for page in source["pages"]:
        metadata = {
            "source": source["name"],
            "format": source["format"],
            "answer_source": "knowledge_base",
            "source_id": source.get("source_id", ""),
            "document_id": source.get("blob_id", source.get("id", "")),
        }
        if "page" in page:
            metadata["page"] = page["page"]
        document = Document(page_content=page["text"], metadata=metadata)
        if configuration.get("preprocessing") == "legacy":
            result.extend(
                RecursiveCharacterTextSplitter(
                    **config.model_dump(),
                    separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
                ).split_documents([document])
            )
        else:
            result.extend(split_document(document, config))
    for ordinal, document in enumerate(result):
        document.metadata["chunk_index"] = ordinal
        media = re.search(
            r"\[MEDIA:\s*(https?://[^\]\s]+)\]", document.page_content, re.IGNORECASE
        )
        if media:
            document.metadata["media_url"] = media[1]
            document.page_content = document.page_content.replace(media[0], "").strip()
    return result


def preview(identifier):
    source = kb_store.source(identifier)
    config = kb_store.catalog()["chunking"]
    chunks = documents(source, config)
    return {
        "name": source["name"],
        "format": source["format"],
        "text": "\n\n".join(p["text"] for p in source["pages"]),
        "url": source_storage.signed_download(source["object_path"]),
        "chunks": [
            {"text": d.page_content, "metadata": d.metadata} for d in chunks[:10]
        ],
        "chunk_count": len(chunks),
        "navigation_only": source["name"] == MENU_FILE,
    }


def passage_page(identifier, page):
    source = kb_store.source(identifier)
    chunks = documents(source, kb_store.catalog()["chunking"])
    return {
        "chunks": [
            {"text": d.page_content, "metadata": d.metadata}
            for d in chunks[page * 10 : page * 10 + 10]
        ],
        "chunk_count": len(chunks),
    }


def sync_step(identifier, checkpoint, token):
    if (
        checkpoint["embedding"] != embedding_identity()
        or checkpoint["vector_index"] != get_settings().pinecone_index_name
    ):
        raise ValueError(
            "Embedding/index changed after this sync started. Restore its configuration before resuming."
        )
    phase = checkpoint["phase"]
    snapshot_id = "kb-" + identifier
    namespace = "kb-" + identifier
    if phase == "prepare":
        records, menu = [], None
        for source in checkpoint["sources"]:
            if source["name"] == MENU_FILE:
                menu = "\n\n".join(p["text"] for p in source["pages"])
                continue
            for document in documents(source, checkpoint["chunking"]):
                if len(records) >= 5000:
                    raise ValueError(
                        "Knowledge exceeds 5,000 passages. Reduce overlap or shorten sources."
                    )
                digest = hashlib.sha256(
                    (
                        source["blob_id"]
                        + "\0"
                        + str(document.metadata["chunk_index"])
                        + "\0"
                        + document.page_content
                    ).encode()
                ).hexdigest()
                records.append(
                    {
                        "id": digest,
                        "document": document.page_content,
                        "metadata": document.metadata,
                    }
                )
        sources = [
            {k: v for k, v in source.items() if k != "pages"}
            for source in checkpoint["sources"]
        ]
        manifest = {
            "files": [s["name"] for s in sources],
            "source_refs": sources,
            "chunking": checkpoint["chunking"],
            "embedding": embedding_identity(),
            "vector_index": get_settings().pinecone_index_name,
            "chunk_count": len(records),
            "menu_text": menu or "",
            "empty": not records,
            "global_kb": True,
            "corpus_sha256": hashlib.sha256(
                json.dumps([(s["name"], s["sha256"]) for s in sources]).encode()
            ).hexdigest(),
            **token_statistics([Document(page_content=r["document"]) for r in records]),
        }
        store.save_version(
            {
                "id": snapshot_id,
                "namespace": namespace,
                "status": "indexing",
                "created_at": store.now(),
                "manifest": manifest,
                "records": records,
            }
        )
        checkpoint = {
            "phase": "embed",
            "revision": checkpoint["revision"],
            "offset": 0,
            "total": len(records),
            "embedding": checkpoint["embedding"],
            "vector_index": checkpoint["vector_index"],
        }
    elif phase == "embed":
        records = store.version(snapshot_id)["records"]
        batch = records[checkpoint["offset"] : checkpoint["offset"] + 16]
        if batch:
            vectors = get_embedding_model().embed_documents(
                [r["document"] for r in batch]
            )
            get_vectorstore().upsert(
                namespace=namespace,
                vectors=[
                    {
                        "id": r["id"],
                        "values": vector,
                        "metadata": {**r["metadata"], "text": r["document"]},
                    }
                    for r, vector in zip(batch, vectors, strict=True)
                ],
                _request_timeout=30,
            )
            checkpoint["offset"] += len(batch)
        if checkpoint["offset"] == len(records):
            checkpoint["phase"] = "verify"
    elif phase == "verify":
        records = store.version(snapshot_id)["records"]
        if records:
            index = get_vectorstore()
            found = {
                i
                for page in index.list(namespace=namespace, _request_timeout=15)
                for i in page
            }
            if found != {r["id"] for r in records}:
                raise RuntimeError(
                    "Pinecone is still making the synchronized vectors visible."
                )
            probe = index.query(
                namespace=namespace,
                vector=get_embedding_model().embed_query(records[0]["document"]),
                top_k=1,
                include_metadata=True,
                _request_timeout=15,
            )
            if not probe.matches:
                raise RuntimeError("Pinecone vectors are not queryable yet.")
        checkpoint["phase"] = "activate"
    elif phase == "activate":
        kb_store.activate(identifier, token, snapshot_id, checkpoint["revision"])
        checkpoint["phase"] = "cleanup"
    elif phase == "cleanup":
        from app.integrations.admin_queue import schedule_cleanup

        schedule_cleanup(identifier)
        checkpoint["phase"] = "completed"
    return (
        checkpoint,
        {
            "phase": checkpoint["phase"],
            "completed": checkpoint.get("offset", 0),
            "total": checkpoint.get("total", 0),
        },
        {"snapshot_id": snapshot_id},
        checkpoint["phase"] == "completed",
    )


def cleanup():
    # The grace period exceeds request execution; unfinished evaluations pin snapshots.
    snapshots, blobs = kb_store.garbage_candidates(get_settings().pinecone_index_name)
    for row in snapshots:
        get_vectorstore().delete(
            delete_all=True, namespace=row["namespace"], _request_timeout=30
        )
        kb_store.finish_deletion(snapshot_id=row["id"])
    for row in blobs:
        if kb_store.claim_blob_deletion(row["id"]):
            source_storage.remove(row["object_path"])
            kb_store.finish_deletion(blob_id=row["id"])
    return bool(snapshots or blobs)
