"""Import only the active corpus after checking original text against stored passages."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.admin import global_knowledge as kb, kb_store, source_storage, store
from app.admin.chunking import LEGACY
from app.config.settings import get_settings


def inventory():
    active = store.version()
    root = (
        Path(get_settings().data_dir).resolve()
        / "knowledge"
        / active["id"]
        / "knowledge_base"
    )
    configuration = active["manifest"].get("chunking") or LEGACY
    sources = []
    for name in active["manifest"]["files"]:
        name = kb.valid_name(name)
        file = root / name
        content = file.read_bytes()
        expected_hash = active["manifest"].get("file_sha256", {}).get(name)
        digest = hashlib.sha256(content).hexdigest()
        if expected_hash and digest != expected_hash:
            raise ValueError(f"Original hash differs for {name}; import stopped.")
        if name != kb.MENU_FILE:
            expected = Counter(
                r["document"]
                for r in active["records"]
                if r["metadata"].get("source") == name
            )
            actual = Counter(
                d.page_content
                for d in kb.documents(
                    {
                        "name": name,
                        "format": name.rsplit(".", 1)[-1],
                        "pages": kb.extract(content, name),
                    },
                    configuration,
                )
            )
            if not expected or actual != expected:
                raise ValueError(
                    f"Original passages differ for {name}; import stopped."
                )
        elif (
            active["manifest"].get("menu_text")
            and content.decode("utf-8-sig") != active["manifest"]["menu_text"]
        ):
            raise ValueError(
                "Original menu differs from active metadata; import stopped."
            )
        sources.append((name, content, digest, kb.extract(content, name)))
    print(
        f"Verified {len(sources)} active originals; factual passages match the active corpus."
    )
    return active, sources


def run(apply=False):
    if store.version_info()["manifest"].get("global_kb"):
        print("Global knowledge is already active; no legacy import needed.")
        return
    active, sources = inventory()
    if not apply:
        return
    if kb_store.catalog()["initialized"]:
        print("Global sources are already initialized; no changes made.")
        return
    for name, content, digest, pages in sources:
        current = kb_store.catalog()["sources"]
        if any(s["name"] == name and s["sha256"] == digest for s in current):
            continue
        identifier = kb_store.stage_upload(name, len(content))
        blob = kb_store.blob(identifier)
        source_storage.write(
            blob["object_path"],
            content,
            "application/pdf" if name.endswith(".pdf") else "text/plain",
        )
        if (
            hashlib.sha256(source_storage.read(blob["object_path"])).hexdigest()
            != digest
        ):
            raise ValueError(
                "Private original verification failed; active knowledge was not changed."
            )
        kb_store.finish_upload(identifier, digest, pages)
    with store._connection("administration") as db:
        kb_store._state(db, editable=True)
        pointer = db.execute(
            "SELECT value FROM chatbot.settings WHERE key='published_version'"
        ).fetchone()
        import json

        if not pointer or json.loads(pointer["value"]) != active["id"]:
            raise ValueError(
                "Active knowledge changed during import; review before resuming."
            )
        db.execute("UPDATE chatbot.knowledge_state SET initialized=true WHERE id=1")
    print(
        "Private originals imported. Sync knowledge to build and activate the replacement."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write verified originals to private Storage and stage the global source list",
    )
    run(parser.parse_args().apply)
