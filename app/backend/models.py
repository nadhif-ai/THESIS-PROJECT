import logging
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Memuat model embedding teks dari HuggingFace secara lokal.

    Model ini mengubah kalimat menjadi representasi vektor berdimensi 384.
    Fungsi hanya dieksekusi sekali; eksekusi berikutnya langsung dari cache (lru_cache).

    Returns:
        Instance model embedding, dibungkus E5EmbeddingsWrapper jika model E5.
    """
    settings   = get_settings()
    model_name = settings.embedding_model.strip()

    logger.info(f"[Embeddings] Provider: HuggingFace Lokal → model: {model_name}")

    base_embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 32,
        },
    )

    if "e5" in model_name.lower():
        logger.info("[Embeddings] Model E5 terdeteksi. Menggunakan E5EmbeddingsWrapper.")

        class E5EmbeddingsWrapper:
            """
            Pembungkus model E5 yang menambahkan prefix 'passage:' dan 'query:'
            secara otomatis sesuai persyaratan model intfloat/e5-*.
            """

            def __init__(self, inner):
                self.inner = inner

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                """Tambahkan prefix 'passage:' pada dokumen sebelum di-embed."""
                prefixed = [t if t.startswith("passage: ") else f"passage: {t}" for t in texts]
                return self.inner.embed_documents(prefixed)

            def embed_query(self, text: str) -> list[float]:
                """Tambahkan prefix 'query:' pada pertanyaan sebelum di-embed."""
                prefixed = text if text.startswith("query: ") else f"query: {text}"
                return self.inner.embed_query(prefixed)

            def __getattr__(self, name):
                return getattr(self.inner, name)


        return E5EmbeddingsWrapper(base_embeddings)

    return base_embeddings


def get_llm() -> ChatOpenAI:
    """
    Membuat klien LLM yang terhubung ke model Gemini melalui layanan OpenRouter.

    Returns:
        Instance ChatOpenAI yang siap digunakan untuk memanggil LLM.
    """
    settings = get_settings()

    logger.info(f"Initializing LLM: {settings.openrouter_model} via OpenRouter")

    llm = ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.0,
        max_tokens=1024,
        request_timeout=120,
        default_headers={
            "HTTP-Referer": "https://printing-rag-chatbot.local",
            "X-Title": "Digital Printing RAG Chatbot",
        },
    )

    logger.info("LLM initialized successfully.")
    return llm
