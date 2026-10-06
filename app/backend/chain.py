import logging
import time
from typing import Optional
from dataclasses import dataclass
from app.backend.models import get_llm
from app.backend.prompt_template import get_chat_prompt, format_context
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_FAQ_FILTER = None

_GREETINGS = {
    # Standar & Variasi Halo / Hi
    "halo", "halo kak", "halo min", "halo admin", "halo mas", "halo mba", "halo mbak", "halo gan", "halo sis", "halo bos",
    "hi", "hi kak", "hi min", "hi admin", "hi mas", "hi mba", "hi gan", "hi sis",
    "hai", "hai kak", "hai min", "hai admin", "hai mas", "hai mba", "hai gan", "hai sis",
    "helo", "hello", "hei", "hey", "hoy",

    # Sebutan / Panggilan
    "kak", "kakak", "min", "admin", "mas", "mba", "mbak", "bang", "bg", "kk", "bos", "bu", "pak", "gan", "sis", "bro", "sis/gan", "gan/sis",

    # Tes & Panggilan Singkat
    "p", "ping", "tes", "test", "testing", "tes tes", "permisi", "permisi kak", "permisi min", "spada", "misi", "misi kak",

    # Salam Waktu & Variasinya
    "pagi", "pagi kak", "pagi min", "pagi admin", "pagi mas", "pagi mba",
    "siang", "siang kak", "siang min", "siang admin", "siang mas", "siang mba",
    "sore", "sore kak", "sore min", "sore admin", "sore mas", "sore mba",
    "malam", "malam kak", "malam min", "malam admin", "malam mas", "malam mba",
    "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
    "met pagi", "met siang", "met sore", "met malam",
    "sugeng enjang", "sugeng siang", "sugeng sore", "sugeng dalu",

    # Salam Keagamaan & Variasinya
    "assalamualaikum", "assalamu'alaikum", "assalamu'alaikum wr wb", "assalamualaikum wr wb",
    "assalamualaikum wr. wb.", "ass", "askum", "assalam", "syalom", "shalom",

    # Navigasi & Bantuan
    "start", "menu", "bantuan", "posisi", "layanan", "info", "help", "bantu", "fitur", "menu utama",
}

_RESET_COMMANDS = {
    "reset",
    "clear",
    "/reset",
    "/clear",
    "reset chat",
    "clear history",
    "hapus histori",
    "reset histori",
    "hapus riwayat",
    "reset percakapan",
    "restart",
    "mulai ulang",
    "batal",
}

_RESET_RESPONSE_TEXT = """🔄 *Riwayat percakapan berhasil direset!*

Konteks percakapan sebelumnya telah dibersihkan. Silakan ketik pertanyaan atau topik baru Kakak ya! 😊"""


def clear_session_history(session_id: str) -> bool:
    """
    Menghapus/mereset riwayat percakapan aktif (History-in-Prompt) untuk session_id tertentu.

    Args:
        session_id: ID sesi (misal: nomor WhatsApp pengguna).

    Returns:
        True jika sesi ada di memori histori dan berhasil dihapus, False jika tidak ada.
    """
    if session_id in _chat_history:
        del _chat_history[session_id]
        logger.info("[Session %s] Riwayat percakapan aktif berhasil direset.", session_id)
        return True
    logger.info("[Session %s] Tidak ada riwayat percakapan aktif di memori untuk direset.", session_id)
    return False


def clear_all_session_histories() -> int:
    """
    Menghapus seluruh riwayat percakapan aktif di memori untuk semua sesi.

    Returns:
        Jumlah sesi yang direset.
    """
    count = len(_chat_history)
    _chat_history.clear()
    logger.info("Seluruh riwayat percakapan (%d sesi) telah dibersihkan.", count)
    return count


# Peta angka menu ke file knowledge base & label kategorinya (Data-Driven)
_MENU_MAP = {
    "1": ("02_spesifikasi_bahan_dan_finishing.txt", "Penjelasan Bahan Cetak"),
    "2": ("03_panduan_berkas_siap_cetak.txt", "Cara Pemrosesan File"),
    "3": ("01_sop_dan_kebijakan_toko.txt", "Standar Operasional Toko"),
    "4": ("04_daftar_estimasi_harga.txt", "Estimasi Harga Produk"),
}

