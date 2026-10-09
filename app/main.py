import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat_router, admin_router
from app.dependencies import initialize_rag_system, start_kb_watcher
from app.config.settings import get_settings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Mengelola siklus hidup aplikasi FastAPI (startup dan shutdown).

    Pada fase startup: menginisialisasi seluruh pipeline RAG termasuk
    memuat model embedding, menghubungkan ke ChromaDB, dan menyiapkan RAGChain.
    Pada fase shutdown: mencatat log bahwa aplikasi berhenti dengan bersih.

    Args:
        app: instance aplikasi FastAPI.
    """
    logger.info("FastAPI Application Lifespan: Starting up...")
    try:
        initialize_rag_system()
        start_kb_watcher()
        logger.info("Lifespan Startup: RAG system initialized successfully.")
    except Exception as e:
        logger.critical(f"Startup FAILED: {e}", exc_info=True)
        raise e
    yield
    logger.info("FastAPI Application Lifespan: Shutting down...")


from fastapi.responses import HTMLResponse
from pathlib import Path

settings = get_settings()

app = FastAPI(
    title="Chatbot Informasi CV. Asia Visual Grafika",
    description="REST API Backend untuk Chatbot Informasi Percetakan RAG WhatsApp",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse, tags=["Root"], include_in_schema=False)
async def root():
    """
    Endpoint root untuk menampilkan dashboard utama chatbot RAG dan kalkulator harga.

    Returns:
        HTMLResponse berisi konten dari file index.html.
    """
    index_path = Path(__file__).parent / "frontend" / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>index.html not found</h1>", status_code=404)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))
