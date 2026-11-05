"""Safe session diagnostics shared by the dashboard, webhooks, and operator CLI."""

import math
import time
from datetime import datetime, timezone

STATUSES = frozenset({
    "STOPPED", "STARTING", "SCAN_QR_CODE", "WORKING", "FAILED",
    "PASSKEY_REQUIRED", "PASSKEY_CONFIRMATION_REQUIRED",
})
REASONS = frozenset({
    "LoggedOut", "TemporaryBan", "ClientOutdated", "StreamReplaced",
    "ConnectFailure", "CATRefreshError",
})


def parse_event(event):
    payload = event.get("payload")
    state = payload.get("status") if isinstance(payload, dict) else None
    if not isinstance(state, str) or state not in STATUSES:
        raise ValueError("Invalid session status.")
    timestamp = event.get("timestamp", int(time.time() * 1000))
    if (isinstance(timestamp, bool) or not isinstance(timestamp, (int, float))
            or not 0 <= timestamp <= time.time() * 1000 + 300_000 or not math.isfinite(timestamp)):
        raise ValueError("Invalid session timestamp.")
    data = payload.get("data")
    reason = data.get("reason") if isinstance(data, dict) else None
    reason = reason if isinstance(reason, dict) else {}
    name = reason.get("event")
    code = reason.get("Reason", reason.get("Code"))
    return {
        "status": state,
        "timestamp": int(timestamp),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "reason": name if isinstance(name, str) and name in REASONS else None,
        "reason_code": code if type(code) is int and 0 <= code <= 999 else None,
    }


def hint(state, last_event=None):
    if state == "FAILED" and isinstance(last_event, dict) and last_event.get("status") == state:
        reason = last_event.get("reason")
        code = last_event.get("reason_code")
        if reason == "TemporaryBan" or code in (402, 403, 406):
            return "WhatsApp restricted this account. Check the shop phone and WAHA logs; repeated restarts or QR pairing cannot lift an account restriction."
        if reason == "ClientOutdated" or code == 405:
            return "WhatsApp rejected the client version. Update WAHA on its host, then restart the session."
        if reason == "StreamReplaced":
            return "Another client replaced this connection. Run only one WAHA instance with these session keys, then restart the session."
        if reason == "LoggedOut" or code == 401:
            return "WhatsApp invalidated the linked-device login. Restart once, then scan the new QR code with the shop phone."
    return {
        "FAILED": "WAHA is reachable, but the WhatsApp session failed. Restart it once. If a QR code appears, link the shop phone again. Server health alone does not confirm a WhatsApp login.",
        "SCAN_QR_CODE": "Link the shop phone again in WhatsApp > Linked devices by scanning the current QR code in the WAHA console. Restarting repeatedly does not complete pairing.",
        "STOPPED": "Start the session in WAHA when ready to connect the shop phone.",
        "STARTING": "WAHA is connecting to WhatsApp. Wait for WORKING; do not repeatedly restart a connecting session.",
        "WORKING": "The WhatsApp session is ready.",
        "PASSKEY_REQUIRED": "Complete the passkey step requested by WhatsApp in the WAHA console.",
        "PASSKEY_CONFIRMATION_REQUIRED": "Confirm the pairing code requested by WhatsApp in the WAHA console.",
        "unreachable": "The backend could not read a valid WAHA session. Check the gateway address, API key, session name, and network.",
    }.get(state, "Session readiness has not been reported.")


def request_error_hint(status_code):
    if status_code == 404:
        return "WAHA is reachable, but the configured session does not exist. Create the session with the exact WAHA_SESSION name or correct that setting before pairing."
    if status_code in (401, 403):
        return "WAHA rejected access to the session. Check the configured API key and its permissions."
    return hint("unreachable")


def snapshot(session, webhook_url="", webhook_secret="", last_event=None):
    state = session.get("status") if isinstance(session, dict) else None
    if not isinstance(state, str) or state not in STATUSES:
        raise ValueError("WAHA returned an invalid session status.")
    engine = session.get("engine")
    engine = engine if isinstance(engine, dict) else {}
    gows = engine.get("gows")
    connected = gows.get("connected") if isinstance(gows, dict) else None
    connected = connected if type(connected) is bool else None
    config = session.get("config")
    hooks = config.get("webhooks") if isinstance(config, dict) else None
    events_configured = None
    webhook_configured = None
    if isinstance(hooks, list):
        matching = [hook for hook in hooks if (
            isinstance(hook, dict) and hook.get("url") == webhook_url
            and isinstance(hook.get("events"), list)
            and isinstance(hook.get("hmac"), dict)
            and bool(webhook_secret) and hook["hmac"].get("key") == webhook_secret
        )]
        events_configured = any("session.status" in hook["events"] or "*" in hook["events"] for hook in matching)
        webhook_configured = any("*" in hook["events"] or all(event in hook["events"] for event in ("message", "message.ack")) for hook in matching)
    detail = hint(state, last_event)
    if state == "WORKING" and connected is False:
        detail = "WAHA reports WORKING, but GOWS is disconnected. Wait for reconnection and inspect the session if it persists."
    elif state == "WORKING" and webhook_configured is False:
        detail = "WhatsApp is paired, but WAHA's callback URL, HMAC key, or message events do not match this app. Configure the production webhook before expecting bot replies."
    result = {
        "session_status": state,
        "engine": engine.get("engine") if engine.get("engine") in ("GOWS", "NOWEB", "WEBJS", "WPP") else None,
        "gateway_reachable": True,
        "session_connected": connected,
        "session_ready": state == "WORKING" and connected is not False,
        "status_events_configured": events_configured,
        "session_hint": detail,
    }
    if webhook_configured is not None:
        result["webhook_configured"] = webhook_configured
    return result
