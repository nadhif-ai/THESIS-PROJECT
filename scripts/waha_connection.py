"""Inspect WAHA or perform one explicit recovery action without exposing credentials."""

import argparse
from copy import deepcopy
import json
import time
from urllib.parse import quote

import requests

from app.config.settings import get_settings
from app.integrations import waha, waha_session


def session_path():
    return "/api/sessions/" + quote(get_settings().waha_session, safe="")


def read_session():
    session = waha.api("GET", session_path(), timeout=10)
    waha_session.snapshot(session)
    return session


def restart_session():
    session = read_session()
    state = session["status"]
    if state not in ("FAILED", "STOPPED"):
        return session
    action = "start" if state == "STOPPED" else "restart"
    waha.api("POST", session_path() + "/" + action, {}, timeout=25)
    deadline = time.monotonic() + 20
    while True:
        session = read_session()
        if session["status"] != "STARTING" or time.monotonic() >= deadline:
            return session
        time.sleep(1)


def configure_webhook():
    settings = get_settings()
    if not settings.waha_webhook_url or not settings.waha_webhook_secret:
        raise ValueError("Webhook credentials are not configured.")
    session = read_session()
    config = deepcopy(session.get("config"))
    config = {} if config is None else config
    if not isinstance(config, dict):
        raise ValueError("Invalid session configuration.")
    hooks = config.get("webhooks")
    hooks = [] if hooks is None else hooks
    if not isinstance(hooks, list):
        raise ValueError("Invalid webhook configuration.")
    matches = [hook for hook in hooks if isinstance(hook, dict) and hook.get("url") == settings.waha_webhook_url]
    if not hooks:
        config["webhooks"] = [{
            "url": settings.waha_webhook_url,
            "events": ["message", "message.ack", "session.status"],
            "hmac": {"key": settings.waha_webhook_secret},
            "retries": {"policy": "constant", "delaySeconds": 2, "attempts": 5},
        }]
    elif len(matches) != 1:
        raise ValueError("Expected one matching webhook.")
    else:
        hook = matches[0]
        hmac_config = hook.get("hmac")
        events = hook.get("events")
        if (not isinstance(hmac_config, dict) or hmac_config.get("key") != settings.waha_webhook_secret
                or not isinstance(events, list) or not all(isinstance(event, str) for event in events)):
            raise ValueError("Existing webhook configuration does not match this app.")
        missing = [event for event in ("message", "message.ack", "session.status") if event not in events]
        if not missing or "*" in events:
            return session
        hook["events"] = [*events, *missing]
    # WAHA replaces the full config and restarts the session on PUT.
    waha.api("PUT", session_path(), {"name": settings.waha_session, "config": config}, timeout=25)
    return read_session()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "restart", "configure-webhook"), help="configure-webhook preserves the full config but restarts the WAHA session")
    parser.add_argument("--require-events", action="store_true", help="also fail if signed session.status callbacks are missing")
    args = parser.parse_args(argv)
    settings = get_settings()
    if settings.whatsapp_provider != "waha":
        print(json.dumps({"error": "WAHA is not the configured WhatsApp provider."}))
        return 1
    try:
        session = {"check": read_session, "restart": restart_session, "configure-webhook": configure_webhook}[args.action]()
        result = {"session": settings.waha_session, **waha_session.snapshot(session, settings.waha_webhook_url, settings.waha_webhook_secret)}
    except (requests.RequestException, ValueError) as error:
        code = error.status_code if isinstance(error, waha.WahaAPIError) else None
        print(json.dumps({"session": settings.waha_session, "session_ready": False, "gateway_http_status": code,
                          "error_type": type(error).__name__, "session_hint": waha_session.request_error_hint(code)}))
        return 1
    print(json.dumps(result))
    if result["session_status"] in ("SCAN_QR_CODE", "PASSKEY_REQUIRED", "PASSKEY_CONFIRMATION_REQUIRED"):
        return 3
    if not result["session_ready"]:
        return 2 if result["session_status"] == "STARTING" else 1
    return 1 if args.require_events and not result["status_events_configured"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
