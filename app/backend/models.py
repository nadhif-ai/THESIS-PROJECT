import asyncio
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from functools import lru_cache

import httpx
import requests
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
NEMOTRON = "nvidia/nemotron-3-embed-1b:free"


def embedding_identity():
    settings = get_settings()
    if settings.embedding_model != NEMOTRON or settings.embedding_dimensions != 2048:
        raise ValueError("The active runtime requires Nemotron/OpenRouter with 2048 dimensions. Use the separate baseline environment for E5.")
    return {"provider": "openrouter", "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions, "normalization": "l2",
            "input_contract": "nvidia-query-passage-v1"}


class EmbeddingUnavailable(RuntimeError):
    pass


class OpenRouterEmbeddings(Embeddings):
    def __init__(self):
        self.identity = embedding_identity()
        self.settings = get_settings()

    def _embed(self, texts, input_type):
        if any(not isinstance(t, str) or not t.strip() or len(t.encode("utf-8")) + 64 > 32768 for t in texts):
            raise ValueError("Embedding inputs must be nonempty text within the conservative 32768-token bound.")
        attempts = 2 if input_type == "query" else 3
        for attempt in range(attempts):
            status = None
            try:
                response = requests.post(
                    self.settings.openrouter_base_url.rstrip("/") + "/embeddings",
                    headers={"Authorization": "Bearer " + self.settings.openrouter_api_key},
                    json={"model": self.identity["model"], "input": texts,
                          "dimensions": self.identity["dimensions"], "encoding_format": "float",
                          "input_type": input_type, "provider": {"allow_fallbacks": False}},
                    timeout=(5, 20) if input_type == "query" else (10, 60),
                )
                status = response.status_code
            except requests.RequestException:
                if attempt == attempts - 1:
                    raise EmbeddingUnavailable(f"OpenRouter embedding transport unavailable after {attempts} attempts.") from None
            else:
                if status == 200:
                    break
                if status != 429 and status < 500:
                    raise EmbeddingUnavailable(f"OpenRouter embeddings returned HTTP {status}; check credentials and request configuration.")
                if attempt == attempts - 1:
                    raise EmbeddingUnavailable(f"OpenRouter embeddings returned HTTP {status} after {attempts} attempts; retry the job later.")
            time.sleep(2 ** attempt)
        try:
            rows = response.json()["data"]
            if len(rows) != len(texts) or sorted(r["index"] for r in rows) != list(range(len(texts))):
                raise ValueError
            vectors = []
            for row in sorted(rows, key=lambda r: r["index"]):
                vector = row["embedding"]
                if len(vector) != self.identity["dimensions"] or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector):
                    raise ValueError
                norm = math.sqrt(sum(v * v for v in vector))
                if not math.isfinite(norm) or norm == 0:
                    raise ValueError
                vectors.append([v / norm for v in vector])
            return vectors
        except (KeyError, TypeError, ValueError):
            raise ValueError("OpenRouter returned incomplete or invalid embedding vectors; indexing was stopped.") from None

    def embed_documents(self, texts):
        vectors = []
        for start in range(0, len(texts), 32):
            vectors.extend(self._embed(texts[start:start + 32], "passage"))
        return vectors

    def embed_query(self, text):
        return self._embed([text], "query")[0]


@lru_cache(maxsize=1)
def get_embedding_model():
    return OpenRouterEmbeddings()


@lru_cache(maxsize=8)
def get_llm(model: str | None = None, *, structured=False, timeout=45) -> ChatOpenAI:
    """
    Membuat klien model jawaban melalui layanan OpenRouter.

    Returns:
        Instance ChatOpenAI yang siap digunakan untuk memanggil LLM.
    """
    settings = get_settings()

    selected_model = model or settings.openrouter_model
    bounded_reasoning = structured and selected_model in {"openai/gpt-oss-20b", "z-ai/glm-5.3-flash"}
    structured_parameters = {"provider": {"require_parameters": True}}
    if bounded_reasoning:
        structured_parameters["reasoning"] = {"effort": "low"}
    logger.info("Initializing LLM: %s via OpenRouter", selected_model)

    llm = ChatOpenAI(
        model=selected_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.0,
        max_tokens=4096 if bounded_reasoning else 2048,
        request_timeout=timeout,
        max_retries=0 if structured else 1,
        extra_body=structured_parameters if structured else None,
        default_headers={
            "HTTP-Referer": "https://printing-rag-chatbot.local",
            "X-Title": "Digital Printing RAG Chatbot",
        },
    )

    logger.info("LLM initialized successfully.")
    return llm


async def _structured_result(model, schema, messages, timeout):
    # Cached async transports cannot be shared between these per-call event loops.
    async with asyncio.timeout(timeout):
        async with httpx.AsyncClient(timeout=timeout) as transport:
            async with AsyncOpenAI(
                api_key=model.openai_api_key.get_secret_value(),
                base_url=model.openai_api_base,
                organization=model.openai_organization,
                timeout=timeout,
                max_retries=model.max_retries,
                default_headers=model.default_headers,
                default_query=model.default_query,
                http_client=transport,
            ) as client:
                owned_model = model.model_copy(update={
                    "root_async_client": client,
                    "async_client": client.chat.completions,
                    "http_async_client": transport,
                })
                return await owned_model.with_structured_output(
                    schema, method="json_schema", strict=True, include_raw=True,
                ).ainvoke(messages)


def structured_response(schema, messages, *, timeout, model=None):
    """One provider-constrained structured call, retaining reported usage for diagnostics."""
    from app.admin import store

    selected_model = model or store.get_setting("product_intent_model", get_settings().product_intent_model)
    model = get_llm(selected_model, structured=True, timeout=timeout)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        result = asyncio.run(_structured_result(model, schema, messages, timeout))
    else:
        # Join the bounded async call; a thread timeout would leave its HTTP request alive.
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(
                copy_context().run, asyncio.run,
                _structured_result(model, schema, messages, timeout),
            ).result()
    if result.get('parsing_error') or result.get('parsed') is None:
        raise ValueError('Invalid structured provider response')
    raw = result['raw']
    usage = raw.usage_metadata or {}
    metadata = raw.response_metadata or {}
    reported = metadata.get('token_usage') or {}
    cost = reported.get('cost')
    return result['parsed'], {
        'prompt_tokens': usage.get('input_tokens', reported.get('prompt_tokens', 0)),
        'completion_tokens': usage.get('output_tokens', reported.get('completion_tokens', 0)),
        'cost_usd': cost if isinstance(cost, (int, float)) else None,
        'provider': metadata.get('provider'), 'model': metadata.get('model_name'),
        'requests': 1,
    }
