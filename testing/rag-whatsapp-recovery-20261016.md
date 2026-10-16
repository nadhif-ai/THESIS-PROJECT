# Playground and WhatsApp recovery — 16 October 2026

## Root causes confirmed

1. **Stale runtime configuration after editing `.env`.** The backend started at
   14:59 Jakarta time, while `.env` was modified at 15:09. The live Providers UI
   reported `chatbot-nadhif`; a fresh configuration read reported `chatbot-avg`.
   Two failed WhatsApp items corresponded to the E5 index-compatibility exception.
   The restored index was verified through Pinecone: dimension 384, cosine, ready,
   with 95 vectors in the published knowledge namespace. Settings and provider
   clients are process-local caches; editing the file alone does not reload them.

2. **Chat downloaded complete embedding snapshots to select knowledge metadata.**
   Playground first loaded a complete version. RAG then selected a namespace by
   loading every version, and numeric menu replies repeated that selection. Eight
   snapshots contained 9,660,971 bytes of records. The full-version-list operation
   reproduced the 35-second driver timeout; the backend log associated the same
   call with Playground 503s and one failed WhatsApp item. These were database
   transfer failures, separate from the Pinecone incompatibility.

## Changes

- `store.version_info()` selects a single version by bound ID or namespace and
  returns metadata without embedding records. Existing full-record methods remain
  available for editing, indexing, and explicit chunk access.
- Playground validation, RAG selection, numeric menus, and retrieval's default
  namespace use metadata. Menus reuse the version already selected by RAG.
- Startup validates Pinecone compatibility before starting the WhatsApp worker.
  Index mismatch errors identify the configured index, actual dimension/metric,
  and the need to correct configuration and restart.
- No provider model, embedding model, index contents, published version, database
  schema, authentication policy, or delivery-retry policy was changed.

## Verification

- A regression reproduced HTTP 503 when full snapshot transfers were unavailable,
  then passed for the same Playground greeting and a synthetic WhatsApp delivery
  after the fix. All outbound calls in this test are stubbed.
- A startup regression failed before implementation and now rejects an incompatible
  index before the RAG instance becomes available.
- Published/default, explicit ID, namespace, and unknown namespace selection are
  covered; records remain available through the existing full-version method.
- **87 backend tests passed in 19.84 seconds**, with two existing deprecation
  warnings. **12 frontend retry/auth regression checks passed**. No frontend code
  changed in this fix.
- Live metadata transfer returned **476 bytes**, versus approximately 9.7 MB for
  the previous namespace selection. Warm measurements were **513.3 / 517.0 ms**;
  the initial connection measurement was 1,866.1 ms. This is not an end-to-end
  subsecond claim.
- The backend was restarted with `chatbot-avg`. `/health` returned 200 and the normal
  WAHA worker was running.
- Real browser Playground: `Hi admin` returned the welcome message. The business
  question `Min, alamat toko di mana?` returned an answer with **5 retrieved sources**
  and a LangSmith trace; the displayed RAG latency was **9.639 seconds**.
- The user sent the same business question to WhatsApp after the fix. The persisted
  item reached **sent**, had **one reply ID**, no error, and **ACK 2**. Inbound time
  was 15:17:46 Jakarta and sent time was 15:18:02. No recipient or message identity
  is included in this report.
- No new database or WhatsApp processing failure was logged during verification.

[Working Playground screenshot](playground-recovery-20261016.png)

The three historical failed messages remain failed and were not replayed or
deleted. Paid DeepEval suites, image delivery, and a prolonged outage/soak test
were not run. This fixes the reproduced configuration and transfer paths; it
does not guarantee provider or network uptime.

## Reproduce offline checks

Start a disposable UTF-8 PostgreSQL cluster on loopback port 54585, then run:

```bash
LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_admin_workflow.py testing/test_waha_integration.py testing/test_postgres_state.py testing/test_state_lifecycle.py testing/test_dashboard_reads.py testing/test_waha_reconciliation.py testing/test_dashboard_progress.py testing/test_state_migration.py testing/test_public_landing.py -q
node --experimental-strip-types --test testing/test_dashboard_query_retry.mjs
```

The tests create and remove synthetic databases. They do not use the configured
Supabase database, call paid generation/evaluation providers, or send real WhatsApp
messages.
