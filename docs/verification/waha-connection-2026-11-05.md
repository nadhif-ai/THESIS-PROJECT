# WhatsApp connection incident, 5 November 2026

## Observed failure

The admin dashboard reported **Connection failed** although the WAHA container's
health endpoint returned HTTP 200. The production Vercel deployment was
`dpl_7isUaKcrHLQu2H4D9ETKviYtruuA`, source `0f97805`, serving
`https://chatbotta-nadhif.vercel.app`.

A read-only invocation of the real dashboard function,
`waha.status(observations={})`, reproduced the screenshot in about two seconds:

```text
provider=waha session=asia-chatbot session_status=FAILED engine=GOWS
credentials_configured=true webhook_configured=true
FAIL: Dashboard reports a failed WhatsApp connection: session_status=FAILED
```

Independent WAHA requests confirmed:

```text
GET /health                           HTTP 200, status=ok
GET /api/server/version               HTTP 200, version=2026.8.2, engine=GOWS
GET /api/sessions?all=true             HTTP 200, asia-chatbot=FAILED
GET /api/sessions/asia-chatbot         HTTP 200, me=null
  engine.grpc.client=READY
  engine.grpc.stream=READY
  engine.gows.found=true
  engine.gows.connected=false
  webhook URL matches application: true
  webhook HMAC matches application: true
  events: message, message.ack
```

The same direct session check failed repeatedly. The minimal reproduction was
one authenticated session GET and the assertion `status == "WORKING"`.

The permanent, credential-safe feedback command is now:

```powershell
.\venv\Scripts\python.exe -m scripts.waha_connection check
```

## Vercel evidence

The investigation used the Vercel MCP tools `get_project`, `get_deployment`,
`get_runtime_errors`, and `get_runtime_logs` for project
`prj_e5lPmnJmameYgDoCqnMMI3Yfpapb`, team
`team_SoJawqKi10DnP6rwCLKjjEH9`.

- `/health` returned HTTP 200 with `status=ready`, `backend=pinecone`.
- Error-cluster queries found no uncaught runtime errors for the connection and
  webhook routes. This does not establish WhatsApp readiness.
- The first 24-hour runtime-log query was rejected because the Hobby plan
  retains only one hour. It was an API retention error, not an empty healthy
  history. Subsequent queries used 15- or 30-minute windows.
- Available runtime lines included `WhatsApp execution=vercel_queue; polling
  worker disabled.` This is expected in production.
- Status-route logs showed approximately 1.0–3.0 second requests, with database
  pool availability and no waiting requests after completion. These lines did
  not contain a WAHA session-failure reason.

WAHA was not subscribed to `session.status`, and the existing webhook handler
ignored that event even if delivered. Consequently, the event explaining the
original disconnect was neither captured in Vercel nor persisted by the app.
Host SSH access was unavailable; host Docker logs were not inspected.

## Diagnosis and recovery

Three hypotheses were tested: invalid linked-device authentication, a transient
GOWS stall, and an incorrect gateway/session configuration. The original
session listing, matching credentials/callback, and ready gRPC channels ruled
out an initial configuration mismatch and a stopped WAHA process.

One `POST /api/sessions/asia-chatbot/restart` returned HTTP 201 and moved the
session to `SCAN_QR_CODE`, with `me=null`. The existing stored login could not
restore WhatsApp connectivity. Manual pairing with the shop phone was required.
No logout, deletion, or reply replay was performed by the recovery command.

The proven fault was the disconnected WhatsApp session on a healthy WAHA
server. The exact event that invalidated the original login remains unknown;
phone logout, account restrictions, and other permanent GOWS failures cannot be
distinguished retrospectively without the missing event or host logs.

During manual recovery, a newly created session with a generated name produced
HTTP 404 for the application's configured name. The operator was instructed to
keep `asia-chatbot`, preserving the application's session identity and inbox.
After manual pairing, the same live command returned `session_status=WORKING`,
`session_connected=true`, and `session_ready=true`. At that point,
`status_events_configured=false` still required subscription repair.
The recreated session had inherited a `httpbin.org` example callback instead
of the configured production URL and HMAC; this also needed correction before
the dashboard's bot could receive new messages.

## Changes

- Receive HMAC-verified, session-scoped `session.status` events without
  enqueuing replies. Persist the latest event and latest failure separately in
  existing PostgreSQL settings; no schema migration is required.
- Use atomic conditional upserts so duplicate and out-of-order callbacks do not
  regress the stored state. Preserve the last failure after recovery and cold
  starts, beyond Vercel's runtime-log retention.
- Allowlist reason names and numeric codes. Exclude raw provider messages,
  phone identifiers, QR data, and credentials from saved diagnostics and logs.
- Expose gateway reachability, GOWS connection state, actual status-event
  subscription, readiness, and recovery guidance in the admin status response.
  Verify the actual callback URL, HMAC, and message events before reporting
  webhook configuration as ready. Distinguish a missing configured session
  from an unreachable server.
- Handle malformed/empty provider responses without crashing the status API.
- Add explicit `check`, one-shot `restart`, and `configure-webhook` commands.
  Recovery preserves authentication and leaves working/pairing sessions alone.
  Subscription repair preserves the full session configuration and installs
  signed callbacks for a recreated session with no existing webhooks.

## Validation

The incident replay and signed-event regression tests failed before the fix:
`16 failed, 1 passed`. Failures included ignored status events, missing
connection diagnostics, and status-route exceptions on malformed responses.

The expanded API/database/queue/dashboard suite passed 77 checks, including
recreated-session callback configuration. Tests use a disposable PostgreSQL 17.11 cluster on loopback port
54585, mocked WhatsApp transports, and no paid model calls.

The Windows test process requires `PYTHONUTF8=1`, matching deployment text
encoding. An initial unrelated evaluation-artifact check failed under cp1252;
it passed with UTF-8 enabled. The application evaluation code was not changed.
An existing attention-control test also depended on two wall-clock reads being
different. A Windows run produced equal timestamps; the fixture now uses two
explicit timestamps to test a newer failure deterministically.

See [the recovery runbook](../runbooks/waha-connection-recovery.md) for the
commands, pairing steps, event subscription, and reason-specific actions.

Live pairing, deployment identity, and post-deployment verification are recorded
in the PR as they complete. A successful application build alone is not evidence
that the phone finished pairing.

Sources checked through Exa:
[WAHA session lifecycle](https://waha.devlike.pro/docs/how-to/sessions/),
[GOWS failure reasons](https://waha.devlike.pro/docs/engines/gows/),
[PostgreSQL test binaries](https://www.enterprisedb.com/download-postgresql-binaries).
