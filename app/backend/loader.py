import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanta format file yang didukung oleh loader
# ---------------------------------------------------------------------------
_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".csv"}

# Ukuran chunk untuk teks naratif (TXT / MD / PDF)
_CHUNK_SIZE    = 1500
_CHUNK_OVERLAP = 200


def _hash_directory(kb_path: Path) -> str:
    """
    Menghitung satu nilai MD5 gabungan dari seluruh isi berkas di direktori
    knowledge_base. Digunakan untuk mendeteksi perubahan isi folder secara otomatis.

    Berkas dipindai secara alfabetis agar urutan selalu konsisten.

    Args:
        kb_path: objek Path dari direktori knowledge_base.

    Returns:
        String heksadesimal MD5 gabungan seluruh berkas.
    """
    hasher = hashlib.md5()
    for file_path in sorted(kb_path.glob("*.*")):
        if file_path.suffix.lower() in _SUPPORTED_EXTENSIONS:
            try:
                hasher.update(file_path.name.encode("utf-8"))
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except Exception as e:
                logger.warning("Gagal membaca berkas saat hashing: %s — %s", file_path, e)
    return hasher.hexdigest()


def _load_text_file(file_path: Path, splitter: RecursiveCharacterTextSplitter) -> list[Document]:
    """
    Memuat berkas teks naratif (.txt atau .md) dan memotongnya menjadi
    potongan-potongan kontekstual menggunakan RecursiveCharacterTextSplitter.

    Setiap potongan diberi metadata untuk keperluan audit dan penelusuran sumber.

    Args:
        file_path: path absolut berkas teks.
        splitter : instance RecursiveCharacterTextSplitter yang sudah dikonfigurasi.

    Returns:
        Daftar objek Document siap ingest ke ChromaDB.
    """
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = file_path.read_text(encoding="utf-8-sig")

    raw_doc = Document(
        page_content=raw_text,
        metadata={
            "source":        file_path.name,
            "format":        file_path.suffix.lower().lstrip("."),
            "answer_source": "knowledge_base",
        },
    )

    import re as _re
    chunks = splitter.split_documents([raw_doc])

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        # Ekstrak tag [MEDIA: url] jika ada di dalam teks chunk, lalu bersihkan dari teks utama
        match = _re.search(r"\[MEDIA:\s*(https?://[^\s\]]+)\]", chunk.page_content, _re.IGNORECASE)
        if match:
            chunk.metadata["media_url"] = match.group(1).strip()
            chunk.page_content = _re.sub(r"\[MEDIA:\s*https?://[^\s\]]+\]", "", chunk.page_content).strip()

    logger.info("  [TXT/MD] %s → %d chunk", file_path.name, len(chunks))
    return chunks


def _load_pdf_file(file_path: Path, splitter: RecursiveCharacterTextSplitter) -> list[Document]:
    """
    Memuat berkas PDF halaman per halaman menggunakan PyPDFLoader dari LangChain,
    lalu memotong teks hasil ekstraksi menggunakan splitter yang sama.

    Membutuhkan dependensi: pip install pypdf

    Args:
        file_path: path absolut berkas PDF.
        splitter : instance RecursiveCharacterTextSplitter yang sudah dikonfigurasi.

    Returns:
        Daftar objek Document siap ingest ke ChromaDB.
    """
    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError:
        logger.error(
            "PyPDFLoader tidak ditemukan. Jalankan: pip install pypdf langchain-community"
        )
        return []

    try:
        loader = PyPDFLoader(str(file_path))
        pages  = loader.load()
    except Exception as e:
        logger.error("Gagal memuat PDF %s: %s", file_path.name, e)
        return []

    for page in pages:
        page.metadata["source"]        = file_path.name
        page.metadata["format"]        = "pdf"
        page.metadata["answer_source"] = "knowledge_base"

    chunks = splitter.split_documents(pages)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    logger.info("  [PDF] %s → %d halaman → %d chunk", file_path.name, len(pages), len(chunks))
    return chunks


