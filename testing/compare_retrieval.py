"""Re-run the original retrieval metric against the published Pinecone corpus."""

import csv
import json
from datetime import datetime
from pathlib import Path
from app.admin import store, knowledge
from app.backend.vectorstore import similarity_search_with_score


def main():
    store.initialize()
    knowledge.bootstrap()
    rows = list(
        csv.DictReader(
            (knowledge.BASELINE / "retrieval.csv").open(encoding="utf-8-sig")
        )
    )
    results = []
    for row in rows:
        sources = [
            doc.metadata["source"]
            for doc, _ in similarity_search_with_score(row["question"], k=3)
        ]
        hits = sum(row["expected_source"] in source for source in sources)
        results.append(
            {
                "id": row["no"],
                "sources": sources,
                "hit_at_3": int(hits > 0),
                "precision_at_3": round(hits / 3, 4),
            }
        )
    report = {
        "backend": "pinecone",
        "reference_set": "frozen-2026-10-12-source-labels",
        "namespace": store.version()["namespace"],
        "cases": results,
        "hit_rate_at_3": sum(r["hit_at_3"] for r in results) / len(results),
        "precision_at_3": sum(r["precision_at_3"] for r in results) / len(results),
    }
    path = Path("testing/comparisons")
    path.mkdir(exist_ok=True)
    output = path / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-pinecone.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Hit Rate@3: {report['hit_rate_at_3']:.1%}; Precision@3: {report['precision_at_3']:.1%}; saved {output}"
    )


if __name__ == "__main__":
    main()
