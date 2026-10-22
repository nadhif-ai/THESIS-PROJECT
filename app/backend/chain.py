import logging
import time
from typing import Optional
from dataclasses import dataclass, field
from langsmith import traceable, get_current_run_tree
from app.admin import store
from app.backend.models import get_llm
from app.backend.prompt_template import get_chat_prompt, format_context, prompt_snapshot
from app.backend.history import bounded_history, retrieval_question
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_FAQ_FILTER = None

_GREETINGS = {
    # Standar & Variasi Halo / Hi
    "halo",
    "halo kak",
    "halo min",
    "halo admin",
    "halo mas",
    "halo mba",
    "halo mbak",
    "halo gan",
    "halo sis",
    "halo bos",
    "hi",
    "hi kak",
    "hi min",
    "hi admin",
    "hi mas",
    "hi mba",
    "hi gan",
    "hi sis",
    "hai",
    "hai kak",
    "hai min",
    "hai admin",
    "hai mas",
    "hai mba",
    "hai gan",
    "hai sis",
    "helo",
    "hello",
    "hei",
    "hey",
    "hoy",
    # Sebutan / Panggilan
    "kak",
    "kakak",
    "min",
    "admin",
    "mas",
    "mba",
    "mbak",
    "bang",
    "bg",
    "kk",
    "bos",
    "bu",
    "pak",
    "gan",
    "sis",
    "bro",
    "sis/gan",
    "gan/sis",
    # Tes & Panggilan Singkat
    "p",
    "ping",
    "tes",
    "test",
    "testing",
    "tes tes",
    "permisi",
    "permisi kak",
    "permisi min",
    "spada",
    "misi",
    "misi kak",
    # Salam Waktu & Variasinya
    "pagi",
    "pagi kak",
    "pagi min",
    "pagi admin",
    "pagi mas",
    "pagi mba",
    "siang",
    "siang kak",
    "siang min",
    "siang admin",
    "siang mas",
    "siang mba",
    "sore",
    "sore kak",
    "sore min",
    "sore admin",
    "sore mas",
    "sore mba",
    "malam",
    "malam kak",
    "malam min",
    "malam admin",
    "malam mas",
    "malam mba",
    "selamat pagi",
    "selamat siang",
    "selamat sore",
    "selamat malam",
    "met pagi",
    "met siang",
    "met sore",
    "met malam",
    "sugeng enjang",
    "sugeng siang",
    "sugeng sore",
    "sugeng dalu",
    # Salam Keagamaan & Variasinya
    "assalamualaikum",
    "assalamu'alaikum",
    "assalamu'alaikum wr wb",
    "assalamualaikum wr wb",
    "assalamualaikum wr. wb.",
    "ass",
    "askum",
    "assalam",
    "syalom",
    "shalom",
    # Navigasi & Bantuan
    "start",
    "menu",
    "bantuan",
    "layanan",
    "info",
    "help",
    "bantu",
    "fitur",
    "menu utama",
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
}

_RESET_RESPONSE_TEXT = "Kita mulai pembahasan baru, Kak. Konteks percakapan sebelumnya tidak dipakai lagi."


def clear_session_history(session_id: str) -> bool:
    return store.clear_session(session_id)


def clear_all_session_histories() -> int:
    sessions = {row["session_id"] for row in store.conversations(limit=10000)}
    for session in sessions:
        store.clear_session(session)
    return len(sessions)


# Peta angka menu ke file knowledge base & label kategorinya (Data-Driven)
_MENU_MAP = {
    "1": ("02_spesifikasi_bahan_dan_finishing.txt", "Penjelasan Bahan Cetak"),
    "2": ("03_panduan_berkas_siap_cetak.txt", "Cara Pemrosesan File"),
    "3": ("01_sop_dan_kebijakan_toko.txt", "Standar Operasional Toko"),
    "4": ("04_daftar_estimasi_harga.txt", "Estimasi Harga Produk"),
}

def _format_history_for_prompt(session_id: str, channel=None):
    return bounded_history(store.prompt_turns(session_id, channel))


def get_all_chat_logs() -> list[dict]:
    return store.conversations()


def _trace_inputs(inputs):
    return {
        key: inputs.get(key) for key in ("question", "channel", "namespace", "top_k")
    }


