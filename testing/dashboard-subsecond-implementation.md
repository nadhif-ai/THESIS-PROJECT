# Dashboard latency implementation — 2026-10-16

The approved first implementation slice is complete. Warm reads and cached section
changes improved substantially. This is not a guarantee that every request is below
one second: restarted processes, new connections, and variable network latency
still produced slower responses.

## Changes shipped

- Removed all seven Psycopg pipeline scopes. `ClientCursor` safely binds parameters
  through the ordinary simple query protocol. Authenticated read snapshots combine
  session verification, transaction-local timeouts, data selection, and commit in
  one command. Prepared statements stay disabled and the pool stays bounded at two.
- Recently used connections skip an extra checkout ping; idle connections are
  checked again after 30 seconds. Failures remain sanitized and fail closed.
- Login/settings writes use compatible SQL batching. Transaction rollback,
  maintenance locks, shared throttling, CSRF, and immediate session revocation
  remain enforced. Private responses carry `Cache-Control: private, no-store`.
- New knowledge saves persist derived `manifest.chunk_count`. All eight existing
  Supabase versions were backfilled and checked, with a private manifest backup.
  Namespaces, records, published selection, and other manifest fields were retained.
  The idempotent command is `venv/bin/python -m scripts.backfill_version_metadata`.
- `Server-Timing` reports `db_acquire`, `db_read`, and total `app` time. Login
  reports `db_login`, `password`, and `db_session`. Slow admin requests log numeric
  pool statistics without credentials or conversation contents. Read timing covers
  the batched command including commit; it is not a SQL-only execution timer.
- Sidebar pointer/focus intent prefetch uses the installed `queryClient.query()`
  API, shared query keys, and cancellation. At most one optional prefetch runs at a
  time; other concurrent intents are skipped. Logout clears the in-flight queries
  and private cache. Provider saves update the cache from the confirmed response,
  guarded against a response arriving after the session changes.
- Evaluation form, references, history, and saved result details load independently.
  A first job-list fetch no longer treats every historical completed job as a new
  transition. Subsequent observed terminal transitions still invalidate resources.

## Live HTTP measurements

Local Mac HTTP backend → configured Supabase shared transaction pooler. The WAHA
worker and ambient browser polling were active. Each row has 20 sequential samples
with no HTTP errors. The status row was measured separately after consolidating its
read path. Benchmark sessions expired automatically and were revoked on completion;
no password, token, response content, or customer identifiers were recorded.

| Read | Median, ms | p95, ms | Maximum, ms |
| --- | ---: | ---: | ---: |
| Session | 225.8 | 356.9 | 438.3 |
| Overview | 231.1 | 320.8 | 820.8 |
| Versions | 243.4 | 527.8 | 794.4 |
| Settings | 215.1 | 372.8 | 747.3 |
| Jobs | 218.5 | 335.8 | 447.8 |
| WhatsApp history | 463.0 | 731.9 | 1,035.9 |
| Conversation reference dataset | 221.8 | 458.6 | 468.1 |
| QA reference dataset | 212.4 | 251.7 | 490.6 |
| Saved evaluation detail | 685.5 | 946.5 | 1,142.5 |
| WAHA status | 554.1 | 694.2 | 1,267.8 |

Four simultaneous overview/versions/jobs/settings reads completed in 643.4 ms or
less, one small concurrency probe. WAHA status previously took 1,717.3 ms median in
three samples before its database observations were folded into the authenticated
snapshot. Its remote WAHA session check remains live, without a cached readiness claim.

Version metadata SQL execution after backfill was 0.166 ms, eight rows, five shared
buffer hits and no reads, compared with the earlier diagnostic 120.975 ms and 821
hits. These are individual EXPLAIN samples, not a controlled causal benchmark.

## Browser checks

The user's existing Edge dashboard was available through its normal HTTP URL.
All six sections displayed their content. A sidebar focus prefetched `/jobs`, and
the immediate evaluation visit reused that request without a duplicate jobs fetch.
The evaluation form and job table appeared while other widgets were still loading.

Repeated cached navigation, measured around supported browser clicks and a
visible-content wait, took Dashboard 290 ms, Knowledge 242 ms, Playground 221 ms,
Conversations 238 ms, Providers 232 ms, and Evaluations 234 ms. These six samples
include automation overhead; they are not browser-only paint timings or a p95.

![Verified evaluation view](dashboard-subsecond-evaluations.png)

## Checks and remaining limits

- 59 targeted backend checks passed against disposable PostgreSQL on port 54585:
  auth/CSRF, one-command snapshots, timeout/recovery, rollback, backfill idempotence,
  migration, lifecycle, state, progress, and the existing public landing boundary.
- Frontend TypeScript/production build passed. Lint completed with eight existing
  warnings in shared components/hooks. Changed Python files parsed; diff whitespace
  checks passed. No paid evaluation, ingestion, publish, or outbound test was run.
- Real password login was not benchmarked: `ADMIN_PASSWORD` is empty in the local
  runtime configuration. Existing signed-in browser sessions were retained, and
  synthetic-account login plus phase headers were checked in disposable PostgreSQL.
- After a backend restart, slow-request logs recorded 1.69–6.87-second requests.
  Two connection establishments totalled 8.32 seconds, and one worker checkout
  error was logged before retry. The warm sample set does not describe that cold
  or unstable-network distribution. History, detail, and status also had individual
  warm outliers above one second despite their subsecond p95 in this small sample.
- No region change, Redis provisioning, auth-provider change, or Vercel deployment
  is included. Confirm the database region and colocate a preview backend before
  making an end-to-end production latency claim. Local files, model startup, and
  the persistent worker still need their deployment work.

Raw numeric evidence: [HTTP/browser samples](dashboard-subsecond-performance.json).
Architecture and primary references: [preceding research](dashboard-subsecond-research.md).

## Availability follow-up — 2026-10-16

At 02:58 local time, the running backend logged socket and DNS failures. After
connectivity recovered, a new connection and a fresh store passed while the old
backend still returned 503. Its live pool statistics showed zero connections and
20 expired waiting requests. In installed psycopg-pool 3.3.3, a full waiting queue
rejects new requests before they can restart pool growth after the reconnect
window expires. This was reproduced with injected connection failures.

The pool now registers a `reconnect_failed` callback that uses the public `check()`
method to restart connection recovery unless the pool is closed. Connection limits,
SQL transactions, authorization, and delivery semantics remain unchanged. This
does not retry application writes or WhatsApp sends.

A regression through `/admin/api/me` failed before the fix and passes afterwards:
503 while offline, automatic recovery with the original session after the waiting
queue fills and the reconnect deadline expires, then 401 after session revocation.
All 60 targeted backend checks pass against disposable PostgreSQL. After restarting
the local backend, `/health` returned 200, and reloading the user's existing browser
tab returned 200 for both `/admin/api/me` and `/admin/api/overview` without resetting
credentials or session data. Evidence: [recovered dashboard](dashboard-recovery-verification.png).

This fixes failure to recover from an outage. Actual network/database downtime
still correctly returns 503; no claim is made that this patch prevents outages.
