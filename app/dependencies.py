import logging
import threading
import time
from pathlib import Path
from app.backend.loader import load_structured_kb_as_documents, calculate_kb_hash
from app.backend.vectorstore import get_vectorstore, ingest_documents, clear_collection
from app.backend.chain import RAGChain
from app.config.settings import get_settings

logger     = logging.getLogger(__name__)
_rag_chain: RAGChain = None
_kb_lock   = threading.Lock()   # Mencegah dua proses ingest berjalan bersamaan


# ---------------------------------------------------------------------------
# Fungsi internal: rebuild ChromaDB dari knowledge_base/
# ---------------------------------------------------------------------------

def _rebuild_vectorstore(settings) -> None:
    """
    Memuat ulang seluruh dokumen dari folder knowledge_base/ dan
    mengingest ulang ke ChromaDB. Fungsi ini thread-safe menggunakan Lock.

    Dipanggil saat startup DAN saat file watcher mendeteksi perubahan.

    Args:
        settings: instance Settings berisi konfigurasi path dan model.
    """
    with _kb_lock:
        logger.info("[RAG] Memulai rebuild ChromaDB dari knowledge_base/ ...")

        documents, source = load_structured_kb_as_documents(
            kb_dir=settings.structured_kb_dir
        )
        logger.info("[RAG] Loaded %d chunk dari [%s].", len(documents), source)

        clear_collection()
        ingest_documents(documents)

        # Simpan hash terbaru agar startup berikutnya bisa skip jika tidak berubah
        hash_path    = Path(settings.chroma_persist_dir) / ".dataset_hash"
        current_hash = calculate_kb_hash(settings.structured_kb_dir)
        hash_path.parent.mkdir(parents=True, exist_ok=True)
        hash_path.write_text(current_hash, encoding="utf-8")

        logger.info("[RAG] Rebuild selesai. %d chunk aktif di ChromaDB.", len(documents))


# ---------------------------------------------------------------------------
# Startup: inisialisasi RAG dengan deteksi hash (skip jika tidak berubah)
# ---------------------------------------------------------------------------

def initialize_rag_system() -> None:
    """
    Menginisialisasi seluruh pipeline RAG saat aplikasi pertama kali dinyalakan.

    Alur kerja:
    1. Muat seluruh dokumen dari folder dataset/knowledge_base/ (TXT/MD/PDF/CSV).
    2. Periksa kecocokan MD5 hash gabungan folder dengan hash yang tersimpan.
    3. Jika isi folder berubah atau database kosong, jalankan rebuild otomatis.
    4. Buat instance RAGChain yang menghubungkan retriever dengan LLM.

    Fungsi ini hanya boleh dipanggil satu kali pada event startup aplikasi FastAPI.
    """
    global _rag_chain

    settings = get_settings()
    logger.info("[RAG] Initializing RAG system ...")

    current_hash = calculate_kb_hash(settings.structured_kb_dir)
    db           = get_vectorstore()
    db_empty     = db._collection.count() == 0

    hash_path = Path(settings.chroma_persist_dir) / ".dataset_hash"
    old_hash  = ""
    if hash_path.exists():
        try:
            old_hash = hash_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    need_rebuild = db_empty or (current_hash != old_hash)

    if need_rebuild:
        logger.info(
            "[RAG] Perubahan knowledge_base/ terdeteksi atau DB kosong "
            "→ Rebuild otomatis ..."
        )
        _rebuild_vectorstore(settings)
    else:
        logger.info("[RAG] knowledge_base/ tidak berubah → Skip ingest.")

    _rag_chain = RAGChain()
    logger.info("[RAG] System ready. Pipeline: ChromaDB (Cosine) → LLM.")


# ---------------------------------------------------------------------------
# File Watcher: memantau knowledge_base/ secara realtime
# ---------------------------------------------------------------------------