def _trace_outputs(output):
    if output is None:
        return {}
    return {
        "answer": output.answer,
        "sources": output.sources,
        "retrieval_context": output.retrieval_context,
        "usage": output.usage,
        "latency_seconds": output.latency_seconds,
        "error": output.error,
        "prompt_sha256": output.prompt_sha256,
    }


def _load_menu_from_file(category_number: str, label: str, kb_dir: str, raw: str | None = None) -> str:
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
        raw = faq_file.read_text(encoding="utf-8") if raw is None else raw
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
    return (
        f"*{label}*\n\n"
        f"Contoh pertanyaan:\n{contoh}\n\n"
        "Ketik pertanyaan langsung, atau ketik *menu* untuk pilihan lain."
    )


_WELCOME_GREETING_TEXT = """Halo, Sahabat Asia! 👋

Selamat datang di chatbot CV. Asia Visual Grafika. Saya bisa membantu Kakak mencari informasi dan menyiapkan kebutuhan cetak.

Mau cari informasi tentang apa?
1. Bahan cetak dan kegunaannya
2. Cara menyiapkan file untuk dicetak
3. Informasi toko dan ketentuan pemesanan
4. Estimasi harga produk

Ketik angka 1, 2, 3, atau 4 untuk melihat contoh pertanyaan, atau langsung ceritakan kebutuhan Kakak. Misalnya: “Mau cetak label makanan 50 pcs, cocoknya pakai bahan apa?”

Ketik *menu* untuk melihat pilihan ini lagi, atau *reset* untuk memulai pembahasan baru tanpa memakai konteks sebelumnya."""
_MENU_TEXT = """Pilih contoh pertanyaan:
1. Bahan cetak
2. Persiapan file
3. Kebijakan toko
4. Estimasi harga

Ketik angka 1 sampai 4, atau langsung tulis pertanyaan.
Ketik *reset* untuk memulai pembahasan baru tanpa memakai konteks sebelumnya."""
_HELP_COMMANDS = {"start", "menu", "bantuan", "help", "fitur", "menu utama", "layanan", "info"}
_THANKS = {"makasih", "makasih min", "makasih kak", "terima kasih", "terimakasih", "thanks", "thank you", "tks"}
_ACKNOWLEDGEMENTS = {"oke", "ok", "okay", "siap", "baik", "sip", "oke kak", "oke min", "siap kak"}


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
    retrieval_context: list[dict] = field(default_factory=list)
    latency_seconds: float = 0
    trace_id: Optional[str] = None
    trace_url: Optional[str] = None
    error: Optional[str] = None
    prompt_sha256: Optional[str] = None
    media_selection: Optional[dict] = None
    media_decision: Optional[dict] = None
    media_context: Optional[dict] = None


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
        self.prompt_fingerprint = prompt_snapshot()["sha256"]
        self.settings = get_settings()
        logger.info("RAGChain initialized (Naive mode).")

    @traceable(
        name="rag-answer", process_inputs=_trace_inputs, process_outputs=_trace_outputs
    )
    def run(
        self,
        question: str,
        session_id: str,
        intent_filter: Optional[str] = None,
        namespace: Optional[str] = None,
        channel: str = "api",
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        prompt_config: Optional[dict] = None,
        history_turns: Optional[list] = None,
        media_conversation_key: Optional[str] = None,
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

        catalog_data = None
        media_context = None
        if channel in ('whatsapp', 'playground'):
            from app.admin import catalog
            catalog_data = catalog.snapshot()
            if catalog_data['enabled']:
                media_context = store.catalog_context(
                    media_conversation_key or channel + ':' + session_id,
                    reset=cleaned_query in _RESET_COMMANDS,
                )
        if cleaned_query in _RESET_COMMANDS:
            clear_session_history(session_id)
            history = []
        else:
            history = (
                bounded_history(history_turns)
                if history_turns is not None
                else _format_history_for_prompt(session_id, channel)
            )

        shortcut = None
        if cleaned_query in _HELP_COMMANDS:
            shortcut = (_MENU_TEXT, "Menu")
        elif cleaned_query in _THANKS:
            shortcut = ("Sama-sama, Kak! 😊", "Acknowledgement")
        elif cleaned_query in _ACKNOWLEDGEMENTS and not history:
            shortcut = ("Siap, Kak! 👍", "Acknowledgement")
        elif cleaned_query in _GREETINGS:
            greeting = (
                "Halo lagi, Kak! Ada yang ingin ditanyakan atau dilanjutkan?"
                if history else _WELCOME_GREETING_TEXT
            )
            shortcut = (greeting, "Greeting")
        elif cleaned_query in _RESET_COMMANDS:
            shortcut = (_RESET_RESPONSE_TEXT + "\n\n" + _WELCOME_GREETING_TEXT, "Reset")
        if shortcut:
            store.record_conversation(session_id, channel, question, shortcut[0],
                                      latency=time.monotonic() - t_start)
            return RAGResponse(answer=shortcut[0], session_id=session_id,
                               answer_source=shortcut[1], sources=[],
                               usage={"prompt_tokens": 0, "completion_tokens": 0})

        active = None
        if self.settings.vector_store == "pinecone":
            from app.admin.global_knowledge import EMPTY_ANSWER
            if namespace:
                active = store.version_info(namespace=namespace)
            else:
                from app.admin.kb_store import active_info
                active = active_info()
            if active is None or active["manifest"].get("empty"):
                response = RAGResponse(answer=EMPTY_ANSWER, session_id=session_id,
                                   answer_source="Empty knowledge", sources=[],
                                   usage={"prompt_tokens": 0, "completion_tokens": 0})
                store.record_conversation(session_id, channel, question, response.answer,
                                          usage=response.usage, latency=time.monotonic() - t_start)
                return response
            namespace = active["namespace"]

        # Penanganan ketikan angka 1-4 → Tampilkan Menu Kategori Data-Driven
        # A numeric reply to a branch/quantity question belongs to that conversation.
        menu_expected = (
            not history
            or history[-1].content == _MENU_TEXT
            or history[-1].content.endswith(_WELCOME_GREETING_TEXT)
        )
        if cleaned_query in _MENU_MAP and menu_expected:
            _, label = _MENU_MAP[cleaned_query]
            menu_dir = self.settings.structured_kb_dir
            menu_raw = None
            if self.settings.vector_store == "pinecone":
                menu_version = active
                menu_raw = menu_version["manifest"].get("menu_text")
                if menu_version["manifest"].get("global_kb") and not menu_raw:
                    return RAGResponse(answer=EMPTY_ANSWER, session_id=session_id,
                                       answer_source="Empty menu", sources=[],
                                       usage={"prompt_tokens": 0, "completion_tokens": 0})
            menu_text = _load_menu_from_file(
                category_number=cleaned_query,
                label=label,
                kb_dir=menu_dir,
                raw=menu_raw,
            )
            logger.info(
                "[Session %s] Menu shortcut '%s' dipilih → KATEGORI_%s dari file 05",
                session_id,
                cleaned_query,
                cleaned_query,
            )
            store.record_conversation(session_id, channel, question, menu_text,
                                      latency=time.monotonic() - t_start)
            return RAGResponse(
                answer=menu_text,
                session_id=session_id,
                answer_source="Menu",
                sources=["05_daftar_pertanyaan_populer.txt"],
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        top_k = top_k or store.get_setting(
            "semantic_top_k", self.settings.semantic_top_k
        )
        model = model or store.get_setting(
            "openrouter_model", self.settings.openrouter_model
        )
        selected_version = None
        if self.settings.vector_store == "pinecone":
            selected_version = active
            from app.backend.vectorstore import require_compatible_version

            require_compatible_version(selected_version)
            if selected_version:
                namespace = selected_version["namespace"]
        tree = get_current_run_tree()
        if tree:
            tree.add_metadata(
                {
                    "channel": channel,
                    "model": model,
                    "top_k": top_k,
                    "namespace": namespace,
                    "knowledge_version": selected_version["id"]
                    if selected_version
                    else None,
                    "backend": self.settings.vector_store,
                    "embedding": selected_version["manifest"].get("embedding") if selected_version else None,
                    "vector_index": selected_version["manifest"].get("vector_index") if selected_version else None,
                }
            )

        if isinstance(intent_filter, str):
            faq_filter = {"intent_type": intent_filter}
        else:
            faq_filter = intent_filter if intent_filter else _FAQ_FILTER

        from app.admin.prompt_settings import active_snapshot

        captured_prompt = prompt_config if prompt_config is not None else active_snapshot()
        search_question = retrieval_question(question, history)
        if media_context:
            from app.backend.catalog_selection import products
            current_products = products(question, catalog_data['assets'])
            if current_products and current_products != media_context['focus']:
                search_question = question
        if tree:
            tree.add_metadata({"prompt_sha256": captured_prompt["sha256"],
                               "history_recipe": "eight-pairs-utf8-bound-v1"})

        from app.backend.vectorstore import similarity_search_with_score

        semantic_results = similarity_search_with_score(
            query=search_question,
            k=top_k,
            namespace=namespace,
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
                k=top_k,
                namespace=namespace,
                filter_dict=None,
            )
            for doc, distance in semantic_results:
                doc.metadata["similarity_score"] = float(distance)
            retrieved_docs = [doc for doc, _ in semantic_results]

        media_url = None
        if retrieved_docs and not (catalog_data and catalog_data['enabled']):
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
        generation_error = None

        try:
            prompt_value = get_chat_prompt(captured_prompt).format_messages(
                context=context_str,
                history=history,
                question=question,
            )
            response = get_llm(model).invoke(prompt_value)
            answer = response.content if hasattr(response, "content") else str(response)
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("The answering provider returned no usable text.")
            from app.integrations.waha import plain_text
            answer = plain_text(answer)
            if not answer:
                raise ValueError("The answering provider returned no usable text.")

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
            generation_error = (
                "The answering provider failed. Check model access and retry."
            )
            answer = "Maaf kak, terjadi kesalahan teknis saat memproses pertanyaan. Silakan coba lagi atau hubungi admin langsung ya"

        # Simpan giliran percakapan ini ke histori sesi untuk konteks berikutnya
        total_elapsed = time.monotonic() - t_start
        trace_id = str(tree.id) if tree else None
        trace_url = None
        if tree:
            try:
                trace_url = tree.get_url()
            except Exception:
                pass
        if not generation_error:
            store.record_conversation(
                session_id,
                channel,
                question,
                answer,
                usage_dict,
                total_elapsed,
                trace_id,
            )

        total_elapsed = time.monotonic() - t_start
        logger.info(
            "[Session %s] RAG Selesai dalam %.2fs. Dokumen dirujuk: %s | Usage: %s",
            session_id,
            total_elapsed,
            sources_list,
            usage_dict,
        )

        media_selection = None
        media_decision = {'reason': 'catalog_disabled', 'asset_id': None}
        if media_context and not generation_error:
            from app.backend.catalog_selection import select
            from app.admin.catalog_storage import public_url
            decision = select(question, catalog_data['assets'], [d.page_content for d in retrieved_docs],
                              focus=media_context['focus'], seen=media_context['seen'])
            media_context['next_focus'] = decision['focus']
            if channel == 'playground':
                store.catalog_focus(media_context, decision['focus'], preview_asset=decision['asset'])
            asset = decision['asset']
            media_decision = {'reason': decision['reason'], 'asset_id': asset['asset_id'] if asset else None,
                              'catalog_revision': catalog_data['revision']}
            if asset:
                media_selection = {k: asset[k] for k in ('asset_id','revision','object_key','mime_type','caption','alt_text')}
                media_selection['explicit'] = decision['explicit']
                media_selection['reason'] = decision['reason']
                media_selection['catalog_revision'] = catalog_data['revision']
                media_url = public_url(asset['object_key'])
        return RAGResponse(
            answer=answer,
            session_id=session_id,
            answer_source="naive_rag",
            media_url=media_url,
            sources=sources_list,
            usage=usage_dict,
            retrieval_context=[
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": distance,
                    "similarity": 1 - distance,
                }
                for doc, distance in semantic_results
            ],
            latency_seconds=round(total_elapsed, 3),
            trace_id=trace_id,
            trace_url=trace_url,
            error=generation_error,
            prompt_sha256=captured_prompt["sha256"],
            media_selection=media_selection,
            media_decision=media_decision,
            media_context=media_context,
        )
