# Dashboard under one second: research and proposed stages

Implementation follow-up: [completed first slice and measured limits](dashboard-subsecond-implementation.md).
The research-only findings below are retained as the record preceding implementation.

Date: 2026-10-16 (Asia/Jakarta). Research only; no application, configuration, or database changes.

Exa recheck: completed on the same date after Exa MCP became available. The earlier
measurements below are preserved; this review did not rerun benchmarks.

## Goal and evidence

Cover login, the first visit to every section, manual/background refresh, and returning to a visited section. Distinguish an immediate UI response from fresh data arriving. Playground generation, ingestion, and DeepEval should acknowledge work quickly and show progress; this is not a proposal that LLM or evaluation computation finishes within one second.

The previous [read optimization report](dashboard-read-performance.md) records exploratory HTTP samples, not p95. The current read path still checks an opaque, revocable session in its own store operation before performing another operation for data: [routes.py](/Users/royanrosyad/Nayor/Nadhif-TA/app/admin/routes.py:37), [store.py](/Users/royanrosyad/Nayor/Nadhif-TA/app/admin/store.py:175). Each store operation obtains a pooled connection, checks it, sets local timeouts, and ends a transaction: [store.py](/Users/royanrosyad/Nayor/Nadhif-TA/app/admin/store.py:41).

The coordinator supplied this new read-only protocol probe. It used one persistent TLS connection; no application/configuration/schema changes occurred. The configured pooler points to `ap-south-1:6543`; the actual project region was not verified through Management API, whose lookup failed.

| Phase | Three samples, milliseconds |
| --- | ---: |
| Checkout health check | 446 / 454 / 427 |
| Implicit BEGIN plus pipeline of two SET LOCAL statements | 857 / 827 / 845 |
| Indexed lookup for a nonexistent session | 415 / 452 / 392 |
| COMMIT | 390 / 441 / 453 |
| Whole store operation | 2,107 / 2,175 / 2,117 |

One fresh TLS connection took 3,146 ms. A synthetic local scrypt operation took approximately 36 ms. These are three diagnostic samples, not p95 or a geography-controlled comparison. They include network, pooler, and protocol waits; they do not isolate PostgreSQL execution time. A separate real HTTP request must be traced to attribute pool waiting and overlapping traffic. Nevertheless, multiple serial protocol waits already prevent this exact local read path from reaching one second. Further shrinking the JSON response alone cannot remove those waits.

The coordinator also ran read-only `EXPLAIN ANALYZE BUFFERS FORMAT JSON` on the current SQL, applying `supabase-postgres-best-practices`:

| Current query | Server execution, ms | Planning, ms | Rows | Shared buffer hits / reads |
| --- | ---: | ---: | ---: | ---: |
| Version metadata, newest first | 120.975 | 0.073 | 8 | 821 / 0 |
| Job summaries, newest 100 | 5.359 | 0.083 | 5 | 43 / 0 |
| WhatsApp history, newest 200 | 0.143 | 0.092 | 103 | 23 / 0 |

These execution times exclude result delivery and differ from the preceding protocol timings. With these small datasets, speculative new indexes are not the primary current fix. Version metadata still parses approximately 9.66 MB of `records::json` to count chunks; storing `chunk_count` when saving/indexing a version is one concrete later optimization, requiring compatible schema/source migration. It is not implemented. Preserve bounded connections and transaction-pooler compatibility (`prepare_threshold=None`); increasing `max_size` without measuring demand and the database connection budget is not the recommendation.

## Material correction from the Exa recheck

Current Supabase documentation explicitly states that its shared transaction pooler
does not support query pipelining. Direct connections and session mode support it.
This is documented alongside the port-6543 shared transaction endpoint and its
transaction-mode limitations. Generic Psycopg pipeline support is not proof that an
intermediate pooler supports it. [Supabase connection methods and limitations](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Psycopg pipeline semantics](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html).

The current application contains seven `db.pipeline()` scopes in
[store.py](/Users/royanrosyad/Nayor/Nadhif-TA/app/admin/store.py:89), while its
configured endpoint is the shared transaction pooler. Earlier probes succeeded for
limited operations; they did not prove complete compatibility. No production
failure or mismatched result has been established by this research. Resolve this
documented compatibility risk before extending pipeline-based optimization.

