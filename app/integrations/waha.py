"""WAHA transport and persistent single-worker WhatsApp inbox."""

import hashlib
import hmac
import json
import logging
import re
import threading

import requests
from fastapi import APIRouter, HTTPException, Request
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
    return response.json()


def initialize():
    store.get_runtime_mode()


def enqueue(message):
    inserted = store.enqueue_inbox(
        get_settings().waha_session, message.id, message.sender, message.body
    )
    _wake.set()
    return inserted


def update(row, **fields):
    store.update_inbox(row["session"], row["message_id"], fields)


def plain_text(answer):
    import html

    text = re.sub(r"<br\s*/?>", "\n", answer, flags=re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _reply_id(response):
    identifier = response.get("id") if isinstance(response, dict) else None
    if not isinstance(identifier, str) or not identifier.strip():
        raise requests.RequestException("WAHA send response has no identity; delivery outcome unknown.")
    return identifier


def send_reply(row):
    settings = get_settings()
    base = {"session": row["session"], "chatId": row["sender"]}
    replies = []
    media_error = None
    media_uncertain = False
    if row["media_url"]:
        try:
            from urllib.parse import urlsplit

            media_url = row["media_url"]
            parts = urlsplit(media_url)
            if parts.scheme not in ("https", "http"):
                raise ValueError("Knowledge image needs an HTTP(S) URL.")
            if (
                parts.hostname in ("127.0.0.1", "localhost")
                and settings.waha_webhook_url
            ):
                callback = urlsplit(settings.waha_webhook_url)
                media_url = parts._replace(
                    scheme=callback.scheme, netloc=callback.netloc
                ).geturl()
            image = api(
                "POST",
                "/api/sendImage",
                {
                    **base,
                    "file": {
                        "url": media_url,
                        "mimetype": "image/png"
                        if parts.path.lower().endswith(".png")
                        else "image/jpeg",
                        "filename": "preview.png"
                        if parts.path.lower().endswith(".png")
                        else "preview.jpg",
                    },
                    "caption": "Contoh gambar terkait informasi yang Kakak tanyakan.",
                },
                timeout=60,
            )
            replies.append(_reply_id(image))
            update(row, reply_ids=json.dumps(replies))
        except (requests.RequestException, ValueError) as error:
            media_uncertain = isinstance(error, requests.RequestException)
            media_error = f"Image delivery: {type(error).__name__}; text fallback used."
            logger.warning("WAHA image delivery failed; sending text fallback.")
    text = api(
        "POST", "/api/sendText", {**base, "text": row["answer"], "linkPreview": True}
    )
    replies.append(_reply_id(text))
    update(row, status="uncertain" if media_uncertain else "sent", reply_ids=json.dumps(replies), error=media_error)


def process(row):
    from app.dependencies import get_rag_chain

    try:
        if not row["answer"]:
            update(row, status="generating")
            # Keep previous Fonnte customer history when WAHA supplies a phone JID.
            session_id = "wa_" + row["sender"].removesuffix("@c.us")
            response = get_rag_chain().run(
                question=row["body"],
                session_id=session_id,
                channel="whatsapp",
            )
            answer = plain_text(response.answer)
            if response.error:
                answer = "Maaf Kak, sedang ada gangguan teknis. Silakan coba lagi sebentar ya."
            row = dict(
                row,
                answer=answer,
                media_url=response.media_url if not response.error else None,
            )
            update(row, answer=row["answer"], media_url=row["media_url"])
        update(row, status="sending")
        send_reply(row)
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
    return {
        "provider": "waha",
        "session": get_settings().waha_session,
        "worker_running": bool(_thread and _thread.is_alive()),
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
                store.record_ack(message_id, ack)
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
    inserted = enqueue(message)
    return {"status": "queued" if inserted else "duplicate"}


def status():
    settings = get_settings()
    result = {
        "provider": settings.whatsapp_provider,
        "session": settings.waha_session,
        "worker_running": bool(_thread and _thread.is_alive()),
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
        result.update(store.whatsapp_observations(settings.waha_session))
    return result
