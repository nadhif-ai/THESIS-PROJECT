import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat_router, admin_router
from app.dependencies import initialize_rag_system
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
    logger.info("FastAPI Application Lifespan: Starting up...")
    try:
        initialize_rag_system()
        logger.info("Lifespan Startup: RAG system initialized successfully.")
    except Exception as e:
        logger.critical(f"Startup FAILED: {e}", exc_info=True)
        raise e
    from app.integrations import waha

    waha.start()
    try:
        yield
    finally:
        from app.admin import jobs, store

        waha.stop()
        jobs.stop()
        store.close_pool()
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
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from pathlib import Path

assets = Path(__file__).resolve().parent.parent / "frontend/dist/assets"
if assets.exists():
    app.mount("/admin/assets", StaticFiles(directory=assets), name="admin-assets")
app.include_router(chat_router)
app.include_router(admin_router)
from app.integrations.waha import router as waha_router

app.include_router(waha_router)


@app.get("/health", tags=["Health"])
def health():
    from app.dependencies import get_rag_chain
    from fastapi import HTTPException

    try:
        get_rag_chain()
    except RuntimeError:
        raise HTTPException(503, "RAG is not ready.")
    return {"status": "ready", "backend": settings.vector_store}


@app.get("/", response_class=HTMLResponse, tags=["Root"], include_in_schema=False)
async def root():
    """
    Endpoint root untuk menampilkan dashboard utama chatbot RAG dan kalkulator harga.

    Returns:
        HTMLResponse berisi konten dari file index.html.
    """
    from fastapi.responses import RedirectResponse

    return RedirectResponse("/admin/")

from app.admin.store import StateUnavailable
from fastapi.responses import JSONResponse


@app.exception_handler(StateUnavailable)
async def state_unavailable(request, error):
    return JSONResponse({"detail": "Chatbot is temporarily unavailable. Please try again later."},
                        status_code=503, headers={"Retry-After": "5"})
