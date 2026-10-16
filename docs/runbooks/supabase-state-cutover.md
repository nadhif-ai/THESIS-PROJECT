# Administration state: SQLite → Supabase PostgreSQL

Scope: one business, one local FastAPI process and worker, existing Pinecone namespaces, existing authentication. This phase moves administration state. Knowledge files, evaluation artifacts and the embedding cache remain local. It does not make the application serverless or finish Vercel deployment.

## Connection and security

Confirmed project: `ndgfipshsgqmqnsmjhzz`. Tables live in the private `chatbot` schema. The browser never connects to this schema; it calls the existing authenticated FastAPI API. `anon` and `authenticated` have no access. Supabase Auth is not introduced.

Obtain the actual host from the project's Connect panel. These are placeholders, not usable credentials:

```dotenv
DATABASE_URL=postgresql://chatbot_app.PROJECT_REF:PASSWORD@POOLER_HOST:6543/postgres?sslmode=require
DATABASE_MIGRATION_URL=postgresql://postgres.PROJECT_REF:PASSWORD@SESSION_POOLER_HOST:5432/postgres?sslmode=require
```

`DATABASE_URL` must authenticate as `chatbot_app`, never `postgres`. Use a distinct generated password for this role; provision it locally through a privileged TLS SQL connection and verify it before updating `.env`. Never put the password in a shell argument, MCP prompt, migration file, frontend variable or report. Keep `.env` mode 0600. The migration credential belongs only on the operator's machine; do not upload it as a Vercel runtime variable.

The Python pool has at most two connections per process, transaction-local timeouts and disabled prepared statements for Supavisor transaction mode. Production connections require TLS. There is no SQLite fallback or schema creation during startup.

## Preconditions

1. Apply and test the committed schema on a disposable PostgreSQL database. Run the eight test files listed below. Do not use the production project for tests.
2. Confirm the project with scoped Supabase MCP and inspect existing schemas, grants and advisors. Refuse unexpected application data or an existing privileged `chatbot_app` role.
3. Preserve the current application/configuration, SQLite backup and working dependency environment privately. `data/migrations/` is ignored and must be owner-only. Retain existing artifact directories.
4. Prove installed WAHA GOWS history access: enumerate every chat page and message page to an empty page, including LID chats, with fixed timestamp filters and `downloadMedia=false`. Confirm a known stored inbound ID appears. A successful HTTP response alone does not prove coverage.
5. Confirm the published version and namespace exist in Pinecone without changing them. Inspect source jobs/inbox for active `running`, `generating` or `sending` work. Drain source activity before stopping it; do not globally reset statuses.

If a precondition fails, retain the original SQLite application and defer cutover. Maintenance is temporary chatbot unavailability. WAHA keeps its session and history, but webhook retries alone are not a delivery guarantee.

## Transfer

Run all commands from the repository root. The example backup path must be fresh on every run.

1. Stop incoming source requests, drain work, and stop every source writer. Record a UTC start watermark. If the backend was already offline, scan from the last verified source inbound receipt, not merely from the current time.
2. Make a consistent backup using SQLite's backup API, which includes committed WAL rows:

   ```bash
   venv/bin/python -m scripts.migrate_state snapshot --source data/admin.sqlite3 --output data/migrations/RUN/source.sqlite3
   ```

3. Apply `supabase/migrations/*.sql` explicitly to the confirmed project through the migration workflow. No real role password belongs in those SQL files. Verify the restricted runtime role connection.
4. Import and verify:

   ```bash
   venv/bin/python -m scripts.migrate_state import --snapshot data/migrations/RUN/source.sqlite3 --expected-project ndgfipshsgqmqnsmjhzz
   venv/bin/python -m scripts.migrate_state verify --snapshot data/migrations/RUN/source.sqlite3
   ```

   All eight tables import in one transaction. Ordered full-content digests distinguish NULL, text and numbers, preserve JSON text, and check the published selection. Counts alone are insufficient. Repeating an import with the same checksum is a no-op; changed live data is never overwritten. Verification reports subsequent differences separately. Unknown source schemas and nonempty unrelated destinations are rejected.

5. Start exactly one backend with the restricted DSN. Initial shared mode is `closed`; startup only checks schema, published selection and credentials. Validate `/health`, authenticated read views, existing history and job progress. There must be no business writes, model calls or test WhatsApp sends during this check.

## Intake and reconciliation

1. Enable intake only after verified import:

   ```bash
   venv/bin/python -m scripts.migrate_state control intake
   ```

   Incoming HMAC-validated events are persisted; jobs, playground generation and the WhatsApp processing worker remain paused. The first committed post-cutover write records a marker in the same transaction. The runtime role cannot change maintenance mode.