def _load_csv_file(file_path: Path) -> list[Document]:
    """
    Memuat berkas CSV terstruktur (format Q&A) dan mengubah setiap barisnya
    menjadi satu objek Document.

    Kolom yang diharapkan: doc_id, intent_type, title, body, media_url (opsional).

    Args:
        file_path: path absolut berkas CSV.

    Returns:
        Daftar objek Document siap ingest ke ChromaDB.
    """
    try:
        df = pd.read_csv(
            file_path,
            dtype=str,
            keep_default_na=False,
            engine="python",
            on_bad_lines="skip",
            encoding="utf-8-sig",
        )
        df.columns = [c.lstrip("\ufeff").strip() for c in df.columns]
    except Exception as e:
        logger.error("Gagal membaca CSV %s: %s", file_path.name, e)
        return []

    documents: list[Document] = []
    for _, row in df.iterrows():
        doc_id      = str(row.get("doc_id",      "")).strip()
        intent_type = str(row.get("intent_type", "")).strip()
        title       = str(row.get("title",       "")).strip()
        body        = str(row.get("body",        "")).strip()
        media_url   = str(row.get("media_url",   "")).strip()

        if not title or not body:
            continue

        documents.append(
            Document(
                page_content=f"Pertanyaan: {title}\nJawaban: {body}",
                metadata={
                    "id":            doc_id,
                    "source":        file_path.name,
                    "format":        "csv",
                    "intent_type":   intent_type,
                    "judul":         title,
                    "answer_source": "knowledge_base",
                    "body":          body,
                    "media_url":     media_url,
                },
            )
        )

    logger.info("  [CSV] %s → %d baris → %d dokumen", file_path.name, len(df), len(documents))
    return documents


def load_structured_kb_as_documents(kb_dir: str) -> Tuple[list, str]:
    """
    Memuat seluruh berkas pengetahuan dari direktori knowledge_base dan
    mengubahnya menjadi daftar objek Document LangChain siap ingest ke ChromaDB.

    Format berkas yang didukung:
        - .txt  : Teks naratif (SOP, Panduan Pracetak, Spesifikasi Bahan, dsb.)
        - .md   : Dokumen Markdown (struktur judul ## dikenali sebagai pemisah)
        - .pdf  : Dokumen PDF (diekstrak halaman per halaman)
        - .csv  : Data terstruktur Q&A (format: doc_id, intent_type, title, body)

    Berkas dipindai secara otomatis dari folder knowledge_base di dalam kb_dir.
    Jika folder knowledge_base tidak ada, fungsi ini fallback ke kb_dir langsung.

    Args:
        kb_dir: path direktori utama dataset (misal: './dataset').

    Returns:
        Tuple berisi (daftar Document gabungan, label sumber data).

    Raises:
        FileNotFoundError: jika folder knowledge_base tidak ditemukan.
    """
    kb_path = Path(kb_dir) / "knowledge_base"

    if not kb_path.exists():
        raise FileNotFoundError(
            f"Folder knowledge_base tidak ditemukan di: {kb_path}\n"
            f"Pastikan folder '{kb_path}' berisi setidaknya satu berkas "
            f"(.txt / .md / .pdf / .csv)."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )

    all_documents: list[Document] = []
    file_list = sorted(kb_path.glob("*.*"))

    logger.info("[Loader] Memindai %d berkas di %s ...", len(file_list), kb_path)

    for file_path in file_list:
        if file_path.name.startswith("05_") or "daftar_pertanyaan" in file_path.name:
            logger.debug("  [SKIP] Mengabaikan file contoh pertanyaan: %s", file_path.name)
            continue

        ext = file_path.suffix.lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            logger.debug("  [SKIP] Format tidak didukung: %s", file_path.name)
            continue

        if ext in (".txt", ".md"):
            docs = _load_text_file(file_path, splitter)
        elif ext == ".pdf":
            docs = _load_pdf_file(file_path, splitter)
        elif ext == ".csv":
            docs = _load_csv_file(file_path)
        else:
            docs = []

        all_documents.extend(docs)

    logger.info(
        "[Loader] Total %d chunk/dokumen dimuat dari %d berkas di knowledge_base.",
        len(all_documents),
        sum(1 for f in file_list if f.suffix.lower() in _SUPPORTED_EXTENSIONS),
    )

    return all_documents, "knowledge_base"


def calculate_kb_hash(kb_dir: str) -> str:
    """
    Menghitung hash MD5 gabungan dari seluruh isi folder knowledge_base.

    Digunakan oleh dependencies.py untuk mendeteksi perubahan dataset
    dan memutuskan apakah ChromaDB perlu di-rebuild ulang.

    Args:
        kb_dir: path direktori utama dataset.

    Returns:
        String heksadesimal MD5 gabungan.
    """
    kb_path = Path(kb_dir) / "knowledge_base"
    if not kb_path.exists():
        return ""
    return _hash_directory(kb_path)
