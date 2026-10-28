import os
import logging
import time
from typing import Optional
from dataclasses import dataclass, field
from langsmith import trace, traceable, get_current_run_tree
from app.admin import store
from app.backend.models import answer_defaults, answer_selection, get_llm
from app.backend.prompt_template import get_chat_prompt, format_context, prompt_snapshot
from app.backend.history import bounded_history, retrieval_question
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@traceable(name="product-intent")
def _extract_product_intent(*args, **kwargs):
    from app.backend import product_intent
    return product_intent.extract(*args, **kwargs)


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
        intent_model: Optional[str] = None,
        prompt_config: Optional[dict] = None,
        history_turns: Optional[list] = None,
        media_conversation_key: Optional[str] = None,
        model_provider: Optional[str] = None,
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
        with trace("catalog-context", inputs={"channel": channel}):
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
        empty_knowledge = False
        if self.settings.vector_store == "pinecone":
            from app.admin.global_knowledge import EMPTY_ANSWER
            with trace("knowledge-version", inputs={"namespace": namespace}):
                if namespace:
                    active = store.version_info(namespace=namespace)
                else:
                    from app.admin.kb_store import active_info
                    active = active_info()
                empty_knowledge = active is None or active["manifest"].get("empty")
            if empty_knowledge and not media_context:
                response = RAGResponse(answer=EMPTY_ANSWER, session_id=session_id,
                                   answer_source="Empty knowledge", sources=[],
                                   usage={"prompt_tokens": 0, "completion_tokens": 0})
                store.record_conversation(session_id, channel, question, response.answer,
                                          usage=response.usage, latency=time.monotonic() - t_start)
                return response
            namespace = active["namespace"] if active else None

        # Penanganan ketikan angka 1-4 → Tampilkan Menu Kategori Data-Driven
        # A numeric reply to a branch/quantity question belongs to that conversation.
        menu_expected = (
            not history
            or history[-1].content == _MENU_TEXT
            or history[-1].content.endswith(_WELCOME_GREETING_TEXT)
        )
        if cleaned_query in _MENU_MAP and menu_expected and not empty_knowledge:
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

        with trace("runtime-settings", inputs={"model_override": bool(model), "top_k_override": top_k}):
            top_k = top_k or store.get_setting(
                "semantic_top_k", self.settings.semantic_top_k
            )
            if not model:
                answer_config = store.get_settings_values(answer_defaults(self.settings))
                if model_provider is not None:
                    answer_config["answer_provider"] = model_provider
                model_provider, model = answer_selection(answer_config)
            else:
                model_provider = model_provider or "openrouter"
        selected_version = None
        if self.settings.vector_store == "pinecone":
            selected_version = active
            from app.backend.vectorstore import require_compatible_version

            if not empty_knowledge:
                require_compatible_version(selected_version)
            if selected_version:
                namespace = selected_version["namespace"]
        tree = get_current_run_tree()
        if tree:
            tree.add_metadata(
                {
                    "channel": channel,
                    "model": model,
                    "model_provider": model_provider,
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
        from app.backend import product_intent
        from app.admin.catalog import PRODUCTS
        intent_started = time.monotonic()
        intent_history = bounded_history(store.prompt_turns(session_id, channel, max_age_hours=24)) if media_context and history_turns is None else history
        visual_vocabulary = {}
        for catalog_asset in (catalog_data or {}).get('assets', []):
            for name, values in catalog_asset.get('visual_attributes', {}).items():
                visual_vocabulary[name] = sorted(set(visual_vocabulary.get(name, []) + values))
        intent_model = intent_model or store.get_setting("product_intent_model", self.settings.product_intent_model)
        intent = _extract_product_intent(question, intent_history, (media_context or {}).get('focus', []),
                                         visual_vocabulary=visual_vocabulary, model=intent_model)
        intent_latency = round(time.monotonic() - intent_started, 3)
        needs_knowledge = product_intent.requires_knowledge(question, intent)
        if tree:
            tree.add_metadata({"needs_knowledge": needs_knowledge,
                               "intent_needs_knowledge": intent.needs_knowledge,
                               "retrieval_reason": 'business_evidence' if needs_knowledge else 'social_message'})
        requested_image = intent.resolution == 'resolved' and intent.action != 'none'
        media_response = requested_image or intent.resolution == 'failed' or (intent.action != 'none' and intent.resolution != 'resolved')
        if empty_knowledge and not requested_image:
            intent_usage = {k: intent._usage.get(k, 0) for k in ('prompt_tokens', 'completion_tokens')}
            store.record_conversation(session_id, channel, question, EMPTY_ANSWER, usage=intent_usage,
                                      latency=time.monotonic() - t_start)
            return RAGResponse(answer=EMPTY_ANSWER, session_id=session_id,
                               answer_source='Empty knowledge', sources=[],
                               usage=intent_usage)
        retrieval_history = [] if intent.resolution == 'resolved' and intent.changes_product else history
        search_question = retrieval_question(question, retrieval_history)
        if intent.resolution == 'resolved' and intent.product_ids:
            labels = ', '.join(PRODUCTS[p][0] for p in intent.product_ids)
            search_question += '\nProduk yang dimaksud: ' + labels
        if requested_image:
            search_question += '\nHarga dan detail bahan, ukuran, serta pilihan produk yang diminta.'
        if tree:
            tree.add_metadata({"prompt_sha256": captured_prompt["sha256"],
                               "history_recipe": "eight-pairs-utf8-bound-v1"})

        from app.backend.vectorstore import similarity_search_with_score

        retrieval_recovery = False
        semantic_results = [] if empty_knowledge or not needs_knowledge else similarity_search_with_score(
            query=search_question,
            k=top_k,
            namespace=namespace,
            filter_dict=faq_filter,
        )

        for doc, distance in semantic_results:
            if distance is not None:
                doc.metadata["similarity_score"] = float(distance)

        retrieved_docs = [doc for doc, _ in semantic_results]

        if not retrieved_docs and not empty_knowledge and needs_knowledge and faq_filter:
            logger.warning(
                "[Session %s] Dokumen tidak ditemukan, cari tanpa filter.", session_id
            )
            retrieval_recovery = True
            semantic_results = similarity_search_with_score(
                query=search_question,
                k=top_k,
                namespace=namespace,
                filter_dict=None,
            )
            for doc, distance in semantic_results:
                if distance is not None:
                    doc.metadata["similarity_score"] = float(distance)
            retrieved_docs = [doc for doc, _ in semantic_results]

        media_url = None
        if requested_image and retrieved_docs and not (catalog_data and catalog_data['enabled']):
            for doc in retrieved_docs:
                url = doc.metadata.get('media_url')
                if url and str(url).strip():
                    media_url = str(url).strip()
                    break
        media_selection = None
        media_decision = {'reason': 'catalog_disabled', 'asset_id': None,
                          'retrieval_reason': 'empty_knowledge' if empty_knowledge else 'business_evidence' if needs_knowledge else 'social_message',
                          'retrieval_recovery': retrieval_recovery,
                          'product_ids': intent.product_ids, 'intent_resolution': intent.resolution,
                          'intent_latency_seconds': intent_latency, 'intent_model': intent_model,
                          'intent_prompt_sha256': product_intent.PROMPT_SHA256,
                          'application_version': os.getenv('VERCEL_GIT_COMMIT_SHA', 'local')}
        if media_url:
            media_selection = {'kind': 'knowledge', 'explicit': True, 'reason': 'explicit_example',
                               'alt_text': 'Gambar referensi produk dari knowledge.',
                               'caption': 'Ilustrasi produk terkait pertanyaan Kakak.'}
        if media_context:
            from app.backend.product_image_selection import select
            from app.admin.catalog_storage import public_url
            decision = select(intent, catalog_data['assets'], focus=media_context['focus'])
            media_context['next_focus'] = decision['focus']
            asset = decision['asset']
            media_decision = {**media_decision, 'reason': decision['reason'], 'asset_id': asset['asset_id'] if asset else None,
                              'catalog_revision': catalog_data['revision'], 'product_ids': intent.product_ids,
                              'intent_resolution': intent.resolution, 'intent_latency_seconds': intent_latency}
            if asset:
                media_selection = {k: asset[k] for k in ('asset_id','revision','object_key','mime_type','caption','alt_text')}
                media_selection['kind'] = 'catalog'
                media_selection['explicit'] = decision['explicit']
                media_selection['reason'] = decision['reason']
                media_selection['catalog_revision'] = catalog_data['revision']
                media_url = public_url(asset['object_key'])
        media_prompt = []
        if media_response:
            from langchain_core.messages import SystemMessage
            from app.admin.catalog import PRODUCTS
            if media_selection and media_selection.get('kind') == 'catalog':
                labels = [PRODUCTS[p][0] for p in decision['focus']]
                state = 'Ilustrasi katalog terpilih: ' + ', '.join(labels) + '.'
            elif media_url:
                state = 'Gambar referensi dari knowledge tersedia untuk dilampirkan.'
            else:
                state = 'Tidak ada gambar yang dipilih. Alasan: ' + media_decision['reason'] + '.'
                if intent.resolution != 'resolved':
                    state += ' Maksud/produk belum pasti. Jangan menyatakan gambar tidak tersedia di katalog. Jawab bagian yang jelas, lalu minta klarifikasi singkat bila perlu.'
            media_prompt = [SystemMessage(content=(
                'STATUS LAMPIRAN TERVERIFIKASI (kontrol aplikasi, bukan sumber harga): ' + state +
                ' Jika ilustrasi terpilih, aplikasi akan mengirim gambar dahulu, lalu jawaban teks Anda sebagai pesan terpisah. '
                'Tulis hanya detail produk. Status lampiran dan keterangan ilustrasi ditambahkan aplikasi. Jangan membahas tersedia/tidaknya foto, menjanjikan pengiriman, membuat URL, atau mengklaim gambar sudah diterima. '
                'Berikan harga dan detail produk relevan secara ringkas dari KONTEKS KNOWLEDGE, meskipun pelanggan hanya meminta gambar. '
                'Jika harga pasti bergantung pada ukuran/bahan yang belum dipilih, jelaskan opsi yang tersedia atau tanyakan detail yang diperlukan; jangan menebak. '
                'Jika tidak ada gambar terpilih, jelaskan keterbatasan yang sebenarnya atau klarifikasi produknya, tanpa menyiratkan ada lampiran. '
                'Gambar katalog adalah ilustrasi, bukan bukti model stok atau varian persis.'
            ))]

        context_str = format_context(retrieved_docs)

        # Ambil daftar nama berkas sumber pengetahuan yang ditarik ChromaDB
        sources_list = [
            doc.metadata.get("source", "")
            for doc in retrieved_docs
            if doc.metadata.get("source")
        ]

        usage_dict = {"prompt_tokens": 0, "completion_tokens": 0}
        generation_error = None
        generated = None

        try:
            prompt_value = get_chat_prompt(captured_prompt).format_messages(
                context=context_str,
                history=history,
                question=question,
                media=media_prompt,
            )
            from app.backend.answer_generation import generate
            generated = generate(get_llm(model, model_provider), prompt_value,
                                 recovery_available=not retrieval_recovery)
            answer = generated['answer']
            usage_dict = generated['usage']
            media_decision['answer_recovery'] = generated['recovery']
            if generated['recovery'] in ('incomplete', 'failed') and not media_response:
                generation_error = 'The answering provider did not complete its answer within the recovery limit.'

        except Exception as e:
            logger.error("[Session %s] Answer provider failed: %s", session_id, type(e).__name__)
            generation_error = (
                "The answering provider failed. Check model access and retry."
            )
            answer = "Maaf kak, terjadi kesalahan teknis saat memproses pertanyaan. Silakan coba lagi atau hubungi admin langsung ya"

        validation_usage = {}
        truncated_answer = not generation_error and generated['recovery'] in ('incomplete', 'failed')
        if not generation_error and media_response:
            from app.backend import attachment_answer
            if truncated_answer or not attachment_answer.consistent(answer, selected=bool(media_url),
                    reason=media_decision['reason'], evidence=context_str, plan={
                        'product_ids': intent.product_ids, 'view': intent.view,
                        'exact_visual': intent.exact_visual,
                        'verified_attributes': decision['asset'].get('visual_attributes', {}) if media_context and decision['asset'] else {}}, metrics=validation_usage, model=intent_model):
                answer = attachment_answer.fallback(bool(media_url), media_decision['reason'])
                media_decision['answer_validation'] = 'safe_fallback'
            else:
                media_decision['answer_validation'] = 'passed'

        answer_usage = dict(usage_dict, model=model, provider=model_provider,
                            finish_reason=generated['finish_reason'] if generated else 'error')
        stage_usage = {'intent': intent._usage, 'answer': answer_usage, 'validation': validation_usage}
        media_decision['model_usage'] = stage_usage
        usage_dict = {key: sum(stage.get(key, 0) for stage in stage_usage.values())
                      for key in ('prompt_tokens', 'completion_tokens')}
        if media_selection:
            media_selection['decision'] = dict(media_decision)
        if not generation_error and media_response and intent.resolution != 'failed':
            answer = attachment_answer.explanation(bool(media_url), media_decision['reason'],
                [PRODUCTS[p][0] for p in intent.product_ids]) + '\n\n' + answer

        if generation_error:
            media_url = None
            media_selection = None
            media_decision = {'reason': 'generation_error', 'asset_id': None}
            if media_context:
                media_context.pop('next_focus', None)
        elif media_context and channel == 'playground':
            store.catalog_focus(media_context, decision['focus'], preview_asset=decision['asset'])

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
                {**usage_dict, "image_decision": media_decision},
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
                    "similarity": 1 - distance if distance is not None else None,
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
