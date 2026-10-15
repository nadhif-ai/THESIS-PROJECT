import hashlib
import json
import secrets
import time
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.admin import store, knowledge, jobs
from app.admin.chunking import Chunking, LEGACY
from app.config.settings import get_settings

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


def check_origin(request):
    origin = request.headers.get("origin")
    if (
        origin
        and origin not in get_settings().allowed_origins.split(",")
        and origin != f"{request.url.scheme}://{request.url.netloc}"
    ):
        raise HTTPException(403, "This request origin is not allowed.")


def require_admin(request: Request):
    token = request.cookies.get("avg_admin", "")
    row = store.get_session(hashlib.sha256(token.encode()).hexdigest(), time.time())
    if not row:
        raise HTTPException(401, "Sign in to continue.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), row["csrf"]
        ):
            raise HTTPException(403, "Refresh your session before saving changes.")
        store.require_live()
    return row["csrf"]


protected = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


@admin_router.post("/api/login")
def login(body: Login, request: Request, response: Response):
    check_origin(request)
    ip = request.client.host if request.client else "local"
    client_hash = hashlib.sha256(ip.encode()).hexdigest()
    if not store.login_allowed(client_hash, time.time()):
        raise HTTPException(429, "Too many attempts. Try again in five minutes.")
    user = store.get_user(body.username.strip())
    salt = user["salt"] if user else "00" * 16
    digest = store.hash_password(body.password, salt)
    if not user or not secrets.compare_digest(digest, user["password_hash"]):
        store.record_login_failure(client_hash, time.time())
        raise HTTPException(401, "Username or password is incorrect.")
    store.clear_login_failures(client_hash)
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    store.create_session(
        hashlib.sha256(token.encode()).hexdigest(), time.time() + 28800, csrf
    )
    response.set_cookie(
        "avg_admin",
        token,
        httponly=True,
        samesite="strict",
        secure=get_settings().cookie_secure,
        max_age=28800,
        path="/admin",
    )
    return {"username": body.username, "csrf": csrf}


@protected.get("/me")
def me(csrf: Annotated[str, Depends(require_admin)]):
    return {"username": get_settings().admin_username, "csrf": csrf}


@protected.post("/logout")
def logout(request: Request, response: Response):
    store.delete_session(
        hashlib.sha256(request.cookies.get("avg_admin", "").encode()).hexdigest()
    )
    response.delete_cookie("avg_admin", path="/admin")
    return {"ok": True}


def summary(item):
    return {k: v for k, v in item.items() if k != "records"} | {
        "chunk_count": len(item["records"]),
        "chunking": item["manifest"].get("chunking", LEGACY),
    }


@protected.get("/overview")
def overview():
    rows = store.conversations(limit=10000)
    published = store.version()
    baseline = json.loads((knowledge.BASELINE / "results.json").read_text())
    latency = [r["latency"] for r in rows if r["latency"]]
    return {
        "conversations": len(rows),
        "whatsapp_messages": sum(r["channel"] == "whatsapp" for r in rows),
        "average_latency": round(sum(latency) / len(latency), 2) if latency else None,
        "published": summary(published),
        "baseline": {
            "cases": len(baseline["rows"]),
            "hit_rate": baseline["avg_hit_rate"],
            "precision": baseline["avg_precision"],
        },
        "recent": rows[:8],
        "jobs": jobs.list_jobs()[:8],
    }


@protected.get("/versions")
def versions():
    return {
        "versions": [summary(v) for v in store.versions()],
        "published": store.get_setting("published_version"),
    }


class Draft(BaseModel):
    base_id: str | None = None


@protected.post("/versions")
def draft(body: Draft):
    try:
        return summary(knowledge.new_draft(body.base_id))
    except ValueError as e:
        raise HTTPException(400, str(e))


@protected.get("/versions/{version_id}/files/{name}")
def file_content(version_id: str, name: str):
    try:
        item = store.version(version_id)
        name = knowledge.valid_name(name)
        if name not in item["manifest"]["files"]:
            raise ValueError("File is not part of this version.")
        path = knowledge.path_for(item) / name
        if path.suffix == ".pdf":
            return {"name": name, "content": None, "editable": False}
        return {
            "name": name,
            "content": path.read_text(encoding="utf-8-sig"),
            "editable": item["status"] in ("draft", "failed"),
        }
    except (ValueError, UnicodeDecodeError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))


@protected.put("/versions/{version_id}/chunking")
def chunking(version_id: str, body: Chunking):
    try:
        knowledge.configure_chunking(version_id, body)
        return summary(store.version(version_id))
    except ValueError as error:
        raise HTTPException(400, str(error))


class TextFile(BaseModel):
    name: str = Field(max_length=200)
    content: str = Field(max_length=2_000_000)


@protected.put("/versions/{version_id}/files")
def save_file(version_id: str, body: TextFile):
    try:
        knowledge.save_file(version_id, body.name, body.content.encode())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@protected.post("/versions/{version_id}/upload")
