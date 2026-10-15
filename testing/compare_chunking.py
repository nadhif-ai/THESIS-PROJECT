"""Audit candidate passage sizes locally; --index also compares Pinecone retrieval.

No answer/judge calls and no publishing. File-source precision is a historical
diagnostic, not answer accuracy or DeepEval Contextual Precision.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from app.admin import knowledge, store
from app.admin.chunking import Chunking, token_statistics
from app.backend.vectorstore import similarity_search_with_score


CONFIGURATIONS = [(1500, 200), (1000, 100), (800, 80), (1000, 0)]
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-version", help="Default: the current published version")
    parser.add_argument(
        "--index",
        action="store_true",
        help="Create isolated versions and query Pinecone; never publish",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "testing/comparisons/chunking-candidates.json",
    )
    args = parser.parse_args()
    store.check_ready()
    source = store.version(args.base_version)
    hashes = {
        name: hashlib.sha256(
            (knowledge.path_for(source) / name).read_bytes()
        ).hexdigest()
        for name in source["manifest"]["files"]
    }
    report = {
        "base_version": source["id"],
        "corpus_sha256": hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest(),
        "file_sha256": hashes,
        "preprocessing": "sections-v1",
        "started_at": store.now(),
        "mode": "index-and-retrieval" if args.index else "local-size-audit",
        "reference_sha256": hashlib.sha256(
            (ROOT / "testing/test_dataset.csv").read_bytes()
        ).hexdigest(),
        "held_business_reference_ids": [
            row["id"]
            for row in json.loads(
                (ROOT / "testing/evals/qa-reference-candidates.json").read_text()
            )
            if row.get("review_status") == "hold"
        ],
        "note": "All candidates use the same section preprocessing. Original frozen vectors remain a separate historical baseline. No answer-quality claims follow from this report.",
        "candidates": [],
    }
    rows = list(
        csv.DictReader((ROOT / "testing/test_dataset.csv").open(encoding="utf-8-sig"))
    )
    for size, overlap in CONFIGURATIONS:
        config = Chunking(chunk_size=size, chunk_overlap=overlap)
        docs = [
            document
            for name in source["manifest"]["files"]
            if name != "05_daftar_pertanyaan_populer.txt"
            for document in knowledge.draft_documents(
                knowledge.path_for(source) / name, config
            )
        ]
        statistics = token_statistics(docs)
        result = {**config.model_dump(), "chunks": len(docs), **statistics}
        report["candidates"].append(result)
        if statistics["over_limit"]:
            result["status"] = "blocked-by-embedding-token-limit"
        elif args.index:
            draft = knowledge.new_draft(source["id"])
            knowledge.configure_chunking(draft["id"], config)
            result["version_id"] = draft["id"]
            knowledge.index_version(draft["id"])
            result["namespace"] = store.version(draft["id"])["namespace"]
            cases = []
            for row in rows:
                passages = similarity_search_with_score(
                    row["question"], k=3, namespace=result["namespace"]
                )
                hits = sum(
                    row["expected_source"] in doc.metadata["source"]
                    for doc, _ in passages
                )
                cases.append(
                    {
                        "id": row["id"],
                        "hit_at_3": int(hits > 0),
                        "source_precision_at_3": hits / 3,
                        "passages": [
                            {
                                "source": doc.metadata["source"],
                                "text": doc.page_content,
                                "cosine_similarity": 1 - distance,
                            }
                            for doc, distance in passages
                        ],
                    }
                )
            result.update(
                status="ready",
                cases=cases,
                hit_rate_at_3=sum(c["hit_at_3"] for c in cases) / len(cases),
                source_precision_at_3=sum(c["source_precision_at_3"] for c in cases)
                / len(cases),
            )
        else:
            result["status"] = "size-audited-only"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            f"{size}/{overlap}: {len(docs)} passages, max {statistics['max_tokens']} tokens; {result['status']}"
        )
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
