"""Pinecone retrieval, retaining cosine-distance semantics for the existing prompt."""

from functools import lru_cache
import time
from langchain_core.documents import Document
from langsmith import traceable
from app.config.settings import get_settings
from app.backend.models import get_embedding_model


@lru_cache(maxsize=1)
def get_vectorstore():
    settings = get_settings()
    if settings.vector_store == "chroma":
        from app.backend.chroma_legacy import get_vectorstore as legacy

        return legacy()
    if not settings.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY is required.")
    from pinecone import Pinecone

    if settings.embedding_model != "intfloat/multilingual-e5-small":
        raise ValueError(
            "This migration preserves multilingual-e5-small; changing embeddings requires a new compatible index and reindexing."
        )
    pc = Pinecone(api_key=settings.pinecone_api_key)
    description = pc.describe_index(settings.pinecone_index_name)
    if description.dimension != 384 or description.metric != "cosine":
        raise ValueError(
            "The current E5 model requires a 384-dimensional cosine index."
        )
    if not description.status["ready"]:
        raise ValueError("Pinecone index is not ready.")
    return pc.Index(host=description.host)


def ingest_records(records, namespace):
    if not records:
        raise ValueError("Knowledge version contains no searchable chunks.")
    index = get_vectorstore()
    for offset in range(0, len(records), 100):
        vectors = []
        for record in records[offset : offset + 100]:
            if len(record["embedding"]) != 384:
                raise ValueError("An embedding has the wrong dimension.")
            metadata = {
                k: v
                for k, v in record["metadata"].items()
                if v is not None and isinstance(v, (str, int, float, bool, list))
            }
            metadata["text"] = record["document"]
            vectors.append(
                {
                    "id": record["id"],
                    "values": record["embedding"],
                    "metadata": metadata,
                }
            )
        index.upsert(vectors=vectors, namespace=namespace)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        found = set()
        for offset in range(0, len(records), 100):
            found.update(
                index.fetch(
                    ids=[r["id"] for r in records[offset : offset + 100]],
                    namespace=namespace,
                ).vectors
            )
        if len(found) == len(records):
            probe = index.query(
                vector=records[0]["embedding"],
                namespace=namespace,
                top_k=1,
                include_metadata=True,
            )
            if probe.matches:
                return len(records)
        time.sleep(1)
    raise TimeoutError(
        "Pinecone has not made every chunk queryable yet; retry indexing."
    )


@traceable(name="knowledge-retrieval", run_type="retriever")
def similarity_search_with_score(query, k=10, filter_dict=None, namespace=None):
    if get_settings().vector_store == "chroma":
        from app.backend.chroma_legacy import similarity_search_with_score as legacy

        return legacy(query=query, k=k, filter_dict=filter_dict)
    if not namespace:
        from app.admin.store import version

        namespace = version()["namespace"]
    conditions = [{key: {"$eq": value}} for key, value in (filter_dict or {}).items()]
    where = (
        conditions[0]
        if len(conditions) == 1
        else {"$and": conditions}
        if conditions
        else None
    )
    response = get_vectorstore().query(
        vector=get_embedding_model().embed_query(query),
        top_k=k,
        namespace=namespace,
        filter=where,
        include_metadata=True,
    )
    result = []
    for match in response.matches:
        metadata = dict(match.metadata or {})
        text = metadata.pop("text", "")
        metadata["chunk_id"] = match.id
        metadata["cosine_similarity"] = float(match.score)
        result.append(
            (Document(page_content=text, metadata=metadata), 1 - float(match.score))
        )
    return result
