"""Fuse exact-term evidence with cosine rank without relabeling cosine distances."""

import math
import re
import logging
from collections import Counter
import requests
from langsmith import traceable
from app.config.settings import get_settings


RRF_RECIPE = "semantic-bm25-rrf-v1"
RETRIEVAL_RECIPE = "semantic-bm25-rrf-bge-v2"
RERANK_MODEL = "bge-reranker-v2-m3"
logger = logging.getLogger(__name__)


def rank_candidates(query, candidates, k):
    terms = set(re.findall(r"\w+", query.casefold()))
    documents = [Counter(re.findall(r"\w+", doc.page_content.casefold())) for doc, _ in candidates]
    if not documents:
        return []
    lengths = [sum(counts.values()) for counts in documents]
    average = sum(lengths) / len(lengths) or 1
    frequencies = {term: sum(term in counts for counts in documents) for term in terms}
    lexical = []
    for index, counts in enumerate(documents):
        score = 0
        for term in terms:
            count = counts[term]
            if count:
                inverse = math.log(1 + (len(documents) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
                score += inverse * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * lengths[index] / average))
        if score > 0:
            lexical.append((index, score))
    lexical.sort(key=lambda item: (-item[1], item[0]))
    ranks = {index: rank for rank, (index, _) in enumerate(lexical, 1)}
    fused = sorted(range(len(candidates)), key=lambda index: (
        -(1 / (60 + index + 1) + (1 / (60 + ranks[index]) if index in ranks else 0)), index,
    ))
    result = []
    seen = set()
    for index in fused:
        doc, distance = candidates[index]
        identity = (doc.metadata.get("source"), ' '.join(doc.page_content.split()))
        if identity in seen:
            continue
        seen.add(identity)
        # Copy metadata so cached documents and historic evidence are never mutated.
        doc = doc.model_copy(update={"metadata": {**doc.metadata,
            "retrieval_recipe": RRF_RECIPE, "semantic_rank": index + 1,
            "lexical_rank": ranks.get(index)}})
        result.append((doc, distance))
        if len(result) == k:
            break
    return result


@traceable(name="knowledge-reranking", run_type="retriever")
def rerank_candidates(query, candidates, k):
    """Rerank real passages; a bounded provider failure retains the RRF order."""
    if not candidates:
        return []
    fallback = None
    try:
        response = requests.post(
            "https://api.pinecone.io/rerank",
            headers={"Api-Key": get_settings().pinecone_api_key,
                     "X-Pinecone-Api-Version": "2025-10"},
            json={"model": RERANK_MODEL, "query": query,
                  "documents": [{"id": str(index), "text": doc.page_content}
                                for index, (doc, _) in enumerate(candidates)],
                  "top_n": len(candidates), "return_documents": False,
                  "parameters": {"truncate": "END"}},
            timeout=(3, 8),
        )
        if response.status_code != 200:
            fallback = f"provider_http_{response.status_code}"
        else:
            rows = response.json()["data"]
            if (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)
                    or len(rows) != len(candidates)
                    or any(type(row.get("index")) is not int for row in rows)
                    or sorted(row["index"] for row in rows) != list(range(len(candidates)))
                    or any(type(row.get("score")) not in (int, float)
                           or not math.isfinite(row["score"]) for row in rows)):
                raise ValueError("Invalid reranking response")
            rows = sorted(rows, key=lambda row: -row["score"])
            return [(candidates[row["index"]][0].model_copy(update={"metadata": {
                        **candidates[row["index"]][0].metadata,
                        "retrieval_recipe": RETRIEVAL_RECIPE,
                        "rerank_model": RERANK_MODEL, "rerank_score": row["score"],
                        "rrf_rank": row["index"] + 1}}), candidates[row["index"]][1])
                    for row in rows[:k]]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        fallback = "provider_unavailable_or_invalid_response"
    logger.warning("Reranking unavailable (%s); using captured RRF order", fallback)
    return [(doc.model_copy(update={"metadata": {**doc.metadata,
                "rerank_model": RERANK_MODEL, "rerank_fallback": fallback}}), distance)
            for doc, distance in candidates[:k]]