async def upload(version_id: str, file: Annotated[UploadFile, File()]):
    try:
        name = knowledge.valid_name(file.filename or "")
        content = await file.read(10 * 1024 * 1024 + 1)
        if len(content) > 10 * 1024 * 1024:
            raise ValueError("Maximum upload size is 10 MB.")
        knowledge.save_file(version_id, name, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@protected.delete("/versions/{version_id}/files/{name}")
def delete_file(version_id: str, name: str):
    try:
        knowledge.delete_file(version_id, name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@protected.post("/versions/{version_id}/index")
def index(version_id: str):
    try:
        knowledge.editable(version_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"job_id": jobs.create("index", {"version_id": version_id})}


@protected.post("/versions/{version_id}/publish")
def publish(version_id: str):
    try:
        store.publish(version_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@protected.get("/versions/{version_id}/chunks")
def chunks(version_id: str):
    try:
        rows = store.version(version_id)["records"]
    except ValueError as e:
        raise HTTPException(404, str(e))
    return [
        {"id": r["id"], "text": r["document"], "metadata": r["metadata"]} for r in rows
    ]


class Playground(BaseModel):
    question: str = Field(min_length=1, max_length=6000)
    session_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    version_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


@protected.post("/playground")
def playground(body: Playground):
    from app.dependencies import get_rag_chain

    try:
        version = store.version(body.version_id)
        if version["status"] not in ("ready", "published"):
            raise ValueError("Index this knowledge version before testing it.")
    except ValueError as e:
        raise HTTPException(400, str(e))
    response = get_rag_chain().run(
        question=body.question,
        session_id="playground_" + version["id"] + "_" + body.session_id,
        namespace=version["namespace"],
        channel="playground",
        top_k=body.top_k,
    )
    if response.error:
        raise HTTPException(502, response.error)
    return asdict(response)


@protected.get("/conversations")
def conversations(channel: str | None = None):
    return store.conversations(channel)


@protected.get("/settings")
def settings():
    s = get_settings()
    return {
        "openrouter_model": store.get_setting("openrouter_model", s.openrouter_model),
        "eval_model": store.get_setting("eval_model", s.eval_model),
        "semantic_top_k": store.get_setting("semantic_top_k", s.semantic_top_k),
        "embedding_model": s.embedding_model,
        "dimension": 384,
        "pinecone_index": s.pinecone_index_name,
        "whatsapp_provider": s.whatsapp_provider,
        "waha_session": s.waha_session if s.whatsapp_provider == "waha" else None,
        "langsmith_project": __import__("os").getenv("LANGSMITH_PROJECT", "default"),
        "providers": {
            "openrouter": bool(s.openrouter_api_key),
            "pinecone": bool(s.pinecone_api_key),
            "langsmith": bool(__import__("os").getenv("LANGSMITH_API_KEY")),
            "whatsapp": bool(s.waha_api_key and s.waha_webhook_secret)
            if s.whatsapp_provider == "waha"
            else bool(s.fonnte_token),
        },
    }


@protected.get("/whatsapp/status")
def whatsapp_status():
    from app.integrations.waha import status

    return status()


class ProviderSettings(BaseModel):
    openrouter_model: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_./:-]+$"
    )
    eval_model: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_./:-]+$"
    )
    semantic_top_k: int = Field(ge=1, le=20)


@protected.put("/settings")
def save_settings(body: ProviderSettings):
    for key, value in body.model_dump().items():
        store.set_setting(key, value)
    return settings()


@protected.get("/jobs")
def job_list():
    return jobs.list_jobs()


class Evaluation(BaseModel):
    version_id: str | None = None
    dataset: str = "legacy"
    limit: int = Field(default=10, ge=1, le=40)


@protected.post("/evaluations")
def evaluate(body: Evaluation):
    try:
        item = store.version(body.version_id)
        if item["status"] not in ("ready", "published"):
            raise ValueError("Select indexed knowledge.")
        if body.dataset not in ("legacy", "audited", "conversations", "heldout"):
            raise ValueError("Unknown dataset.")
        from testing.evals.runner import load_cases

        load_cases(body.dataset, body.limit)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "job_id": jobs.create(
            "evaluate", dict(body.model_dump(), version_id=item["id"])
        )
    }


@protected.post("/evaluations/generate")
def generate(body: Draft):
    try:
        item = store.version(body.base_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"job_id": jobs.create("generate", {"version_id": item["id"]})}


@protected.get("/evaluations/dataset")
def dataset(kind: str = "conversations"):
    from testing.evals.runner import dataset_status

    if kind not in ("conversations", "audited"):
        raise HTTPException(400, "Unknown dataset.")
    return dataset_status(kind)


@protected.post("/evaluations/dataset/review")
def review_dataset(kind: str = "conversations"):
    from testing.evals.runner import mark_reviewed

    try:
        if kind not in ("conversations", "audited"):
            raise ValueError("Unknown dataset.")
        return mark_reviewed(kind)
    except ValueError as error:
        raise HTTPException(400, str(error))


@protected.post("/evaluations/{evaluation_id}/report")
def retry_report(evaluation_id: str):
    return {"job_id": jobs.create("report", {"evaluation_id": evaluation_id})}


@protected.get("/evaluations/{evaluation_id}/export")
def export(evaluation_id: str):
    if not evaluation_id.isalnum():
        raise HTTPException(400, "Invalid evaluation ID.")
    path = store.data_path() / "evaluations" / evaluation_id / "results.json"
    if not path.exists():
        raise HTTPException(404, "Results not found.")
    return FileResponse(path, filename="evaluation-" + evaluation_id + ".json")


admin_router.include_router(protected)


FRONTEND_INDEX = Path(__file__).resolve().parents[2] / "frontend/dist/index.html"


@admin_router.get("")
@admin_router.get("/")
@admin_router.get("/{path:path}", include_in_schema=False)
def dashboard(path: str = ""):
    if path.startswith("api/"):
        raise HTTPException(404, "API endpoint not found.")
    if not FRONTEND_INDEX.exists():
        raise HTTPException(
            503, "Build the dashboard: cd frontend && npm install && npm run build"
        )
    return FileResponse(FRONTEND_INDEX)