# ---------------------------------------------------------------------------
# CONVERSATION HISTORY — History-in-Prompt Strategy
# Menyimpan 2 giliran percakapan terakhir per session_id (nomor WhatsApp).
# Histori disisipkan langsung ke dalam prompt Gemini sehingga LLM dapat
# memahami konteks percakapan tanpa perlu memodifikasi kueri ke ChromaDB.
# Query asli pelanggan selalu dikirim langsung ke ChromaDB tanpa perubahan.
# Referensi: Lewis et al. (2020) RAG; Shi et al. (2023) Context-in-Prompt.
# ---------------------------------------------------------------------------

# Kamus histori percakapan per session: { session_id: [(pertanyaan, jawaban), ...] }
# Hanya menyimpan 2 giliran terakhir untuk menjaga efisiensi token.
_chat_history: dict[str, list[tuple[str, str]]] = {}
_MAX_HISTORY_TURNS = 2


def _format_history_for_prompt(session_id: str) -> str:
    """
    Menyusun blok teks riwayat percakapan untuk disisipkan ke dalam prompt LLM.

    Mengambil maksimal _MAX_HISTORY_TURNS giliran terakhir dari histori sesi
    dan memformatnya menjadi teks dialog yang mudah dipahami LLM.

    Args:
        session_id: ID sesi (nomor WhatsApp) pengguna.

    Returns:
        String teks riwayat percakapan siap sisip ke prompt,
        atau string kosong jika belum ada histori untuk sesi ini.
    """
    history = _chat_history.get(session_id, [])
    if not history:
        return ""
    lines = []
    for q, a in history:
        lines.append(f"Pelanggan: {q}")
        lines.append(f"Bot: {a[:300]}")
    return "\n".join(lines)


import json as _json
import pathlib as _pathlib

_HISTORY_FILE = (
    _pathlib.Path(__file__).resolve().parent.parent.parent
    / "dataset"
    / "admin_chat_history.json"
)


def _load_persisted_chat_logs() -> list[dict]:
    """Memuat riwayat chat yang tersimpan secara permanen di disk."""
    try:
        if _HISTORY_FILE.exists():
            return _json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Gagal memuat persisted chat logs: %s", exc)
    return []


_global_chat_logs: list[dict] = _load_persisted_chat_logs()


def get_all_chat_logs() -> list[dict]:
    """Mengembalikan daftar log percakapan terbaru untuk Portal Admin."""
    return _global_chat_logs


