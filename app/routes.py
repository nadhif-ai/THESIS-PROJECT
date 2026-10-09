import csv
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

logger       = logging.getLogger(__name__)
chat_router   = APIRouter(prefix="/chat")

_ROOT      = Path(__file__).parent.parent
_DATA_DIR  = _ROOT / "dataset"


class ChatFaqRequest(BaseModel):
    """
    Skema data request untuk endpoint tanya-jawab FAQ chatbot.

    Attributes:
        session_id      : ID unik sesi pengguna untuk membedakan percakapan.
        question        : teks pertanyaan yang dikirimkan pengguna.
        product_context : konteks produk opsional untuk memperkaya pertanyaan.
    """
    session_id:      str
    question:        str
    product_context: Optional[str] = None


class ResetChatRequest(BaseModel):
    """
    Skema data request untuk mereset riwayat percakapan sesi.
    """
    session_id: str


class ChatFaqResponse(BaseModel):
    """
    Skema data response dari endpoint tanya-jawab FAQ chatbot.

    Attributes:
        answer    : teks jawaban yang dihasilkan oleh pipeline RAG.
        source    : label asal jawaban untuk keperluan audit.
        media_url : URL media jika ada gambar/video untuk visualisasi.
        sources   : daftar nama file berkas pengetahuan yang dirujuk ChromaDB.
        usage     : dictionary penggunaan token LLM (prompt_tokens, completion_tokens).
    """
    answer:    str
    source:    str = "chat_router"
    media_url: Optional[str] = None
    sources:   Optional[list[str]] = None
    usage:     Optional[dict] = None


_rag_chain = None


def _get_rag_chain():
    """
    Mengambil instance RAGChain dari modul dependencies secara lazy (saat pertama dibutuhkan).

    Menggunakan pola lazy initialization agar import tidak circular
    dan RAGChain tidak dimuat sebelum sistem siap digunakan.

    Returns:
        Instance RAGChain yang sudah diinisialisasi.
    """
    global _rag_chain
    if _rag_chain is None:
        from app.dependencies import get_rag_chain
        _rag_chain = get_rag_chain()
        logger.info("[ChatRouter] RAGChain initialized.")
    return _rag_chain


@chat_router.post(
    "/reset",
    tags=["1. Chatbot RAG"],
    summary="Reset Riwayat Percakapan / Konteks Percakapan Sesi",
)
async def reset_chat_history(req: ResetChatRequest):
    """
    Endpoint untuk mereset/membersihkan riwayat percakapan aktif dari memori.
    """
    from app.backend.chain import clear_session_history
    was_active = clear_session_history(req.session_id)
    return JSONResponse({
        "status": "success",
        "session_id": req.session_id,
        "message": f"Riwayat percakapan untuk sesi '{req.session_id}' berhasil dibersihkan.",
        "was_active": was_active,
    })


@chat_router.post(
    "/faq",
    response_model=ChatFaqResponse,
    tags=["1. Chatbot RAG"],
    summary="Tanya Jawab FAQ & Hitung Harga RAG",
)
async def chat_faq(req: ChatFaqRequest) -> ChatFaqResponse:
    """
    Endpoint utama untuk menerima pertanyaan dan mengembalikan jawaban dari pipeline RAG.

    Pertanyaan diproses melalui RAGChain yang mencari dokumen relevan di ChromaDB
    lalu memanggil LLM Gemini untuk merangkum jawaban. Juga memiliki mekanisme
    deteksi prompt injection untuk mencegah kebocoran instruksi sistem.

    Args:
        req: objek ChatFaqRequest berisi session_id dan pertanyaan pengguna.

    Returns:
        ChatFaqResponse berisi jawaban teks dari LLM.

    Raises:
        HTTPException 500: jika pipeline RAG gagal dieksekusi.
    """
    logger.info(
        "[ChatRouter/faq] session=%s question=%r", req.session_id, req.question[:60]
    )

    question = req.question
    if req.product_context:
        question = f"{req.question} [konteks produk: {req.product_context}]"

    _PROMPT_LEAK_MARKERS = [
        "HANYA boleh diberikan jika SEMUA",
        "WAJIB tanya dulu",
        "TUGAS UTAMA",
        "SUMBER JAWABAN",
        "ATURAN PERHITUNGAN HARGA",
        "FINAL VALIDATION",
    ]

    try:
        chain    = _get_rag_chain()
        response = chain.run(
            question=question,
            session_id=req.session_id,
            intent_filter=None,
            
        )
        answer = response.answer

        if any(marker in answer for marker in _PROMPT_LEAK_MARKERS):
            logger.error(
                "[ChatRouter/faq] PROMPT LEAK DETECTED session=%s", req.session_id
            )
            answer = "Maaf kak, admin sedang gangguan teknis. Bisa diulangi?"

        return ChatFaqResponse(
            answer=answer,
            source="chat_routes/faq/rag_chain",
            media_url=response.media_url,
            sources=response.sources,
            usage=response.usage,
        )

    except Exception as e:
        logger.error("[ChatRouter/faq] Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/questions", include_in_schema=False)
