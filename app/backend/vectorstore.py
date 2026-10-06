import logging
from typing import Optional

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_core.documents import Document
from app.backend.models import get_embedding_model
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_chroma_instance: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    """
    Mengambil atau menginisialisasi instance ChromaDB (Singleton Pattern).

    Jika instance sudah ada di cache, langsung dikembalikan tanpa membuat ulang.
    Konfigurasi metrik pencarian menggunakan Cosine Distance (hnsw:space=cosine).

    Returns:
        Instance Chroma yang terhubung ke database vektor lokal.
    """
    global _chroma_instance

    if _chroma_instance is not None:
        return _chroma_instance

    settings   = get_settings()
    embeddings = get_embedding_model()

    logger.info(
        f"Initializing ChromaDB at {settings.chroma_persist_dir} "
        f"with collection: {settings.chroma_collection_name}"
    )

    _chroma_instance = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
        collection_metadata={"hnsw:space": "cosine"},
    )

    count = _chroma_instance._collection.count()
    logger.info(f"ChromaDB loaded. Collection contains {count} documents.")
    return _chroma_instance


def clear_collection() -> None:
    """
    Menghapus seluruh koleksi ChromaDB agar dapat dilakukan ingest ulang yang bersih.

    Aman dipanggil meskipun koleksi belum terbentuk sebelumnya.
    Setelah dipanggil, instance cache direset agar dibuat ulang saat dipanggil berikutnya.
    """
    global _chroma_instance

    settings   = get_settings()
    embeddings = get_embedding_model()

    try:
        existing = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )
        existing.delete_collection()
        logger.info("ChromaDB collection deleted.")
    except Exception as e:
        logger.warning(f"Could not delete collection (may not exist yet): {e}")

    _chroma_instance = None


def ingest_documents(documents: list[Document]) -> Chroma:
    """
    Memasukkan daftar dokumen ke dalam ChromaDB secara bertahap (batch processing).

    Dokumen diproses dalam kelompok (batch) berisi 100 dokumen untuk mencegah
    penggunaan memori yang berlebihan saat dataset berukuran besar.

    Args:
        documents: daftar objek Document LangChain yang akan dimasukkan ke database.

    Returns:
        Instance Chroma yang sudah berisi dokumen baru.
    """
    global _chroma_instance

    settings   = get_settings()
    embeddings = get_embedding_model()

    logger.info(f"Ingesting {len(documents)} documents into ChromaDB...")

    _chroma_instance = None
    BATCH_SIZE = 100

    first_batch = documents[:BATCH_SIZE]
    vectorstore = Chroma.from_documents(
        documents=first_batch,
        embedding=embeddings,
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_dir,
        collection_metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"Batch 1 selesai ({len(first_batch)} dokumen).")

    for i in range(BATCH_SIZE, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        vectorstore.add_documents(batch)
        batch_num = i // BATCH_SIZE + 1
        logger.info(f"Batch {batch_num} selesai ({len(batch)} dokumen).")

    count = vectorstore._collection.count()
    logger.info(f"Ingestion complete. ChromaDB now contains {count} documents.")

    _chroma_instance = vectorstore
    return vectorstore


def _build_chroma_filter(filter_dict: Optional[dict]) -> Optional[dict]:
    """
    Mengubah format filter metadata ke format operator eksplisit yang dikenali ChromaDB.

    ChromaDB versi terbaru memerlukan format: {"field": {"$eq": "value"}}
    bukan format lama: {"field": "value"}.

    Args:
        filter_dict: kamus filter metadata, contoh {"intent_type": "FAQ"}.

    Returns:
        Filter dalam format ChromaDB, atau None jika filter_dict kosong.
    """
    if not filter_dict:
        return None

    conditions = [{k: {"$eq": v}} for k, v in filter_dict.items()]

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}


def similarity_search_with_score(
    query: str,
    k: int = 10,
    filter_dict: Optional[dict] = None,
) -> list[tuple[Document, float]]:
    """
    Melakukan pencarian semantik di ChromaDB dan mengembalikan dokumen beserta skor jaraknya.

    Pertanyaan diubah menjadi vektor oleh embedding model, lalu dibandingkan
    dengan semua vektor dokumen menggunakan Cosine Distance.

    Args:
        query       : teks pertanyaan pencarian.
        k           : jumlah hasil teratas yang dikembalikan.
        filter_dict : filter metadata untuk membatasi ruang pencarian.

    Returns:
        Daftar tuple (Document, Cosine Distance) terurut dari yang paling mirip.
        Nilai Cosine Distance mendekati 0 berarti sangat mirip.
    """
    vectorstore   = get_vectorstore()
    chroma_filter = _build_chroma_filter(filter_dict)

    results = vectorstore.similarity_search_with_score(
        query=query,
        k=k,
        filter=chroma_filter,
    )

    logger.debug(f"Semantic search returned {len(results)} results for: {query!r}")
    return results
