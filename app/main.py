import os
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat_router, admin_router
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
    # Authentication and webhook intake must not wait for Pinecone or model providers.
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


from fastapi.responses import FileResponse
from app.admin.routes import dashboard
from pathlib import Path

settings = get_settings()

app = FastAPI(
    title="Chatbot Informasi CV. Asia Visual Grafika",
    description="REST API Backend untuk Chatbot Informasi Percetakan RAG WhatsApp",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def admin_timing(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/admin/api/"):
        duration = (time.perf_counter() - started) * 1000
        timing = response.headers.get("Server-Timing")
        total = f"app;dur={duration:.1f}"
        response.headers["Server-Timing"] = f"{timing}, {total}" if timing else total
        response.headers["Cache-Control"] = "private, no-store"
        if duration >= 1000:
            from app.admin import store

            logger.info("Slow admin request route=%s duration_ms=%.1f pool=%s",
                        getattr(request.scope.get("route"), "path", "/admin/api/unknown"),
                        duration, store.pool_stats())
    return response


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
    app.mount("/assets", StaticFiles(directory=assets), name="site-assets")
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
        from app.admin import store

        store.check_ready()
    except StateUnavailable:
        raise
    except RuntimeError:
        raise HTTPException(503, "RAG is not ready.")
    return {"status": "ready", "backend": settings.vector_store}


@app.get("/", response_class=FileResponse, tags=["Root"], include_in_schema=False)
async def root():
    return dashboard()


from app.admin.store import StateUnavailable
from fastapi.responses import JSONResponse


@app.exception_handler(StateUnavailable)
async def state_unavailable(request, error):
    return JSONResponse({"detail": "Chatbot is temporarily unavailable. Please try again later."},
                        status_code=503, headers={"Retry-After": "5"})
