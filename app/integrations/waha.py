"""WAHA transport and persistent single-worker WhatsApp inbox."""

import hashlib
import hmac
import json
import logging
import re
import threading
import time
from contextlib import contextmanager

import requests
from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, ValidationError

from app.admin import store
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/waha", tags=["2. Integrasi WhatsApp"])
_wake = threading.Event()
_stop = threading.Event()
_thread = None


class Message(BaseModel):
    id: str = Field(min_length=1, max_length=512)
    sender: str = Field(alias="from", min_length=1, max_length=100)
    fromMe: bool = False
    body: str | None = Field(default="", max_length=6000)


def api(method, path, payload=None, timeout=30):
    settings = get_settings()
    if not settings.waha_api_key:
        raise ValueError("WAHA_API_KEY is not configured.")
    response = requests.request(
        method,
        settings.waha_base_url.rstrip("/") + path,
        headers={"X-Api-Key": settings.waha_api_key},
        json=payload,
        timeout=timeout,
    )
    if not response.ok:
        # Provider response bodies may include message content or credential details.
        if response.status_code >= 500:
            raise requests.HTTPError(
                f"WAHA returned HTTP {response.status_code}; delivery may be uncertain."
            )
        raise ValueError(f"WAHA returned HTTP {response.status_code}.")
    return response.json() if response.content else {}


def initialize():
    store.get_runtime_mode()


def enqueue(message):
    inserted = store.enqueue_inbox(
        get_settings().waha_session, message.id, message.sender, message.body
    )
    _wake.set()
    return inserted


def update(row, **fields):
    store.update_inbox(row["session"], row["message_id"], fields, lease_token=row.get("lease_token"))