2. Confirm the backend is reachable through the actual WAHA callback, then record a UTC end watermark after intake is active. Scan the entire closed interval, with overlap automatically added at both ends:

   ```bash
   venv/bin/python -m scripts.reconcile_waha scan --start 2026-10-15T00:00:00+00:00 --end 2026-10-15T00:10:00+00:00 --output data/migrations/RUN/waha-scan.json
   venv/bin/python -m scripts.reconcile_waha replay --report data/migrations/RUN/waha-scan.json
   venv/bin/python -m scripts.reconcile_waha replay --report data/migrations/RUN/waha-scan.json --write
   ```

   Replace both example timestamps with recorded watermarks. Scan files contain private message data and are mode 0600. Console reports contain counts/digests only. Replay validates all messages first, then inserts missing inbound text messages atomically in intake mode. Original IDs, LID senders and receipt times are retained. Existing `sent` and `uncertain` rows are never requeued. Known outbound ACKs are updated monotonically when exposed by history; absent historic ACKs remain unknown. The tool never sends a message.

3. A completed write replay records evidence bound to the imported snapshot, session, interval and scan digest. A dry run cannot enable live mode. A conflict, malformed page, history gap or interrupted intake leaves processing paused; inspect private evidence and rescan the required interval. Closing maintenance invalidates prior reconciliation evidence.
4. Enable normal processing:

   ```bash
   venv/bin/python -m scripts.migrate_state control live
   ```

   Queued customer messages are now processed by the single existing worker. Check history, inbox status and job visibility. Obtain explicit recipient authorization before sending a separate test message. Retain the source SQLite and private backup unchanged.

## Rollback boundary

```bash
venv/bin/python -m scripts.migrate_state rollback-check
```

Before any post-cutover write, stop the replacement backend and restore the preserved application/configuration against the unchanged SQLite source. Reconcile messages from the maintenance interval into that original SQLite application before resuming. The PostgreSQL replay tool deliberately does not implement reverse transfer: a rollback is not complete until missing interval messages have been restored and verified in the source application.

After the marker is set, a stale SQLite snapshot cannot replace current state. Keep maintenance enabled and repair PostgreSQL. A reverse migration would require a separately verified transfer of every changed table. Changing the DSN alone is never a rollback.

## Verification and deployment boundary

The local fixtures use an explicitly disposable `chatbot_test_*` database on loopback port 54585; they never use production credentials. Start a disposable local PostgreSQL server there (for example with Docker), then run the suite:

```bash
docker run --rm --name chatbot-state-test -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:54585:5432 postgres:17
```

This trust-authenticated instance is for loopback synthetic tests only. Do not use production data or expose it to other hosts. Test command:

```bash
venv/bin/python -m pytest testing/test_postgres_state.py testing/test_state_migration.py testing/test_waha_reconciliation.py testing/test_state_lifecycle.py testing/test_admin_workflow.py testing/test_dashboard_progress.py testing/test_waha_integration.py testing/test_public_landing.py -q
```

Retain redacted rehearsal/cutover reports under `data/migrations/`. Use Supabase advisors after schema changes. Persistent PostgreSQL solves shared state; Vercel still needs durable execution for evaluation/indexing and WhatsApp jobs, remote artifact storage, an embedding runtime strategy, and deployment routing. Do not deploy the current in-process executor/daemon unchanged to a serverless function.

### Observed hosted details

The applied schema migration is `20261015163525_administration_state.sql`; its version matches the actual Supabase MCP migration history. Keep local and hosted migration identities aligned before future CLI pushes.

The hosted connection's `extra_float_digits=0` rounds floating-point text output. Content verification uses PostgreSQL binary reads to compare the exact stored values, including session expiry and latency. Do not weaken verification to rounded comparisons.

Advisors also reported existing EXECUTE grants on the platform's `public.rls_auto_enable()` event-trigger function ([anonymous grant advisory](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable), [authenticated grant advisory](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable)). This existing function was inspected and left unchanged; it is separate from the private chatbot schema. The informational missing-primary-key notice on the short-lived `login_attempts` table does not affect the protected eight migrated tables. Unused-index notices on a new installation do not justify deleting the queue/history indexes.

Schema version 2 adds separate maintenance-start and intake-resumption timestamps while retaining the original cutover and first-write history. Every reopening requires a scan beginning no later than the current maintenance boundary and ending after intake resumed; an old scan cannot authorize a later outage. Control refuses to interrupt a generating/sending WhatsApp item or running job; drain those first. A restart or intake interruption requires a new closed interval and scan.

An ambiguous image send (timeout, connection failure or missing provider reply ID) keeps the inbox item `uncertain` even if its text fallback succeeds. Known reply IDs remain available for inspection. A definitive image rejection can still fall back to a normally sent text reply. Never automatically retry the uncertain item.