For the future serverless deployment, keep the documented transaction-pooler model
and replace reliance on pipelining with compatible parameterized SQL/read
consolidation. Preserve transaction-local timeouts, atomic writes, session checks,
maintenance guards, and disabled automatic prepared statements. For a persistent
local backend, direct IPv6 or shared session mode is a separately documented option;
changing connection mode is not implemented here. [Supabase connection selection](https://supabase.com/docs/guides/database/connecting-to-postgres).

## What the current documentation supports

### 1. Keep FastAPI; place compute near its data

Vercel Functions can select their execution region. Vercel recommends proximity to the database; static assets have independent CDN distribution. Its documented default for new projects is `iad1`, so an unconfigured deployment is not proof of colocation. If the configured pooler reflects a Mumbai database, investigate `bom1`; confirm the actual Supabase region and deployed function region first. A single region is sufficient for this application. [Vercel region configuration](https://vercel.com/docs/functions/configuring-functions/region), [region identifiers](https://vercel.com/docs/regions).

FastAPI runs as one Vercel Function. Fluid Compute supports concurrent Python invocations in an instance and reduces cold starts. It does not promise every request is warm or subsecond. Correction to the initial review: Fluid's bytecode-caching subsection describes Node.js 20+, but current Python runtime documentation separately describes precompiled Python bytecode. Do not conclude that Python has no bytecode optimization. Heavy import/startup work and a new database connection still need separate measurements. [FastAPI on Vercel](https://vercel.com/kb/guide/ship-a-fastapi-app-on-vercel), [Fluid Compute](https://vercel.com/docs/fluid-compute), [Python runtime](https://vercel.com/docs/functions/runtimes/python).

### 2. Extend the existing TanStack Query cache

Prefetch likely destinations on navigation intent, such as sidebar focus/hover, after authentication. Reuse the existing query keys and client. Prefetching pays for a request earlier; it does not shorten an uncached API request. Bound prefetch concurrency so opening the app does not fill a two-connection pool with every section at once. Keep memory-only cache, invalidation, logout clearing, and cached content during refresh. [TanStack prefetching](https://tanstack.com/query/latest/docs/framework/react/guides/prefetching).

Use a mutation's returned object to update the relevant cache immediately. Optimistic UI is suitable only where rollback is clear; publishing knowledge, confirming delivery, changing credentials, and completing evaluation still require server confirmation. The current Query dependency is v5; choose APIs against the installed version because online `latest` documentation can evolve. [Optimistic updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates), [installed dependency](/Users/royanrosyad/Nayor/Nadhif-TA/frontend/package.json:17).

The Exa recheck also verified that current v5 guidance prefers
`queryClient.query(...).catch(...)` for optional prefetch; `prefetchQuery` is
deprecated. The installed `@tanstack/query-core` 5.104.3 source contains `query()`
and the deprecation annotation, so this improvement needs no dependency upgrade.
Optional prefetch must handle rejected promises, use the same resource keys as
`useResource`, consume cancellation signals, and keep concurrency bounded.
[Current v5 prefetch guide](https://tanstack.com/query/v5/docs/framework/react/guides/prefetching),
[installed implementation](/Users/royanrosyad/Nayor/Nadhif-TA/frontend/node_modules/@tanstack/query-core/src/queryClient.ts:594).

Router can coordinate route loading; Table manages rows and state while the application supplies fetching. Neither removes the measured PostgreSQL protocol waits. A new router, table library, or framework rewrite is therefore outside the first performance stage. [Router external data loading](https://tanstack.com/router/latest/docs/guide/external-data-loading), [Table client/server responsibilities](https://tanstack.com/table/latest/docs/guide/client-side-vs-server-side).

### 3. Optional shared Redis read cache, after colocation and profiling

Managed Upstash Redis is compatible with a Python FastAPI backend on serverless. Its `upstash-redis` SDK uses HTTP/REST rather than a long-lived Redis TCP connection. REST simplifies this deployment model; it is not evidence that REST is faster than a healthy persistent TCP connection. Locate the cache near the backend; a distant cache adds another network trip. [Python SDK](https://upstash.com/docs/redis/sdks/py/overview), [placement](https://upstash.com/docs/redis/overall/getstarted).

Use a small cache-aside implementation for repeated overview, version metadata, settings, and terminal job summaries only if the measured miss path still warrants it. Suggested experimental TTLs are 5–15 seconds for summaries and at most 1–3 seconds for active progress, not agreed freshness requirements. Start with one useful endpoint. PostgreSQL remains authoritative. Invalidate after the database commit and on worker-originated changes; include environment, business/authorization scope, filters, and pagination in keys. TTL plus the browser's refresh interval determines the possible stale window. [Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/).

If concurrent misses become material, use bounded fill coordination with an expiring owner token and ownership-checked release. Do not reuse that best-effort mechanism as a WhatsApp delivery lock. Batch independent Redis commands when useful; REST pipelines reduce HTTP round trips but are not atomic. [Redis stampede mitigation](https://redis.io/docs/latest/develop/use-cases/cache-aside/), [Upstash REST pipelines](https://upstash.com/docs/redis/features/restapi).

Authenticate before returning private cached data. Keep cache credentials server-only and fail closed on authorization errors. Cache failures can fall back to the authoritative database for ordinary reads; that is distinct from allowing an unverified session. Caching only response payloads still leaves the current session database lookup, so Redis alone cannot fix the current login/session latency. Do not put private admin responses into a public CDN cache. Upstash documents eventual replication and same-client read-your-writes; that is not a cross-client immediate revocation guarantee. [Security](https://upstash.com/docs/redis/features/security), [consistency](https://upstash.com/docs/redis/features/consistency), [read-your-writes](https://upstash.com/docs/redis/howto/readyourwrites).

### 4. Supabase Auth is a separate future decision

Asymmetric JWT verification with cached JWKS can avoid a remote Auth call for each request. It also changes the session model: signature validation does not prove a session has not been revoked, and immediate sign-out detection requires a session existence check or another explicit revocation design. Do not replace the current revocable session with a short TTL auth cache as an incidental speed fix. Supabase Auth was explicitly excluded from the approved migration spec. [Python verified claims](https://supabase.com/docs/reference/python/auth-getclaims), [session revocation](https://supabase.com/docs/guides/auth/sessions), [approved exclusions](/Users/royanrosyad/Nayor/Nadhif-TA/docs/superpowers/specs/2026-10-15-supabase-administration-state-design.md:40).

## Recommended order and acceptance budgets

These are proposed targets, not benchmark results or service guarantees.

| Stage | Smallest work | Proposed budget / decision gate |
| --- | --- | --- |
| 1 | Resolve the transaction-pooler/pipelining mismatch; trace auth, connection acquisition/check, transaction setup, SQL, commit, and serialization. Consolidate compatible reads and review pool/WAHA contention without weakening timeouts, CSRF, maintenance, or revocation. | Identify p50/p95 by endpoint; no blanket pool increase or connection-mode switch. |
| 2 | Deploy a preview backend next to the confirmed Supabase region; compare warm and cold samples separately. | Warm login and fresh read APIs p95 <1,000 ms from the intended client network. If missed, use phase timings to choose the next change. |
| 3 | Intent prefetch, independent widget loading, immediate pending state, and cache updates from mutation responses using existing Query. | Cached section switch target 50–150 ms; immediate interaction acknowledgment <100 ms. First visits and F5 are measured separately. |
| 4 | Add managed Redis for a demonstrated repeated-read bottleneck only if stages 1–3 miss the target. | Warm authenticated cache hits target 100–400 ms; cache misses remain a separate measured class. |

Measure the full user sequence: login → first overview → first visit to every section → return to sections → manual refresh → mutation → refreshed result → logout/session expiry. Test light concurrent traffic and an active WAHA/job state. Record warm/cold, hit/miss, p50/p95, errors, payload bytes, and client-to-region location. LLM and evaluation completion times are separate outcomes; a fast job acknowledgment must not be reported as fast completion.

### First implementation slice after the agreed research

1. Make the seven persistence pipeline scopes compatible with the selected pooler,
   preserving transactional correctness and timeout/error behavior for all callers.
2. Add request-phase timing and pool statistics, consolidate related read operations,
   and remove repeated JSON parsing for metadata chunk counts with a compatible
   migration/backfill design.
3. Add bounded intent prefetch with the installed Query API and independent loading
   of evaluation widgets. Preserve memory-only caching and logout invalidation.

This slice provisions no Redis, changes no auth provider, and does not deploy the
application. A colocated preview follows the remaining deployment-readiness work;
Redis is gated on the resulting measurements.

## Research limits

Exa was unavailable during the initial review. It became available for this recheck:
one low-effort Exa Agent run (`agent_run_20783d3ef22640198908ee365f8e7e18`) and direct
Exa fetches of official Supabase, Psycopg, Vercel, and TanStack documentation were
used, with Context7 corroboration for Psycopg. Search findings were checked against
primary pages and installed source. This note adds no dependency, provisions no
service, and changes no runtime behavior. Region colocation, production cold-start
distribution, current plan eligibility, actual cache hit rate, and browser render
timings are not verified by this research. No new benchmark or load/regression test
suite was run. The pipeline compatibility issue is identified here and remains
unresolved in application code at the end of this research-only request.