def plain_text(answer):
    import html

    text = re.sub(r"<br\s*/?>", "\n", answer, flags=re.IGNORECASE)
    text = re.sub(r"</?(?:b|strong)\b[^>]*>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"*\1*", text)
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _reply_id(response):
    identifier = response.get("id") if isinstance(response, dict) else None
    if not isinstance(identifier, str) or not identifier.strip():
        raise requests.RequestException("WAHA send response has no identity; delivery outcome unknown.")
    return identifier


def send_reply(row):
    from app.admin import catalog_storage

    settings = get_settings()
    base = {"session": row["session"], "chatId": row["sender"]}
    parts = row.get("delivery_parts") or {}
    if not parts and json.loads(row.get("reply_ids") or "[]"):
        update(row, status="uncertain", error="Legacy partial delivery requires operator inspection.")
        return

    def send_part(name, path, payload, timeout=30):
        previous = (row.get("delivery_parts") or {}).get(name, {})
        if previous.get("status") == "sent":
            return "sent"
        if previous.get("status") in ("sending", "uncertain"):
            store.checkpoint_delivery_part(row, name, "uncertain", error="Previous send outcome unknown.")
            return "uncertain"
        if previous.get("status") in ("failed", "skipped"):
            return previous["status"]
        if not store.checkpoint_delivery_part(row, name, "sending"):
            store.checkpoint_delivery_part(row, name, "skipped", error="Delivery disabled before send.")
            return "skipped"
        try:
            result = api("POST", path, {**base, **payload}, timeout=timeout)
            identifier = _reply_id(result)
        except requests.RequestException:
            store.checkpoint_delivery_part(row, name, "uncertain", error="Provider outcome unknown; inspect before retrying.")
            return "uncertain"
        except ValueError:
            store.checkpoint_delivery_part(row, name, "failed", error="Provider rejected this delivery part.")
            return "failed"
        store.checkpoint_delivery_part(row, name, "sent", provider_id=identifier)
        return "sent"

    selection = row.get("media_selection")
    media_url = catalog_storage.public_url(selection["object_key"]) if selection else row.get("media_url")
    from app.backend.catalog_selection import image_request
    explicit = bool(selection.get('explicit')) if selection else image_request(row.get('body', ''), product_context=True)
    if not explicit:
        media_url = None
    image = None
    if media_url:
        from urllib.parse import urlsplit
        parsed = urlsplit(media_url)
        if parsed.scheme not in ("http", "https"):
            store.checkpoint_delivery_part(row, "image", "failed", error="Invalid media URL.")
            image = "failed"
        else:
            if selection:
                mime = selection["mime_type"]
                caption = selection["caption"]
            else:
                # Only pre-catalog legacy jobs may use knowledge URLs.
                if store.catalog_snapshot()['enabled']:
                    media_url = None
                mime = "image/png" if parsed.path.lower().endswith(".png") else "image/jpeg"
                caption = "Ilustrasi produk terkait pertanyaan Kakak."
            if media_url:
                image = send_part("image", "/api/sendImage", {
                    "file": {"url": media_url, "mimetype": mime,
                             "filename": (selection["asset_id"] if selection else "preview") + (".png" if mime == "image/png" else ".jpg")},
                    "caption": caption,
                }, timeout=60)
    text = send_part("text", "/api/sendText", {"text": row["answer"], "linkPreview": True})
    notice = None
    if image == "failed" and text == "sent" and explicit:
        notice = send_part("notice", "/api/sendText", {
            "text": "Maaf Kak, gambar belum berhasil dikirim. Silakan minta kembali nanti ya.",
            "linkPreview": False,
        })
    uncertain = "uncertain" in (image, text, notice)
    status = "uncertain" if uncertain else "failed" if text == "failed" else "skipped" if text == "skipped" and image != "sent" else "sent"
    errors = [name + ' delivery ' + outcome + '.' for name, outcome in
              (('Image', image), ('Text', text), ('Notice', notice)) if outcome and outcome != 'sent']
    update(row, status=status,
           reply_ids=row.get("reply_ids") or "[]",
           error=' '.join(errors) or None)


def _typing(row, action):
    try:
        api("POST", "/api/" + action,
            {"session": row["session"], "chatId": row["sender"]}, timeout=3)
    except (requests.RequestException, ValueError) as error:
        logger.warning("WAHA presence action=%s failed error=%s; message processing continues.",
                       action, type(error).__name__)


@contextmanager
def typing_indicator(row):
    enabled = get_settings().waha_typing_enabled
    if enabled:
        _typing(row, "startTyping")
    try:
        yield
    finally:
        if enabled:
            _typing(row, "stopTyping")


def process(row):
    from app.dependencies import get_rag_chain

    started = time.monotonic()
    item = hashlib.sha256(row["message_id"].encode()).hexdigest()[:12]
    try:
        logger.info("WhatsApp phase=generating item=%s", item)
        with typing_indicator(row):
            if not row["answer"]:
                update(row, status="generating")
                # Keep previous Fonnte customer history when WAHA supplies a phone JID.
                session_id = "wa_" + row["sender"].removesuffix("@c.us")
                response = get_rag_chain().run(
                    question=row["body"],
                    session_id=session_id,
                    channel="whatsapp",
                    media_conversation_key="waha:" + row["session"] + ":" + row["sender"],
                )
                answer = plain_text(response.answer)
                if response.error:
                    answer = "Maaf Kak, sedang ada gangguan teknis. Silakan coba lagi sebentar ya."
                row = dict(
                    row,
                    answer=answer,
                    media_url=response.media_url if not response.error else None,
                )
                context = getattr(response, "media_context", None) or {}
                selection = getattr(response, "media_selection", None) if not response.error else None
                row["media_selection"] = selection
                update(row, answer=row["answer"], media_url=row["media_url"], media_selection=selection,
                       media_conversation_key=context.get("key"), media_epoch=context.get("epoch"),
                       media_focus=context.get('next_focus'))
            if not store.begin_inbox_send(row["session"], row["message_id"], row.get("lease_token")):
                return
        logger.info("WhatsApp phase=sending item=%s generation_ms=%.1f", item, (time.monotonic()-started)*1000)
        send_reply(row)
        logger.info("WhatsApp phase=sent item=%s total_ms=%.1f", item, (time.monotonic()-started)*1000)
    except store.StateUnavailable:
        # Let durable delivery retry; a transient database outage is not a failed customer answer.
        raise
    except requests.RequestException as error:
        update(
            row,
            status="uncertain",
            error=f"{type(error).__name__}: delivery outcome unknown; inspect WhatsApp before retrying.",
        )
        logger.warning("WAHA request failed for an inbox item; outcome recorded.")
    except Exception as error:
        update(
            row,
            status="failed",
            error=f"{type(error).__name__}: processing failed; inspect the backend log.",
        )
        logger.exception("WhatsApp inbox processing failed")


def worker():
    while not _stop.is_set():
        try:
            if store.get_runtime_mode() == "live":
                row = store.claim_inbox(get_settings().waha_session)
                if row:
                    process(dict(row))
                    continue
        except store.StateUnavailable:
            logger.warning("WhatsApp worker waiting for administration database availability.")
        _wake.wait(2)
        _wake.clear()


def start():
    global _thread
    settings = get_settings()
    if settings.whatsapp_provider != "waha":
        return
    if not settings.waha_api_key or not settings.waha_webhook_secret:
        raise ValueError("WAHA API and webhook credentials are required.")
    from app.integrations.waha_queue import enabled
    if enabled():
        logger.info("WhatsApp execution=vercel_queue; polling worker disabled.")
        return
    initialize()
    _stop.clear()
    _thread = threading.Thread(target=worker, name="whatsapp-inbox", daemon=True)
    _thread.start()


def stop():
    _stop.set()
    _wake.set()
    if _thread:
        _thread.join()


@router.get("/webhook")
def webhook_health():
    from app.integrations.waha_queue import enabled
    return {
        "provider": "waha",
        "session": get_settings().waha_session,
        "worker_running": bool(_thread and _thread.is_alive()),
        "execution_mode": "vercel_queue" if enabled() else "local_worker",
    }


@router.post("/webhook")
async def webhook(request: Request):
    settings = get_settings()
    if settings.whatsapp_provider != "waha" or not settings.waha_webhook_secret:
        raise HTTPException(503, "WAHA is not enabled.")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1_000_000:
            raise HTTPException(413, "Webhook payload is too large.")
    signature = hmac.new(
        settings.waha_webhook_secret.encode(), raw, hashlib.sha512
    ).hexdigest()
    if request.headers.get(
        "x-webhook-hmac-algorithm"
    ) != "sha512" or not hmac.compare_digest(
        request.headers.get("x-webhook-hmac", "").lower(),
        signature,
    ):
        raise HTTPException(401, "Invalid webhook signature.")
    try:
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("Expected an event object.")
        if event.get("session") != settings.waha_session:
            return {"status": "ignored", "reason": "other_session"}
        payload = event.get("payload") or {}
        if event.get("event") == "message.ack":
            message_id, ack = payload.get("id"), payload.get("ack")
            if isinstance(message_id, str) and isinstance(ack, int) and -1 <= ack <= 4:
                await run_in_threadpool(store.record_ack, message_id, ack)
            return {"status": "ack_recorded"}
        if event.get("event") != "message":
            return {"status": "ignored", "reason": "other_event"}
        message = Message.model_validate(payload)
    except (ValueError, ValidationError, TypeError, AttributeError):
        raise HTTPException(400, "Invalid WhatsApp event.")
    if message.fromMe:
        return {"status": "ignored", "reason": "from_me"}
    if not re.fullmatch(r"\d+@(c\.us|lid)", message.sender):
        return {"status": "ignored", "reason": "not_a_private_chat"}
    if not message.body or not message.body.strip():
        return {"status": "ignored", "reason": "no_text"}
    inserted = await run_in_threadpool(enqueue, message)
    from app.integrations.waha_queue import enabled, notify
    if enabled():
        row = await run_in_threadpool(store.get_inbox, settings.waha_session, message.id)
        if row["status"] == "queued":
            try:
                await notify(settings.waha_session, message.id)
            except Exception as error:
                logger.warning("WhatsApp queue notification failed error=%s", type(error).__name__)
                raise HTTPException(503, "Reply queue is temporarily unavailable; retry this webhook.") from None
    logger.info("WhatsApp phase=received item=%s duplicate=%s", hashlib.sha256(message.id.encode()).hexdigest()[:12], not inserted)
    return {"status": "queued" if inserted else "duplicate"}


def status(observations=None):
    settings = get_settings()
    from app.integrations.waha_queue import enabled
    result = {
        "provider": settings.whatsapp_provider,
        "session": settings.waha_session,
        "worker_running": bool(_thread and _thread.is_alive()),
        "execution_mode": "vercel_queue" if enabled() else "local_worker",
        "webhook_url": settings.waha_webhook_url,
        "credentials_configured": bool(
            settings.waha_api_key and settings.waha_webhook_secret
        ),
        "webhook_configured": bool(
            settings.waha_webhook_url and settings.waha_webhook_secret
        ),
    }
    if settings.whatsapp_provider == "waha":
        try:
            session = api("GET", "/api/sessions/" + settings.waha_session, timeout=10)
            result.update(
                session_status=session["status"],
                engine=session.get("engine", {}).get("engine"),
            )
        except (requests.RequestException, ValueError):
            result["session_status"] = "unreachable"
        result.update(observations if observations is not None else store.whatsapp_observations(settings.waha_session))
        result["checked_at"] = store.now()
    return result
