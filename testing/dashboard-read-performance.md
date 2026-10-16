# Dashboard read optimization — 2026-10-16

Historical first pass. The later implementation replaces the pipeline-based path;
see [the current measurements and checks](dashboard-subsecond-implementation.md).

## Scope

Optimize the existing FastAPI/PostgreSQL read paths and add TanStack Query v5.
Keep the current page navigation and shadcn tables. No database schema, knowledge,
RAG recipe, or WhatsApp delivery changes are required.

## Observations

Authenticated HTTP requests ran sequentially against `127.0.0.1:8000` and the
configured Supabase runtime connection. Only normal sign-in/session writes occurred;
no evaluation, ingestion, publishing, or outbound message was triggered by the probes.
Responses and credentials were not recorded.

| Operation | Before, seconds | After, seconds (two samples) |
| --- | ---: | ---: |
| Login | 11.108 | 2.767 / 5.349 |
| Session | 2.959 | 1.684 / 1.735 |
| Jobs | 4.162 / 7.247 | 2.886 / 6.456 |
| Versions | 12.606 | 2.670 / 3.634 |
| Overview | 11.970 | 2.263 / 2.263 |
| WhatsApp conversations | 7.295 | 2.654 / 2.640 |
| Settings | 9.310 | 2.600 / 5.225 |

The new job-detail endpoint returned HTTP 200 in 2.842 / 5.487 seconds. Its full
result is now fetched only when Inspect is opened.

These are exploratory samples, not p95 measurements or a controlled load benchmark.
Other dashboard requests and live WAHA webhooks were observed during measurement.
They show reduced typical read cost but do not establish a latency guarantee.

## Reduced work

- `/versions` previously downloaded and decoded approximately 9.66 MB of stored
  records/embeddings before returning an 8,823-byte summary. SQL now computes
  chunk counts and returns metadata only. PostgreSQL still parses records to count them.
- `/jobs` now returns 1,681 bytes, down from 279,016 bytes. Full stored results
  remain available through authenticated `/jobs/{id}`. The latest local evaluation
  artifact supplies reporting status after a LangSmith retry, with the database
  result retained as a fallback when the artifact is absent.
- `/overview` now returns 8,017 bytes, down from 285,352 bytes. SQL computes totals
  across all stored replies and fetches only eight recent rows and eight job summaries.
- Related settings and login operations share transactions; independent statements
  use Psycopg pipeline mode. Local timeouts, maintenance locking, CSRF, shared
  throttling, and session expiry remain enforced.

## Client policy

- One QueryClient survives section changes; cache stays in memory for the tab.
- Cached content remains visible during background refresh and temporary failures.
- Observed sections poll every 20 seconds; active jobs/indexing poll every 3 seconds.
  Background-tab interval polling is disabled. Dataset references and result details
  use invalidation, navigation/focus revalidation, or manual retry instead of polling.
- Successful writes invalidate affected resources. Observed terminal job transitions
  invalidate versions, datasets, history, overview, and inspected result details.
- Logout and session expiry clear private cached data and CSRF state. A failed
  initial session check keeps a retry screen for transient errors; only 401 signs out.

## Checks and limits

Frontend production build and lint completed; lint retained eight existing warnings.
Python sources parsed successfully, and the live read endpoints returned HTTP 200.
A regression case was added to `test_admin_workflow.py` for authenticated summary
and detail boundaries, including empty historical cases and updated reporting state;
the PostgreSQL regression suite was not run in this task.

Browser automation could not inspect the existing browser error tab because its URL
was blocked by the browser security policy. Cached navigation and hidden-tab polling
therefore have not been confirmed through browser interaction in this task.

## References

- [TanStack Query defaults and polling](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)
- [TanStack Query invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)
- [Psycopg pipeline mode](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html)