def _watch_kb_directory(kb_dir: str, chroma_persist_dir: str, debounce: float = 2.0) -> None:
    """
    Background thread yang memantau perubahan isi folder knowledge_base/ secara realtime.

    Menggunakan watchdog (Observer + FileSystemEventHandler) untuk mendeteksi:
    - File baru ditambahkan    (on_created)
    - File yang ada diedit     (on_modified)
    - File yang ada dihapus    (on_deleted)
    - File dipindahkan/rename  (on_moved)

    Ketika perubahan terdeteksi, sistem menunggu `debounce` detik (default 2 detik)
    untuk memastikan proses salin file telah selesai, lalu menjalankan rebuild ChromaDB.

    Args:
        kb_dir             : path direktori utama dataset (misal: './dataset').
        chroma_persist_dir : path folder penyimpanan ChromaDB untuk update hash.
        debounce           : jeda waktu (detik) setelah event terdeteksi sebelum rebuild.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.warning(
            "[Watcher] Library 'watchdog' tidak terinstal. "
            "Jalankan: pip install watchdog\n"
            "[Watcher] File watcher DINONAKTIFKAN. Restart server manual tetap berfungsi."
        )
        return

    kb_path = Path(kb_dir) / "knowledge_base"
    if not kb_path.exists():
        logger.warning("[Watcher] Folder knowledge_base/ tidak ditemukan. Watcher tidak aktif.")
        return

    _SUPPORTED = {".txt", ".md", ".pdf", ".csv"}

    class KBEventHandler(FileSystemEventHandler):
        def __init__(self):
            self._timer: threading.Timer = None

        def _schedule_rebuild(self, event_type: str, path: str) -> None:
            """Batalkan timer sebelumnya lalu jadwalkan rebuild baru (debounce)."""
            if self._timer and self._timer.is_alive():
                self._timer.cancel()

            logger.info("[Watcher] Event '%s' pada: %s", event_type, Path(path).name)

            settings = get_settings()
            self._timer = threading.Timer(
                debounce,
                _rebuild_vectorstore,
                args=[settings],
            )
            self._timer.daemon = True
            self._timer.start()

        def on_created(self, event):
            if not event.is_directory and Path(event.src_path).suffix.lower() in _SUPPORTED:
                self._schedule_rebuild("created", event.src_path)

        def on_modified(self, event):
            if not event.is_directory and Path(event.src_path).suffix.lower() in _SUPPORTED:
                self._schedule_rebuild("modified", event.src_path)

        def on_deleted(self, event):
            if not event.is_directory and Path(event.src_path).suffix.lower() in _SUPPORTED:
                self._schedule_rebuild("deleted", event.src_path)

        def on_moved(self, event):
            src_ext  = Path(event.src_path).suffix.lower()
            dest_ext = Path(event.dest_path).suffix.lower()
            if not event.is_directory and (src_ext in _SUPPORTED or dest_ext in _SUPPORTED):
                self._schedule_rebuild("moved", event.dest_path)

    handler  = KBEventHandler()
    observer = Observer()
    observer.schedule(handler, str(kb_path), recursive=False)
    observer.start()
    logger.info("[Watcher] Realtime file watcher AKTIF memantau: %s", kb_path)

    try:
        while observer.is_alive():
            time.sleep(1)
    except Exception:
        pass
    finally:
        observer.stop()
        observer.join()
        logger.info("[Watcher] File watcher berhenti.")


def start_kb_watcher() -> None:
    """
    Menjalankan file watcher sebagai daemon background thread.

    Dipanggil satu kali pada event startup FastAPI setelah initialize_rag_system().
    Karena berjalan sebagai daemon thread, watcher otomatis berhenti
    saat proses utama FastAPI dimatikan.
    """
    settings = get_settings()
    watcher_thread = threading.Thread(
        target=_watch_kb_directory,
        args=[settings.structured_kb_dir, settings.chroma_persist_dir],
        daemon=True,
        name="KnowledgeBaseWatcher",
    )
    watcher_thread.start()
    logger.info("[Watcher] Background thread 'KnowledgeBaseWatcher' dimulai.")


# ---------------------------------------------------------------------------
# Getter RAGChain untuk dependency injection di endpoint FastAPI
# ---------------------------------------------------------------------------

def get_rag_chain() -> RAGChain:
    """
    Mengembalikan instance RAGChain yang sudah diinisialisasi.

    Digunakan oleh endpoint FastAPI sebagai dependency injection
    untuk memastikan pipeline RAG selalu tersedia saat menerima request.

    Returns:
        Instance RAGChain yang aktif.

    Raises:
        RuntimeError: jika initialize_rag_system() belum dipanggil sebelumnya.
    """
    global _rag_chain

    if _rag_chain is None:
        raise RuntimeError(
            "RAG system not initialized. Call initialize_rag_system() on startup."
        )

    return _rag_chain
