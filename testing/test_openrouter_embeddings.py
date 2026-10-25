import math
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.backend import models
from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def embedding_config(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "2048")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "chatbot-nadhif")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def response(rows, status=200):
    return SimpleNamespace(status_code=status, headers={}, json=lambda: {"data": rows})


def test_openrouter_query_passage_and_response_order(monkeypatch):
    calls = []
    vector = [1.0] * 2048
    def post(url, **kwargs):
        calls.append(kwargs["json"])
        texts = kwargs["json"]["input"]
        return response([{"index": i, "embedding": vector} for i in reversed(range(len(texts)))])
    monkeypatch.setattr("requests.post", post)
    model = models.OpenRouterEmbeddings()
    assert len(model.embed_query("Alamat toko?")) == 2048
    documents = model.embed_documents(["Alamat", "Harga"])
    assert len(documents) == 2
    assert math.isclose(sum(v * v for v in documents[0]), 1)
    assert calls[0]["input_type"] == "query"
    assert calls[1]["input_type"] == "passage"
    assert calls[1]["input"] == ["Alamat", "Harga"]
    assert all(c["model"] == "nvidia/nemotron-3-embed-1b:free" and
               c["provider"] == {"allow_fallbacks": False} for c in calls)


@pytest.mark.parametrize("input_type,attempts,timeout", [("query", 2, (5, 20)), ("passage", 3, (10, 60))])
def test_transient_embedding_retries_are_bounded(monkeypatch, input_type, attempts, timeout):
    calls = []
    monkeypatch.setattr("requests.post", lambda *a, **k: calls.append(k) or response([], 429))
    monkeypatch.setattr("time.sleep", lambda _: None)
    with pytest.raises(models.EmbeddingUnavailable, match="429"):
        models.OpenRouterEmbeddings()._embed(["Alamat?"], input_type)
    assert len(calls) == attempts
    assert all(call["timeout"] == timeout for call in calls)


@pytest.mark.parametrize("rows", [[], [{"index": 0, "embedding": [1.0] * 384}],
    [{"index": 0, "embedding": [float("nan")] * 2048}],
    [{"index": 0, "embedding": [0.0] * 2048}]])
def test_bad_vectors_are_rejected_without_padding_or_retry(monkeypatch, rows):
    calls = []
    monkeypatch.setattr("requests.post", lambda *a, **k: calls.append(1) or response(rows))
    with pytest.raises(ValueError):
        models.OpenRouterEmbeddings().embed_query("Alamat?")
    assert len(calls) == 1


def test_ingestion_verifies_ids_without_downloading_full_vectors(monkeypatch):
    from app.backend import vectorstore
    records = [{"id": str(i), "document": "Passage", "metadata": {}, "embedding": [0.1] * 2048} for i in range(33)]
    batches = []
    class Index:
        def upsert(self, vectors, **kwargs): batches.append(len(vectors))
        def list(self, **kwargs): yield [r["id"] for r in records]
        def fetch(self, **kwargs): pytest.fail("Do not download all 2048-dimensional vectors to check IDs")
        def query(self, **kwargs): return SimpleNamespace(matches=[object()])
    monkeypatch.setattr(vectorstore, "get_vectorstore", lambda: Index())
    assert vectorstore.ingest_records(records, "synthetic") == 33
    assert batches == [32, 1]


def test_fastapi_imports_without_local_inference_packages():
    result = subprocess.run([sys.executable, "-c", """
import importlib.abc, sys
class NoLocalInference(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'sentence_transformers', 'langchain_huggingface'}:
            raise ImportError('Local inference is unavailable')
sys.meta_path.insert(0, NoLocalInference())
from app import main
"""], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
