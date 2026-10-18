from fastapi import APIRouter, HTTPException, Query, Request
from typing import Annotated
from pydantic import BaseModel, Field

from app.admin import durable_jobs, global_knowledge, kb_store, source_storage
from app.admin.chunking import Chunking

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/prompt")
def conversational_prompt():
    from app.admin import prompt_settings

    return prompt_settings.editor()


class ConversationalPrompt(BaseModel):
    prompt: str = Field(strict=True, min_length=1, max_length=12000)


@router.put("/prompt")
def save_conversational_prompt(body: ConversationalPrompt):
    from app.admin import prompt_settings

    try:
        return prompt_settings.save(body.prompt)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None


def invalid(error):
    return HTTPException(400 if isinstance(error, ValueError) else 503, str(error))


@router.get("")
def catalog(request: Request):
    from app.admin.routes import summary

    data = kb_store.validate_catalog(request.state.admin_data)
    data["active"] = summary(data["active"]) if data["active"] else None
    return data


class UploadTicket(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    size_bytes: int = Field(ge=1, le=source_storage.MAX_BYTES)
    source_id: str | None = None


@router.post("/uploads")
def upload_ticket(body: UploadTicket):
    try:
        name = global_knowledge.valid_name(body.name)
        identifier = kb_store.stage_upload(name, body.size_bytes, body.source_id)
        upload = kb_store.blob(identifier)
        return {
            "upload_id": identifier,
            "url": source_storage.signed_upload(upload["object_path"]),
            "content_type": "application/pdf"
            if name.endswith(".pdf")
            else "text/plain",
        }
    except (ValueError, RuntimeError) as error:
        raise invalid(error) from None


class FinishUpload(BaseModel):
    source_id: str | None = None


@router.post("/uploads/{upload_id}/complete")
def finish_upload(upload_id: str, body: FinishUpload):
    try:
        return {"source_id": global_knowledge.finish_upload(upload_id, body.source_id)}
    except (ValueError, RuntimeError) as error:
        raise invalid(error) from None


class SourceState(BaseModel):
    enabled: bool = Field(strict=True)


@router.patch("/sources/{source_id}")
def source_state(source_id: str, body: SourceState):
    try:
        kb_store.change_source(source_id, enabled=body.enabled)
        return {"ok": True}
    except ValueError as error:
        raise invalid(error) from None


@router.delete("/sources/{source_id}")
def delete_source(source_id: str):
    try:
        kb_store.change_source(source_id, delete=True)
        return {"ok": True}
    except ValueError as error:
        raise invalid(error) from None


@router.get("/sources/{source_id}/preview")
def preview(source_id: str):
    try:
        return global_knowledge.preview(source_id)
    except (ValueError, RuntimeError) as error:
        raise invalid(error) from None


@router.put("/chunking")
def configure(body: Chunking):
    try:
        if body.chunk_overlap > body.chunk_size // 2:
            raise ValueError("Overlap must be at most half the chunk size.")
        kb_store.configure({**body.model_dump(), "preprocessing": "sections-v1"})
        return {"ok": True}
    except ValueError as error:
        raise invalid(error) from None


@router.get("/sources/{source_id}/chunks")
def passages(source_id: str, page: Annotated[int, Query(ge=0, le=10000)] = 0):
    try:
        return global_knowledge.passage_page(source_id, page)
    except ValueError as error:
        raise invalid(error) from None


@router.post("/sync")
def synchronize():
    try:
        identifier = kb_store.start_sync()
        try:
            durable_jobs.dispatch(identifier)
        except RuntimeError:
            return {"job_id": identifier, "dispatch_pending": True}
        return {"job_id": identifier}
    except ValueError as error:
        raise invalid(error) from None
