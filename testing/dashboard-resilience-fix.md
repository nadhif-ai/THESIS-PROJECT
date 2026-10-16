# Recurring dashboard 503: investigation and recovery

Date: 2026-10-16, Asia/Jakarta.

## Evidence and reproduced causes

The reported `/admin/api/me` failure took 5,009.4 ms. The old pool acquisition
budget was five seconds. The exact historical operation did not have phase-level
failure logging, so its underlying network trigger cannot be reconstructed fully.
The previous empty-pool callback addressed failed connection creation; it did not
bound an already checked-out connection or make session bootstrap retry.

1. **A checked-out connection could wait indefinitely for missing responses.** A
   TCP relay against disposable PostgreSQL dropped application traffic while keeping
   the socket open. The original session request failed the completion deadline.
   A server-side statement timeout cannot help when the query never reaches the
   server. The fixed driver closes failed/timed-out connections, and the pool
   replaces them. Both an accelerated deadline and the actual 35-second deadline
   are exercised by the transport regression.
2. **The acquisition budget was shorter than valid cold connection setup.** The
   configured pooler resolved to two IPv4 addresses. Libpq's five-second connect
   timeout applies separately to each address; a five-second checkout can therefore
   fail before a valid connection is ready. A scaled healthy cold-connect regression
   returned 503 before the fix and 200 afterwards. Checkout now allows 15 seconds;
   the pool remains capped at two connections and 20 queued requests.
3. **One failed session check left a terminal error screen.** Session bootstrap used
   a one-shot fetch outside Query, while read-query retries were disabled. Session
   bootstrap now retries transient failures with capped backoff and resumes after
   reconnect. A real browser received three intentional 503s from a temporary local
   verification service and opened the authenticated dashboard on attempt four,
   without clicking Retry, resetting credentials, or bypassing authorization.

## Safeguards

- Client database I/O is bounded at 35 seconds, including health probes. TCP
  keepalive settings and TCP user timeout are supplied where supported by the OS.
- Transaction-local statement/lock timeouts remain 30/5 seconds. An additional
  35-second idle-in-transaction deadline releases abandoned maintenance locks. A
  real PostgreSQL contention test verifies that another transaction obtains the
  lock after an abandoned client expires.
- Connection recovery restarts after a 15-second reconnect window; the prior
  `reconnect_failed` callback remains. Failed SQL operations are not replayed.
- Database errors log phase, error class, SQLSTATE, elapsed time, and pool counts.
  SQL text, bind values, credentials, and conversation contents are not logged by
  this instrumentation. The current private runtime log is under `data/diagnostics/`.
- GET/HEAD requests have a 20-second browser deadline. Ordinary reads get at most
  two extra transient retries. Bootstrap retries while awaiting a verified session;
  offline state is shown and retries resume when connectivity returns. Delay is
  exponential, capped at 15 seconds. Cached content remains visible on refresh.
- 401/403 and application/validation errors are not retried. Logout/session expiry
  clears private state and cancels pending checks. POST/PUT/DELETE requests, paid
  evaluation, publishing, and WhatsApp sends are not automatically replayed.

## Verification

```bash
LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_database_transport.py testing/test_dashboard_reads.py testing/test_admin_workflow.py testing/test_state_lifecycle.py testing/test_postgres_state.py testing/test_dashboard_progress.py testing/test_state_migration.py testing/test_public_landing.py testing/test_waha_reconciliation.py -q
node --experimental-strip-types --test testing/test_dashboard_query_retry.mjs
cd frontend
npm run build
npm run lint
```

PostgreSQL tests use the disposable cluster on port 54585, never the configured
Supabase database. The transport test with the production deadline intentionally
takes approximately 35 seconds. Browser and Query tests cover transient recovery,
expired sessions, cache cancellation, partial-body timeouts, and no write replay.
The production build succeeds; lint has eight pre-existing warnings and no new ones.
All 78 backend tests passed in 43.66 seconds, and all 12 frontend checks passed.

The live backend completed **240 authenticated reads in twenty 12-request bursts**
with zero errors, with its normal WAHA worker and browser traffic active. Individual
responses under that load reached 5,961.6 ms; this is not a subsecond performance
claim. The temporary verification session was revoked. Raw numeric evidence:
[load and UI checks](dashboard-resilience-verification.json).

The temporary UI service had no message worker or generation pipeline and was
stopped after the test. The real backend on port 8000 was restarted with the fix;
the user's provider form was left untouched. [Verified live dashboard](dashboard-resilience-complete.png).

This fixes the reproduced software failure/recovery paths. It cannot guarantee
Internet or Supabase uptime, or prove that every possible future outage is eliminated.

References: [Psycopg pool behavior](https://www.psycopg.org/psycopg3/docs/advanced/pool.html),
[libpq connection timeouts and keepalives](https://www.postgresql.org/docs/current/libpq-connect.html),
[Query retry behavior](https://tanstack.com/query/v5/docs/framework/react/guides/query-retries).