async def get_faq_questions(category: str):
    """
    Mengambil daftar pertanyaan FAQ berdasarkan kategori intent dari dataset CSV.

    Args:
        category: nama kategori intent, contoh 'FAQ' atau 'EDUKASI'.

    Returns:
        JSON berisi daftar pertanyaan (id dan judul) sesuai kategori, maksimal 8 item.
    """
    rows = _read_csv("faq_kb.csv")
    questions = [
        {"id": row["doc_id"].strip(), "title": row["title"].strip()}
        for row in rows
        if row.get("intent_type", "").strip() == category
    ]
    return {"questions": questions[:8]}


@chat_router.get("/question/{doc_id}", include_in_schema=False)
async def get_faq_question_by_id(doc_id: str):
    """
    Mengambil judul pertanyaan FAQ berdasarkan ID dokumen tertentu.

    Args:
        doc_id: ID unik dokumen FAQ, contoh 'FAQ-001'.

    Returns:
        JSON berisi judul pertanyaan yang sesuai.

    Raises:
        HTTPException 404: jika doc_id tidak ditemukan di dataset.
    """
    rows = _read_csv("faq_kb.csv")
    for row in rows:
        if row["doc_id"].strip() == doc_id:
            return {"title": row["title"].strip()}
    raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")


def _read_csv(filename: str) -> list[dict]:
    """
    Membaca file CSV dari folder dataset dan mengembalikannya sebagai daftar kamus.

    Args:
        filename: nama file CSV, contoh 'faq_kb.csv'.

    Returns:
        Daftar baris CSV dalam format dict, atau list kosong jika file tidak ditemukan.
    """
    path = _DATA_DIR / filename
    if not path.exists():
        logger.warning("CSV tidak ditemukan: %s", path)
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ===========================================================================
# FONNTE WHATSAPP WEBHOOK — Terisolasi dari sistem Telegram Bot
# ===========================================================================
import os as _os
import re as _re
import requests as _requests
from fastapi import Form, BackgroundTasks

_FONNTE_TOKEN   = _os.getenv("FONNTE_TOKEN", "")
_FONNTE_API_URL = "https://api.fonnte.com/send"


def _send_whatsapp_reply(to: str, message: str, media_url: Optional[str] = None) -> None:
    """Mengirim balasan ke WhatsApp via Fonnte API."""
    from app.config.settings import get_settings
    token = get_settings().fonnte_token.strip()
    if not token:
        logger.warning("[Fonnte] FONNTE_TOKEN tidak ada di .env — balasan tidak terkirim.")
        return

    payload = {"target": to, "message": message}

    try:
        resp = _requests.post(
            _FONNTE_API_URL,
            headers={"Authorization": token},
            data=payload,
            timeout=15,
        )
        logger.info("[Fonnte] Balasan terkirim ke %s → HTTP %s", to, resp.status_code)
    except Exception as e:
        logger.error("[Fonnte] Gagal mengirim balasan ke %s: %s", to, e)