def _update_history(session_id: str, question: str, answer: str) -> None:
    """
    Menyimpan satu giliran percakapan (pertanyaan + jawaban) ke histori sesi dan disk.

    Hanya menyimpan maksimal _MAX_HISTORY_TURNS giliran terakhir agar
    konsumsi token LLM tetap efisien dan tidak membengkak.

    Args:
        session_id: ID sesi (nomor WhatsApp) pengguna.
        question  : Teks pertanyaan asli pengguna pada giliran ini.
        answer    : Teks jawaban bot pada giliran ini.
    """
    history = _chat_history.setdefault(session_id, [])
    history.append((question, answer))
    if len(history) > _MAX_HISTORY_TURNS:
        history.pop(0)

    import datetime

    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": session_id,
        "question": question,
        "answer": answer,
    }
    _global_chat_logs.insert(0, new_entry)
    if len(_global_chat_logs) > 500:
        _global_chat_logs.pop()

    # Simpan secara permanen ke berkas json di disk
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_FILE.write_text(
            _json.dumps(_global_chat_logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Gagal menyimpan riwayat chat ke disk: %s", exc)


def _load_menu_from_file(category_number: str, label: str, kb_dir: str) -> str:
    """
    Membaca file 05_daftar_pertanyaan_populer.txt dan mengekstrak contoh
    pertanyaan pada blok [KATEGORI_X] yang sesuai dengan angka yang dipilih.

    Argumen:
        category_number : angka kategori ("1"–"4") yang diketik pengguna.
        label           : label kategori menu yang ditampilkan ke pengguna.
        kb_dir          : path folder dataset utama (settings.structured_kb_dir).

    Mengembalikan:
        Teks balasan menu berisi contoh pertanyaan siap kirim ke WhatsApp.
    """
    import pathlib

    faq_file = (
        pathlib.Path(kb_dir) / "knowledge_base" / "05_daftar_pertanyaan_populer.txt"
    )
    questions = []
    try:
        raw = faq_file.read_text(encoding="utf-8")
        target_tag = f"[KATEGORI_{category_number}]"
        inside_section = False
        for line in raw.splitlines():
            stripped = line.strip()
            # Masuk ke blok kategori yang tepat
            if stripped == target_tag:
                inside_section = True
                continue
            # Keluar jika menemukan blok kategori lain
            if inside_section and stripped.startswith("[KATEGORI_"):
                break
            if not inside_section:
                continue
            # Lewati baris komentar dan kosong
            if not stripped or stripped.startswith("#"):
                continue
            questions.append(f"• {stripped}")
    except Exception:
        questions = ["• Informasi tersedia, silakan ketik pertanyaan lengkap Kakak."]

    if not questions:
        questions = ["• Informasi tersedia, silakan ketik pertanyaan lengkap Kakak."]

    contoh = "\n".join(questions)
    footer = "\n\n💬 Siap membantu menjawab ya kak😊" if category_number == "4" else ""
    return (
        f"*{label}*\n\n"
        f"Berikut contoh pertanyaan yang bisa Kakak ketik langsung:\n\n"
        f"{contoh}"
        f"{footer}\n\n"
        f"Silakan salin atau ketik pertanyaan Kakak ya! 😊"
    )


_WELCOME_GREETING_TEXT = """Halo Sahabat Asia! 👋

Selamat datang di Chatbot Informasi CV. Asia Visual Grafika.

📌 *Kategori Informasi yang Tersedia:*
1. Penjelasan Bahan Cetak 
2. Cara Pemrosesan File 
3. Standar Operasional Toko 
4. Estimasi Harga Produk

💡 Ketik angka *1*, *2*, *3*, atau *4* untuk melihat contoh pertanyaan setiap kategori.
🔄 Ketik *reset* kapan saja jika ingin mengulang/membersihkan konteks percakapan.

Silakan ketik pertanyaan Kakak secara langsung ya! 😊"""


@dataclass
class RAGResponse:
    """
    Struktur data hasil jawaban dari pipeline RAG.

    Attributes:
        answer        : teks jawaban yang dihasilkan oleh LLM.
        session_id    : ID sesi pengguna untuk pelacakan percakapan.
        answer_source : asal jawaban, contoh 'naive_rag' atau 'Greeting'.
        media_url     : URL media (gambar/video) jika tersemat di dokumen teratas.
        sources       : daftar nama file berkas sumber pengetahuan yang ditarik ChromaDB.
        usage         : dictionary berisi token usage (prompt_tokens, completion_tokens).
    """

    answer: str
    session_id: str
    answer_source: str = "rag"
    media_url: Optional[str] = None
    sources: Optional[list[str]] = None
    usage: Optional[dict] = None


class RAGChain:
    """
    Kelas utama pipeline RAG (Retrieval-Augmented Generation).

    Mengorkestrasi alur kerja lengkap mulai dari penerimaan pertanyaan,
    pencarian dokumen relevan di ChromaDB, pembentukan prompt, hingga
    pemanggilan LLM Gemini untuk menghasilkan jawaban.
    """

    def __init__(self):
        """
        Inisialisasi RAGChain dengan komponen-komponen yang diperlukan.
        """
        self.llm = get_llm()
        self.prompt = get_chat_prompt()
        self.settings = get_settings()
        logger.info("RAGChain initialized (Naive mode).")

    def run(
        self,
        question: str,
        session_id: str,
        intent_filter: Optional[str] = None,
    ) -> RAGResponse:
        """
        Menjalankan pipeline RAG secara penuh untuk menjawab pertanyaan pengguna.
        """
        logger.info("[Session %s] Running Naive RAG for: %r", session_id, question)
        t_start = time.monotonic()

        cleaned_query = (
            question.strip()
            .lower()
            .replace("?", "")
            .replace("!", "")
            .replace(".", "")
            .replace(",", "")
        )

        # Penanganan sapaan awal → Tampilkan Pesan Sambutan Resmi
        if cleaned_query in _GREETINGS:
            return RAGResponse(
                answer=_WELCOME_GREETING_TEXT,
                session_id=session_id,
                answer_source="Greeting",
                sources=[],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        # Penanganan perintah reset percakapan → Hapus konteks & berikan balasan konfirmasi
        if cleaned_query in _RESET_COMMANDS:
            clear_session_history(session_id)
            logger.info("[Session %s] Tombol/perintah reset dipicu pengguna.", session_id)
            return RAGResponse(
                answer=_RESET_RESPONSE_TEXT,
                session_id=session_id,
                answer_source="Reset",
                sources=[],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        # Penanganan ketikan angka 1-4 → Tampilkan Menu Kategori Data-Driven
        if cleaned_query in _MENU_MAP:
            _, label = _MENU_MAP[cleaned_query]
            menu_text = _load_menu_from_file(
                category_number=cleaned_query,
                label=label,
                kb_dir=self.settings.structured_kb_dir,
            )
            logger.info(
                "[Session %s] Menu shortcut '%s' dipilih → KATEGORI_%s dari file 05",
                session_id,
                cleaned_query,
                cleaned_query,
            )
            return RAGResponse(
                answer=menu_text,
                session_id=session_id,
                answer_source="Menu",
                sources=["05_daftar_pertanyaan_populer.txt"],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        if isinstance(intent_filter, str):
            faq_filter = {"intent_type": intent_filter}
        else:
            faq_filter = intent_filter if intent_filter else _FAQ_FILTER

        # Query asli langsung dikirim ke ChromaDB tanpa modifikasi apapun
        # (History-in-Prompt Strategy — konteks ditangani oleh Gemini via prompt)
        search_question = question

        from app.backend.vectorstore import similarity_search_with_score

        semantic_results = similarity_search_with_score(
            query=search_question,
            k=self.settings.semantic_top_k,
            filter_dict=faq_filter,
        )

        for doc, distance in semantic_results:
            doc.metadata["similarity_score"] = float(distance)

        retrieved_docs = [doc for doc, _ in semantic_results]

        if not retrieved_docs:
            logger.warning(
                "[Session %s] Dokumen tidak ditemukan, cari tanpa filter.", session_id
            )
            semantic_results = similarity_search_with_score(
                query=search_question,
                k=self.settings.semantic_top_k,
                filter_dict=None,
            )
            for doc, distance in semantic_results:
                doc.metadata["similarity_score"] = float(distance)
            retrieved_docs = [doc for doc, _ in semantic_results]

        media_url = None
        if retrieved_docs:
            for doc in retrieved_docs:
                url = doc.metadata.get("media_url")
                if url and str(url).strip():
                    media_url = str(url).strip()
                    break

        context_str = format_context(retrieved_docs)

        # Ambil daftar nama berkas sumber pengetahuan yang ditarik ChromaDB
        sources_list = [
            doc.metadata.get("source", "")
            for doc in retrieved_docs
            if doc.metadata.get("source")
        ]

        usage_dict = {"prompt_tokens": 0, "completion_tokens": 0}

        try:
            # Ambil histori percakapan sesi ini untuk disisipkan ke prompt
            history_text = _format_history_for_prompt(session_id)

            prompt_value = self.prompt.format_messages(
                context=context_str,
                history=history_text,
                question=question,
            )
            response = self.llm.invoke(prompt_value)
            answer = response.content if hasattr(response, "content") else str(response)

            # Ekstrak token usage dari response OpenRouter/LangChain jika ada
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage_dict = {
                    "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                    "completion_tokens": response.usage_metadata.get(
                        "output_tokens", 0
                    ),
                }
            elif (
                hasattr(response, "response_metadata")
                and "token_usage" in response.response_metadata
            ):
                tu = response.response_metadata["token_usage"]
                usage_dict = {
                    "prompt_tokens": tu.get("prompt_tokens", 0),
                    "completion_tokens": tu.get("completion_tokens", 0),
                }

        except Exception as e:
            logger.error("[Session %s] Gagal memanggil LLM: %s", session_id, e)
            answer = "Maaf kak, terjadi kesalahan teknis saat memproses pertanyaan. Silakan coba lagi atau hubungi admin langsung ya"

        # Simpan giliran percakapan ini ke histori sesi untuk konteks berikutnya
        _update_history(session_id, question, answer)

        total_elapsed = time.monotonic() - t_start
        logger.info(
            "[Session %s] RAG Selesai dalam %.2fs. Dokumen dirujuk: %s | Usage: %s",
            session_id,
            total_elapsed,
            sources_list,
            usage_dict,
        )

        return RAGResponse(
            answer=answer,
            session_id=session_id,
            answer_source="naive_rag",
            media_url=media_url,
            sources=sources_list,
            usage=usage_dict,
        )
