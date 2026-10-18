# WhatsApp and dashboard reliability — 18 October 2026

## Confirmed causes

- Production menu requests (`2`) raised `OSError: [Errno 30] Read-only file system: '/var/task/data'` in `knowledge.path_for()`. LangSmith then ran the output formatter with `None` while reporting that exception, producing the secondary `NoneType.answer` warning.
- The application started a polling daemon during FastAPI lifespan. Inbox rows remained `generating` after HTTP invocations stopped running. At the start of this investigation there were two stalled generations and seven queued messages. The development MacBook had previously processed messages received by Vercel.
- Every write exclusively locked the single `runtime_control` row. Supabase logs on 18 October contained both lock timeouts and idle-in-transaction termination. These are separate from an unavailable WhatsApp session.
- Functions ran in `iad1`; the configured Supabase pooler is in `ap-south-1` (Mumbai). The first diagnostic response also spent 36.7 seconds outside a handler that took 3 ms. That response was a rejected login payload, not a successful password-login benchmark.
- Anonymous, expired, or different-host sessions legitimately receive 401. Preview Deployment Protection is a second authentication layer. Authentication, session revocation, CSRF and webhook HMAC have not been weakened.

## Changes

- Python Vercel Queues subscriber replaces the polling worker on Vercel. React and FastAPI stay in the existing Services project; only WAHA runs on Linux.
- A Services Python entrypoint must be `pyproject.toml` to compose the declared web application and subscriber. Keeping `app.main:app` as the service entrypoint silently omitted subscribers from the first successful preview build. `tool.vercel.entrypoint` still points to `app.main:app`.
- The consumer claims a specific persisted inbox item under a per-chat advisory lock. Earlier pending messages block later messages from the same chat. A five-minute execution lease permits interrupted generation to recover; fencing tokens stop an obsolete worker from starting a send. An expired send becomes `uncertain`, never an automatic resend.
- Legacy abandoned generations and queued items older than 15 minutes are marked failed when a new callback inspects that chat. History and deduplication identities remain. Existing uncertain deliveries are never replayed automatically.
- Ordinary writes share the maintenance gate. Bot pause and publish retain exclusive serialization. First-cutover accounting is updated before acquiring the shared gate to avoid a lock-upgrade deadlock.
- Blocking database work in the async WAHA webhook runs in the thread pool. Authentication and intake no longer wait for RAG/provider startup. Pinecone index and embedding compatibility validation remains in retrieval and explicit readiness initialization.
- Menu examples are read without creating version directories. New edits persist menu text in the version manifest; historical versions lacking it use the bundled help examples. Trace formatting tolerates a missing output without hiding the original exception.
- Query embedding retries are two attempts with `(5, 20)` second connection/read limits. Ingestion retains three attempts with `(10, 60)` limits. Answer generation uses a 45-second request timeout and one retry. No embedding/model fallback was introduced.
- Functions and their private subscriber deploy in `bom1`. New phase timestamps and logs separate claiming, generation, send and receipt. The UI identifies queue execution instead of presenting a stopped polling thread as a failed worker.
- `.vercelignore` excludes local credentials, `.env`, database backups, diagnostics, virtual environments and development assets. The CLI dry-run initially included these files; nothing was uploaded until the exclusion check passed.

## Measurements

Single sequential samples from the same development network against the production custom domain, using an ephemeral authenticated session removed after each measurement. These are observations, not load-test percentiles. Network/cold-instance variance remains visible.

| Request | Before, ms | After, ms | After handler, ms |
| --- | ---: | ---: | ---: |
| Session `/me` | 2,089 | 2,182 | 9.2 |
| Overview, first sample | 695 | 163 | 54.4 |
| Versions | 640 | 120 | 11.8 |
| Conversations | 1,511 | 271 | 25.4 |
| Jobs | 1,026 | 183 | 27.1 |
| Overview, repeat | 726 | 678 | 35.4 |
| WhatsApp status | 844 | 1,153 | 1,044.5 |
| Playground menu `2` | 3,840 (500) | 161 (200) | — |
| Playground address | 24,306 | 7,544 | Pipeline: 7,409 |

The answering pipeline itself was 7,243 ms before and 7,409 ms after for the address question. Removing infrastructure delays did not make the external embedding/answer providers instantaneous. The status endpoint still includes a live Linux WAHA health request; it is a separate latency source from database reads. The first session sample is also still above one second outside its 9.2 ms handler.

Raw sanitized timings are stored in ignored `data/diagnostics/2026-10-18-reliability-{baseline,improved}.json`.

## Verification

- 133 offline regression tests passed against disposable UTF-8 PostgreSQL on port 54585; no production database is used by these fixtures. The suite covers auth/revocation, HMAC, deduplication, off/on controls, ordering, lease expiry/fencing, concurrent writes and connection blackholes.
- Frontend TypeScript/Vite production build passed.
- Supabase migration `20261018063355_whatsapp_execution_leases` applied; role grants and RLS remain private to the backend.
- Production `dpl_EeoSZGLkLgwQfENFbNE9x5NUBT4i` contains both `services/backend/fastapi` and `services/backend/_py_subscribers/app-integrations-waha__queue`, deployed in `bom1`.
- The local development backend was stopped, and port 8000 confirmed closed. The WAHA session remains `WORKING`, pointing to the production custom-domain webhook, with matching HMAC and `message`/`message.ack` events.
- Production health returns 200. The webhook reports `execution_mode=vercel_queue` and `worker_running=false`. A bad HMAC returns 401; a valid diagnostic non-message event returns 200 without queueing or sending.
- **Pending:** a newly authorized real WhatsApp message must be matched to a leased consumer execution, a successful send and delivery acknowledgement while the local backend remains stopped. Do not call the WhatsApp recovery complete from a green build or session status alone.

## Operational limits

- Vercel Queues is in beta. Publishing happens after the inbox commit; a failed publish returns 503 so WAHA retries the same event. If notification failures outlast WAHA's retry window, the persisted queue needs reconciliation. There is no automatic replay of old failures or uncertain sends.
- Embedding `:free` limits and answering-provider latency can still delay or fail a question. Bounded retries preserve the configured embedding/index contract.
- This change makes WhatsApp execution durable. Long-running administration/evaluation jobs still use their existing executor and need a separate durable execution design before unattended long evaluations can be guaranteed on Vercel.
- Rolling back application code is possible; the added nullable columns should remain. Returning to the old polling implementation would also restore its serverless execution risk.

## References

- [Vercel Python Queues](https://vercel.com/docs/queues/python-sdk)
- [Python builder's explicit Services composition](https://github.com/vercel/vercel/blob/main/packages/python/src/index.ts)
- [Function regions](https://vercel.com/docs/functions/configuring-functions/region)
- [Supabase monitoring and debugging](https://supabase.com/docs/guides/monitoring-and-debugging)