@chat_router.get("/media/gdrive/{file_id}.jpg", include_in_schema=False)
async def get_gdrive_media_proxy(file_id: str):
    """
    Proxy endpoint untuk mengalirkan file gambar dari Google Drive langsung
    ke Fonnte API dengan header Content-Type image/jpeg dan ekstensi .jpg.
    """
    import requests
    from fastapi.responses import Response
    url = f"https://lh3.googleusercontent.com/d/{file_id}"
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        if r.status_code == 200:
            return Response(content=r.content, media_type="image/jpeg")
    except Exception as e:
        logger.error("Failed to proxy gdrive media: %s", e)
    raise HTTPException(status_code=404, detail="Media tidak ditemukan")



@chat_router.api_route(
    "/whatsapp",
    methods=["GET", "POST"],
    tags=["2. Integrasi WhatsApp"],
    summary="Pesan Masuk & Verification Webhook WhatsApp",
)
async def fonnte_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Endpoint Webhook WhatsApp via Fonnte (Fleksibel JSON & Form Data + Support Foto/Media).
    """
    sender  = None
    message = None
    name    = ""

    if request.method == "POST":
        try:
            body_json = await request.json()
            if isinstance(body_json, dict):
                sender  = str(body_json.get("sender")  or body_json.get("from") or "").strip()
                message = str(body_json.get("message") or body_json.get("text") or "").strip()
                name    = str(body_json.get("name", "")).strip()
        except Exception:
            pass

        if not sender or not message:
            try:
                form = await request.form()
                sender  = str(form.get("sender")  or form.get("from") or "").strip()
                message = str(form.get("message") or form.get("text") or "").strip()
                name    = str(form.get("name", "")).strip()
            except Exception:
                pass

    if not sender or not message:
        logger.info("[Fonnte/WA] Ping GET/Verification received — status OK")
        return {"status": "ok", "service": "Fonnte WhatsApp Webhook", "rag": "ready"}

    question = message.strip()
    if not question:
        return {"status": "ignored", "reason": "empty message"}

    logger.info("[Fonnte/WA] Pesan dari %s (%s): %r", sender, name or "unknown", question[:80])
    session_id = f"wa_{sender}"

    def _process_and_reply():
        try:
            chain        = _get_rag_chain()
            response     = chain.run(question=question, session_id=session_id)
            answer_plain = _re.sub(r"<[^>]+>", "", response.answer).strip()

            # Kirim balasan teks beserta foto/media_url jika tersedia dari dokumen RAG
            _send_whatsapp_reply(to=sender, message=answer_plain, media_url=response.media_url)
        except Exception as e:
            logger.error("[Fonnte/WA] Error dari %s: %s", sender, e)
            _send_whatsapp_reply(to=sender, message="Maaf kak, gangguan teknis. Coba lagi ya 🙏")

    background_tasks.add_task(_process_and_reply)
    return {"status": "processing", "sender": sender}


# ===========================================================================
# ADMIN PORTAL ROUTER — Pengelolaan Knowledge Base Karyawan Toko
# ===========================================================================
from fastapi import UploadFile, File

admin_router = APIRouter(prefix="/admin", tags=["3. Kelola Knowledge Base"])


@admin_router.get("", response_class=HTMLResponse, include_in_schema=False)
@admin_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_page():
    admin_path = _ROOT / "app" / "frontend" / "admin.html"
    if not admin_path.exists():
        return HTMLResponse("<h1>admin.html not found</h1>", status_code=404)
    return HTMLResponse(admin_path.read_text(encoding="utf-8"))


class LoginRequest(BaseModel):
    username: str
    password: str


_ADMIN_TOKEN = "asiavisual_admin_secret_token_2026"


@admin_router.post("/api/login", summary="Autentikasi Login Admin Toko")
async def admin_login(req: LoginRequest):
    user = req.username.strip().lower()
    pwd  = req.password.strip()
    # Validasi kredensial resmi admin toko
    if user == "admin" and pwd in ("asiavisual123", "admin123"):
        return JSONResponse({"status": "success", "token": _ADMIN_TOKEN})
    return JSONResponse({"status": "error", "message": "Username atau password salah!"}, status_code=401)



@admin_router.get("/api/chat-logs", summary="Lihat Seluruh Riwayat Chat Log Pelanggan")
async def get_chat_logs():
    from app.backend.chain import get_all_chat_logs
    logs = get_all_chat_logs()
    return JSONResponse({"logs": logs})


@admin_router.get("/api/files", summary="Daftar Berkas Knowledge Base (.txt)")
async def list_kb_files():
    kb_dir = _DATA_DIR / "knowledge_base"
    if not kb_dir.exists():
        return JSONResponse({"files": []})
    files = sorted([f.name for f in kb_dir.glob("*.txt")])
    return JSONResponse({"files": files})


@admin_router.get("/api/file/{filename}", include_in_schema=False)
async def get_kb_file(filename: str):
    kb_dir = _DATA_DIR / "knowledge_base"
    file_path = (kb_dir / filename).resolve()
    if not file_path.exists() or not str(file_path).startswith(str(kb_dir.resolve())):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    content = file_path.read_text(encoding="utf-8")
    return JSONResponse({"filename": filename, "content": content})


class SaveFileRequest(BaseModel):
    filename: str
    content: str


@admin_router.post("/api/save", include_in_schema=False)
async def save_kb_file(req: SaveFileRequest):
    kb_dir = _DATA_DIR / "knowledge_base"
    file_path = (kb_dir / req.filename).resolve()
    if not str(file_path).startswith(str(kb_dir.resolve())):
        raise HTTPException(status_code=400, detail="Nama berkas tidak valid")
    file_path.write_text(req.content, encoding="utf-8")
    logger.info("[Admin] Berkas %s berhasil diperbarui via Admin Portal.", req.filename)
    return JSONResponse({"status": "success", "filename": req.filename})


@admin_router.post("/api/upload", include_in_schema=False)
async def upload_kb_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Hanya berkas .txt yang didukung")
    kb_dir = _DATA_DIR / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    file_path = kb_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)
    logger.info("[Admin] Berkas baru %s diupload via Admin Portal.", file.filename)
    return JSONResponse({"status": "success", "filename": file.filename})


class CreateFileRequest(BaseModel):
    filename: str
    content: str = ""


@admin_router.post("/api/create", include_in_schema=False)
async def create_kb_file(req: CreateFileRequest):
    kb_dir = _DATA_DIR / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    fname = req.filename.strip()
    if not fname.lower().endswith(".txt"):
        fname += ".txt"
    file_path = (kb_dir / fname).resolve()
    if not str(file_path).startswith(str(kb_dir.resolve())):
        raise HTTPException(status_code=400, detail="Nama berkas tidak valid")
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Berkas '{fname}' sudah ada")
    file_path.write_text(req.content, encoding="utf-8")
    logger.info("[Admin] Berkas baru '%s' dibuat via Admin Portal.", fname)
    return JSONResponse({"status": "success", "filename": fname})


@admin_router.post("/api/delete/{filename}", include_in_schema=False)
async def delete_kb_file(filename: str):
    kb_dir = _DATA_DIR / "knowledge_base"
    file_path = (kb_dir / filename).resolve()
    if not file_path.exists() or not str(file_path).startswith(str(kb_dir.resolve())):
        raise HTTPException(status_code=404, detail="Berkas tidak ditemukan")
    try:
        file_path.unlink()
        logger.info("[Admin] Berkas %s berhasil dihapus via Admin Portal.", filename)
        return JSONResponse({"status": "success", "filename": filename})
    except Exception as e:
        logger.error("[Admin] Gagal menghapus berkas %s: %s", filename, e)
        raise HTTPException(status_code=500, detail=f"Gagal menghapus berkas: {e}")







