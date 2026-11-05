# WAHA connection recovery

WAHA process health and a WhatsApp login are separate checks. `/health` can return
HTTP 200 while `asia-chatbot` is `FAILED` and GOWS reports `connected=false`.
Only a `WORKING` session with no explicit disconnected transport is ready.

Run the same read-only check before and after recovery:

```powershell
.\venv\Scripts\python.exe -m scripts.waha_connection check
```

On Linux/macOS, use `venv/bin/python` instead. The command reads the existing
environment and prints only allowlisted diagnostics. Exit codes: `0` ready,
`1` failed/unreachable, `2` starting, `3` pairing or passkey required.
Add `--require-events` to require the signed session-status callback as well.
An HTTP 404 means the configured session is missing, even when WAHA itself is
reachable. Keep the production session name `asia-chatbot` when recreating it;
the dashboard's generated session name does not update the app configuration.

## Recovery

1. Inspect `session_status`, `session_connected`, `session_hint`, and the dashboard
   API's `last_session_event` and `last_session_failure`. The latter preserves the
   most recent failure even after reconnection and a Vercel cold start.
2. If the session is `FAILED`, restart once while preserving its authentication:

   ```powershell
   .\venv\Scripts\python.exe -m scripts.waha_connection restart
   ```

   The command starts a stopped session, waits briefly for a starting session,
   and leaves a working or pairing session alone. It never logs out or deletes
   a session, resends a reply, or repeatedly restarts a failing login.
3. If it reaches `SCAN_QR_CODE`, open the configured WAHA console and select
   `asia-chatbot`. Use WhatsApp on the shop phone: **Linked devices > Link a
   device**. Scan the current QR. If it expired, start/restart the failed session
   in WAHA and scan the fresh QR. A container restart cannot perform this step.
4. Run `check` again. Require `session_status=WORKING` and `session_ready=true`.
   Refresh **Providers** in the admin dashboard.

Use a shop-owned test conversation to confirm inbound receipt, a reply, and its
delivery acknowledgement. Do not replay `uncertain` deliveries automatically.

## Preserve the cause of the next failure

The session's matching webhook must include `message`, `message.ack`, and
`session.status`, use the configured callback URL and HMAC secret, and retain its
existing retry configuration. To add only the missing status subscription:

```powershell
.\venv\Scripts\python.exe -m scripts.waha_connection configure-webhook
.\venv\Scripts\python.exe -m scripts.waha_connection check --require-events
```

Run this after the application supports session events. **WAHA updates restart
the session**, even when only its webhook configuration changes. Schedule that
brief interruption when pairing is not in progress. The command preserves the
complete session config and unrelated webhooks, refuses a mismatched callback
or HMAC key, and skips the update when already subscribed. For a newly recreated
session with no webhooks, it installs the three events with the configured URL,
HMAC key, and the documented constant retry policy.

Signed status events are persisted by session and provider timestamp. Duplicate
or late callbacks cannot replace a newer status. A small allowlist stores the
status, time, reason event, and numeric reason code. Phone numbers, provider
messages, raw reason objects, QR data, and credentials are excluded.

In Vercel MCP, query runtime logs with `query: "phase=session_status"` or
`query: "phase=session_check"`, the correct project/team, and a window within
the plan's retention. Hobby retains one hour; an older-window API error does
not mean there were no failures. The persisted last failure remains available
after log retention expires.

| GOWS failure reason | Action |
| --- | --- |
| `LoggedOut` / 401 | Link the shop phone again after one restart. |
| `ClientOutdated` / 405 | Update WAHA on its host, then restart. |
| `StreamReplaced` | Ensure only one instance uses these session keys. |
| `TemporaryBan` / 402, 403, 406 | Check the phone/account restriction; repeated restarts and pairing do not lift it. |
| No reason reported | Inspect WAHA host logs. State that the original cause is unknown. |

GOWS normally reconnects after recoverable network drops. A permanent failure
or revoked linked-device login needs a different action; a restart watchdog
cannot guarantee recovery and must not repeatedly clear authentication.
Keep a single WAHA session owner and persistent session storage on an always-on
host. Keep the primary phone/account active and review WAHA updates when a
captured reason indicates client incompatibility.

Sources: [WAHA session lifecycle and update behavior](https://waha.devlike.pro/docs/how-to/sessions/),
[GOWS failure reasons and reconnect behavior](https://waha.devlike.pro/docs/engines/gows/),
[Vercel runtime logs](https://vercel.com/docs/observability/runtime-logs).
