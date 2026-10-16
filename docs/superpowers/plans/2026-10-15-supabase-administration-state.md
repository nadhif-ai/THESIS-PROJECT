# Supabase Administration State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execution method: Native in this chat, approved by the user.

**Goal:** Move all existing chatbot administration state from SQLite into the confirmed Supabase PostgreSQL project while preserving login, knowledge publication, conversations, job results, and WhatsApp delivery state.

**Architecture:** Deepen the existing `app/admin/store.py` persistence module with a PostgreSQL adapter and domain operations; move SQL out of its callers. Keep the current local execution model during this phase. Use explicit migrations and client-side snapshot transfer, followed by maintenance reconciliation, rather than changing schema or resetting jobs during startup.

**Tech Stack:** Python 3.12, existing FastAPI, Psycopg 3.3.6, psycopg-pool 3.3.3, Supabase PostgreSQL transaction pooler, standard-library SQLite/JSON/hashlib, existing pytest fixtures, and existing WAHA GOWS HTTP client. Supabase CLI 2.121.0 is the schema authoring tool; discover commands through `--help` before use.

**Spec:** `docs/superpowers/specs/2026-10-15-supabase-administration-state-design.md`.

## Global Constraints

- Supabase project `ndgfipshsgqmqnsmjhzz` is the only authorized production destination.
- Use a dedicated `chatbot` schema that is not exposed through the Supabase Data API.
- Preserve IDs, password hashes, session expiry, job results, Pinecone namespaces, and the selected published knowledge version.
- Keep JSON-bearing source fields as text for this phase to avoid unrelated serialization changes.
- Start with at most two client connections per instance.
- Ordinary startup must not run schema DDL, import historical rows, generate credentials, seed baseline knowledge, ingest Pinecone vectors, or publish a version.
- A timeout after a provider send remains `uncertain`; do not promise exactly-once delivery or automatically resend an uncertain item.
- Keep one local backend worker process after this phase.
- Do not activate multiple Vercel workers or claim reliable serverless job execution until the durable execution phase is complete.
- Keep multilingual E5-small, 384 dimensions, prefixes, normalization, chunking settings, prompts, model choices, and retrieval settings unchanged.
- Preserve existing uncommitted user work. Do not reset/clean the checkout, stage broad directories, or commit unrelated changes.
- Tests in this plan use disposable PostgreSQL and synthetic records. No model evaluation, customer send, production import, or service restart is hidden inside a test command.

## Review Focus

1. Conversation ID gaps and reset markers: the next generated ID must exceed imported IDs, and reset must retain audit history. Task 2 and Task 5 own these checks.
2. Empty or unrelated destinations: a wrong project, mismatched schema, or different completed snapshot must fail without overwriting anything. Task 5 owns these checks.
3. Partial progress and acknowledgement races: a concurrent update must not erase another progress field or lower a receipt. Task 3 owns these checks.
4. Maintenance pagination: new LID chats, duplicate pages, timestamp overlap, and exhausted history must not silently omit or requeue messages. Task 6 owns these checks.
5. Restarts and rollback after new writes: startup must leave active rows alone, and reverting to an old SQLite snapshot must be blocked after PostgreSQL accepts new state. Task 4 and Task 7 own these checks.

## Current preflight facts

The previous inventory found 226 rows in eight application tables; counts must be recollected from the final snapshot. The scoped MCP reached the confirmed project and found no `public` tables; the intended `chatbot` schema still needs inspection. `DATABASE_URL` and `DATABASE_MIGRATION_URL` are absent from the local `.env` at planning time. Docker and psql executables are installed; availability of the Docker daemon has not been established. No production schema or data has been changed.

The plan may be implemented and tested locally before live credentials are available. Production transfer cannot run without a verified privileged SQL connection and an application-role connection. MCP access is not a substitute for the runtime connection string.

## File responsibilities

| Path | Responsibility |
| --- | --- |
| `app/admin/store.py` | PostgreSQL pool, domain state operations, transaction and access-error handling. |
| `app/admin/routes.py` | Existing HTTP contracts; calls persistence operations without SQL. |
| `app/admin/jobs.py` | Existing local execution; calls job persistence operations without SQL. |
| `app/integrations/waha.py` | Existing HMAC/transport behavior; calls inbox/receipt operations without SQL. |
| `app/main.py`, `app/dependencies.py` | Readiness-only startup, pool shutdown, maintenance-aware worker startup. |
| `app/config/settings.py`, `.env.example`, `requirements.txt` | Backend DSNs, maintenance configuration, pinned PostgreSQL dependencies. |
| `supabase/config.toml`, `supabase/migrations/` | Explicit versioned schema produced through the CLI workflow. |
| `scripts/migrate_state.py` | Preflight, consistent snapshot, atomic import, content verification, and cutover checks. |
| `scripts/reconcile_waha.py` | Read-only history scan and explicit validated insertion of missing interval events. |
| `testing/conftest.py`, `testing/test_postgres_state.py`, `testing/test_state_migration.py`, `testing/test_waha_reconciliation.py` | Disposable database fixtures and behavior checks. |
| Existing workflow/progress/WAHA tests | Retain behavior assertions while replacing SQLite setup. |
| `README.md`, `docs/runbooks/supabase-state-cutover.md` | Local setup and exact operational cutover/rollback instructions. |

Do not introduce a generic repository hierarchy or a new framework. SQL and connection helpers stay private to the persistence module. Migration tooling uses its own privileged SQL connection and never imports the application lifespan.

## Task 1: Explicit schema, least privilege, and disposable PostgreSQL

**Files:** Modify `requirements.txt`; create the CLI-generated migration in `supabase/migrations/`, `supabase/config.toml`, `testing/conftest.py`, and `testing/test_postgres_state.py`.

**Interfaces:**
- Consumes: the eight source table definitions in `app/admin/store.py` and `app/integrations/waha.py`.
- Produces: schema `chatbot`, backend role `chatbot_app`, schema version `1`, and a `pg_workspace` fixture. The fixture yields a synthetic PostgreSQL database with the production table names and a disposable `DATA_DIR`; it must never target the Supabase production project.
- Internal bookkeeping tables: `schema_migrations(version integer primary key)`, `state_imports(snapshot_sha256 text primary key, manifest text not null, imported_at text not null)`, `runtime_control(id integer primary key check(id=1), mode text check(mode in ('closed','intake','live')), cutover_started_at text, first_live_write_at text)`, and `login_attempts(client_hash text, attempted_at double precision)`.

- [ ] Discover CLI commands and initialize only the local configuration:

```bash
npx --yes supabase@2.121.0 --help
npx --yes supabase@2.121.0 init --help
npx --yes supabase@2.121.0 migration new --help
npx --yes supabase@2.121.0 init
npx --yes supabase@2.121.0 migration new administration_state
```

Use the filename emitted by `migration new`; do not invent a timestamp. Do not link/push to production in this task. Enable no frontend Data API access for `chatbot`.

- [ ] Pin `psycopg[binary]==3.3.6` and `psycopg-pool==3.3.3`. Prepare a disposable local PostgreSQL database using an available local Docker daemon or an explicitly supplied test database. Bind a Docker database port to `127.0.0.1` only. Fail instead of silently skipping PostgreSQL behavior checks when no test target exists.
- [ ] Add the initial schema/security check:

```python
def test_application_role_and_schema_are_private(pg_workspace):
    with pg_workspace.admin_connection() as db:
        assert db.execute("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='chatbot_app'").fetchone()[0] is False
        assert db.execute("SELECT has_schema_privilege('anon','chatbot','USAGE')").fetchone()[0] is False
        assert db.execute("SELECT has_schema_privilege('authenticated','chatbot','USAGE')").fetchone()[0] is False
        assert db.execute("SELECT count(*) FROM pg_tables WHERE schemaname='chatbot' AND NOT rowsecurity").fetchone()[0] == 0
```

For the local fixture only, provision synthetic `anon`/`authenticated` roles when absent so the access assertions represent Supabase roles. Reject a non-loopback production host in this fixture. Run `venv/bin/python -m pytest testing/test_postgres_state.py -q`; initial failure must be missing schema/role.

- [ ] Build the eight table definitions by copying every source column, preserving field names and text serialization. Map conversation ID to `bigint generated by default as identity primary key`; map session expiry and latency to double precision. Use text for other source strings/JSON and preserve nullable source fields. Use composite primary key `(session,message_id)` and an acknowledgement check `ack BETWEEN -1 AND 4` after source validation. Add indexes on `(session_id,id)` for conversations, `(session,status,created_at,message_id)` for inbox, and a partial unique index allowing one `versions` row with status `published`.
- [ ] Add role creation with an existing-role safety check. A new `chatbot_app` role has LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS, and no default public privileges. Set a password only through local privileged provisioning; never commit one. If an existing role has unexpected privileges, stop rather than silently altering a possibly unrelated role.
- [ ] Revoke application-schema access from PUBLIC, anon, and authenticated. Grant the application role usage and the exact SELECT/INSERT/UPDATE/DELETE privileges its domain operations use; grant sequence usage. Give bookkeeping tables narrower access: runtime may SELECT schema/import records and runtime control; its only bookkeeping write is column-level UPDATE of `runtime_control.first_live_write_at`. It cannot change mode, cutover watermark, migration history, or import records. Enable RLS on all owned tables, with backend-role policies matching granted operations. Example policy:

```sql
CREATE POLICY backend_rows ON chatbot.conversations
FOR ALL TO chatbot_app USING (true) WITH CHECK (true);
```

Apply the same backend-role predicate only where runtime access is required; bookkeeping tables receive a SELECT policy. Runtime control also gets an UPDATE policy whose WITH CHECK requires `first_live_write_at IS NOT NULL`, so the marker cannot be cleared by the runtime role. Column grants still deny mode/watermark changes. The private schema is the additional protection, not a substitute for grants. No SECURITY DEFINER functions are needed.
- [ ] Apply and iterate the schema on the disposable local database; use direct SQL while iterating. Inspect local schema and privileges, then retain the clean migration file. Run relevant local advisors via the discovered CLI command, or document the absence of that local advisor capability and perform the catalog checks above. Run the schema/security checks again. Expected: application role works, external roles are denied, schema version is 1, control mode is closed, all eight business tables are empty.
- [ ] Commit only the task's exact files, using the CLI-emitted migration filename.

## Task 2: PostgreSQL persistence, auth, and publication

**Files:** Modify `app/admin/store.py`, `app/admin/routes.py`, `app/config/settings.py`, `.env.example`; extend `testing/test_postgres_state.py`; adapt `testing/test_admin_workflow.py` fixtures.

**Interfaces:**
- Retain existing `now`, `data_path`, `hash_password`, `get_setting`, `set_setting`, `versions`, `version`, `save_version`, `publish`, `record_conversation`, `conversations`, `prompt_turns`, and `clear_session` argument/return behavior.
- Add `open_pool() -> None`, `close_pool() -> None`, `check_ready() -> None`.
- Add `get_user(name: str) -> dict | None`, `get_session(token_hash: str, at: float) -> dict | None`, `create_session(token_hash: str, expires: float, csrf: str) -> None`, `delete_session(token_hash: str) -> None`.
- Add `login_allowed(client_hash: str, at: float) -> bool`, `record_login_failure(client_hash: str, at: float) -> None`, `clear_login_failures(client_hash: str) -> None`.
- Add `get_runtime_mode() -> str`; mode reads are shared and default to failure, not automatic live operation.
- All connections and SQL remain private. Domain dictionaries remain JSON-compatible as existing callers expect.

- [ ] Add explicit `database_url` and `database_migration_url` settings, defaulting to empty values so migration tooling can inspect SQLite without starting PostgreSQL. Runtime `open_pool()` rejects a missing database URL. Administrative DSN is never used as the runtime fallback.
- [ ] Add failing auth/expiry, publication, and ID-gap checks, preserving the current HTTP tests:

```python
def test_expired_session_is_not_extended(pg_workspace):
    store.create_session('old-token-hash', 1.0, 'synthetic-csrf')
    assert store.get_session('old-token-hash', 2.0) is None

def test_reset_retains_audit_rows(pg_workspace):
    store.record_conversation('wa-test', 'whatsapp', 'question', 'answer')
    assert store.clear_session('wa-test') is True
    assert store.prompt_turns('wa-test') == []
    assert len(store.conversations(channel='whatsapp')) == 1
```

Run `venv/bin/python -m pytest testing/test_postgres_state.py testing/test_admin_workflow.py -q`; verify the expected missing-operation/SQLite setup failures before implementation.

- [ ] Replace SQLite connections with a private pool. The implementation shape is:

```python
ConnectionPool(
    conninfo=settings.database_url,
    min_size=0, max_size=2, timeout=5, open=False,
    kwargs={'row_factory': dict_row, 'prepare_threshold': None,
            'connect_timeout': 5, 'sslmode': 'require'},
    check=ConnectionPool.check_connection,
)
```

The local test connection explicitly overrides TLS requirements only for loopback. Create/open once under a lock, close on shutdown, never emit its DSN in exceptions. Each checkout starts a bounded transaction with `SET LOCAL statement_timeout='30s'` and `SET LOCAL lock_timeout='5s'`. Use schema-qualified SQL, `%s` parameters, commit on success and rollback on error.

- [ ] Translate retained operations to real PostgreSQL upserts (`ON CONFLICT ... DO UPDATE`), not SQL string rewriting. Keep JSON decoding/encoding in this module. Use `RETURNING` for generated IDs. Do not perform filesystem creation when opening a database connection; keep `data_path()` only for deferred local artifacts.
- [ ] Make publication atomic by locking the single runtime-control row, checking the selected version is ready/published, updating old/new status, and updating `settings.published_version` in one transaction. The partial unique index is a second guard. A failed ready check rolls back all changes.
- [ ] Replace auth SQL in routes with the named operations. Preserve existing cookie path, password algorithm, origin check, CSRF, session duration, and error responses. Hash the client identity for login-attempt rows; preserve ten failures in a five-minute window. Serialize updates for one identity using a transaction-scoped advisory lock, and expire only old rows in that operation. Never hold a connection while executing scrypt.
- [ ] Add checks for concurrent publish, reset against nonconsecutive IDs, credential verification against copied hashes, and shared throttling across independent callers. Run the two test files; expected pass with a real PostgreSQL fixture and mocked Pinecone/LLM calls. Commit exact task files.

## Task 3: Job and WhatsApp state callers

**Files:** Modify `app/admin/store.py`, `app/admin/jobs.py`, `app/integrations/waha.py`; adapt `testing/test_dashboard_progress.py` and `testing/test_waha_integration.py`; extend `testing/test_postgres_state.py`.

**Interfaces:**
- `list_job_rows(limit: int = 100) -> list[dict]`, `create_job_row(identifier: str, kind: str, payload: dict) -> None`, `set_job_state(identifier: str, status: str, result: dict | None = None, error: str | None = None) -> None`, `merge_job_progress(identifier: str, fields: dict) -> None`.
- `enqueue_inbox(session: str, message_id: str, sender: str, body: str, received_at: str | None = None) -> bool`, `claim_inbox(session: str) -> dict | None`, `update_inbox(session: str, message_id: str, fields: dict) -> None`, `record_ack(message_id: str, ack: int) -> None`, `whatsapp_observations(session: str) -> dict`, `get_inbox(session: str, message_id: str) -> dict | None`.
- Retain `jobs.list_jobs/create/update_progress/run` and `waha.enqueue/update/status` observable behavior. Those callers translate to the domain operations above; no SQL remains in them.

- [ ] Add the concurrent-claim and monotonic-ack checks:

```python
def test_only_one_caller_claims_one_message(pg_workspace):
    from concurrent.futures import ThreadPoolExecutor
    store.enqueue_inbox('asia-chatbot', 'message-1', '123@lid', 'question')
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(store.claim_inbox, ['asia-chatbot'] * 2))
    assert sum(row is not None for row in rows) == 1

def test_receipt_does_not_move_backwards(pg_workspace):
    store.record_ack('reply-1', 3)
    store.record_ack('reply-1', 1)
    with pg_workspace.admin_connection() as db:
        assert db.execute("SELECT ack FROM chatbot.whatsapp_receipts WHERE message_id='reply-1'").fetchone()[0] == 3

def test_progress_merge_preserves_both_callers_fields(pg_workspace):
    from concurrent.futures import ThreadPoolExecutor
    store.create_job_row('progress-1','evaluate',{})
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda fields: store.merge_job_progress('progress-1',fields),
                      [{'completed':1},{'total':3}]))
    progress=next(row for row in store.list_job_rows() if row['id']=='progress-1')['progress']
    assert progress['completed'] == 1 and progress['total'] == 3
```

Run the target checks and observe missing operations before implementation.

- [ ] Persist queued jobs before submitting local execution. Keep existing progress merging, partial metric errors, sanitized failure text, and result decoding. Merge progress under a row lock so parallel updates to distinct fields both survive. `set_job_state` never erases observed progress.
- [ ] Implement atomic claim using one statement:

```sql
WITH candidate AS (
  SELECT pending.session,pending.message_id FROM chatbot.whatsapp_inbox AS pending
  WHERE pending.session=%s AND pending.status='queued'
    AND NOT EXISTS (
      SELECT 1 FROM chatbot.whatsapp_inbox AS active
      WHERE active.session=pending.session AND active.sender=pending.sender
        AND active.status IN ('generating','sending')
    )
  ORDER BY pending.created_at,pending.message_id LIMIT 1 FOR UPDATE SKIP LOCKED
)
UPDATE chatbot.whatsapp_inbox AS inbox
SET status='generating',updated_at=%s
FROM candidate
WHERE inbox.session=candidate.session AND inbox.message_id=candidate.message_id
RETURNING inbox.*;
```

Single-process execution remains required. Prevent claiming a later item when that conversation already has a generating/sending item; do not extend this into a multi-worker queue implementation. Enqueue uses `ON CONFLICT DO NOTHING`; update fields are selected from an explicit allowlist. Receipt updates use `GREATEST(existing_ack, excluded_ack)`.
- [ ] Replace worker `SELECT` with `claim_inbox`. Remove schema DDL and global restart updates from `waha.initialize`; make it a readiness check or remove it and update all callers/tests. Preserve HMAC and media/text transport handling, including an already-persisted answer and uncertain send status.
- [ ] Add concurrent progress merge, unknown update-field rejection, duplicate-ID content conflict, preserved LID, and no-resend assertions. Preserve existing progress/WAHA test assertions while changing raw SQLite fixture SQL to PostgreSQL setup/domain operations. Run `venv/bin/python -m pytest testing/test_postgres_state.py testing/test_dashboard_progress.py testing/test_waha_integration.py -q`. Expected pass without network sends. Commit exact task files.

## Task 4: Readiness-only startup and maintenance controls

**Files:** Modify `app/admin/store.py`, `app/dependencies.py`, `app/main.py`, `app/admin/routes.py`, `app/admin/jobs.py`, `app/integrations/waha.py`; create `testing/test_state_lifecycle.py`.

**Interfaces:**
- `check_ready()` checks connection, schema version 1, and the selected published version without business writes.
- Private write transaction helper takes a purpose of `administration`, `intake`, or `execution` and checks runtime control within the same transaction.
- Runtime modes: `closed` rejects all business writes, `intake` allows only inbox/receipt intake and explicit operator reconciliation, `live` permits normal behavior.
- `scripts/migrate_state.py control closed|intake|live` (implemented in Task 5) is the privileged control path. Runtime role cannot change the mode. Existing HTTP error contracts gain a sanitized 503 maintenance response, not a new public control endpoint.

- [ ] Add checks that startup leaves active records unchanged and never invokes bootstrap:

```python
def test_startup_does_not_recover_another_workers_job(pg_workspace, monkeypatch):
    from app import dependencies
    store.create_job_row('active', 'evaluate', {})
    store.set_job_state('active', 'running')
    monkeypatch.setattr(dependencies, 'RAGChain', lambda: object())
    monkeypatch.setattr(dependencies.knowledge, 'bootstrap', lambda: pytest.fail('startup bootstrap'))
    dependencies.initialize_rag_system()
    assert next(row for row in store.list_job_rows() if row['id']=='active')['status'] == 'running'
```

Keep `dependencies.knowledge` available for this check until the import is removed; then patch `app.admin.knowledge.bootstrap` instead. The invariant is the absence of any call, not retention of an unused import. Run `venv/bin/python -m pytest testing/test_state_lifecycle.py -q`; observe the current global-recovery failure.

- [ ] Change `initialize_rag_system` to open/check PostgreSQL and construct RAGChain; remove startup calls to `knowledge.bootstrap()` and recovery mutation. Keep `recover_jobs` only while migrating its actual callers, then remove it from callers and definition together. Explicit migration owns provisioning/import.
- [ ] Read maintenance control in each write transaction with `FOR UPDATE`; the control command locks the same row. This serializes short business writes for this one-business deployment and avoids a shared-to-exclusive lock upgrade when recording the first-write marker. Allow intake only in intake/live and other business writes only in live. A missing control row is unavailable, never implicitly live. Worker/executor admission polls shared state; process-local Events remain wake-ups only.
- [ ] Intake can record a message during reconciliation while processing remains stopped. Job admission is denied outside live; active jobs are drained before the production source freeze. On shutdown, stop work safely before closing the pool. Never globally convert generating/sending states on startup.
- [ ] Record the first durable post-cutover write in `runtime_control.first_live_write_at` atomically with the write when `cutover_started_at` is set. Runtime gets only UPDATE on that column, not on mode or watermarks. The timestamp is set once; it covers intake and reconciliation as well as normal application activity. Rollback rehearsal before setting a cutover watermark must not mark ordinary synthetic fixture creation as a production cutover.
- [ ] Add mode transition races, query-timeout sanitization, no-credential readiness failure, and no-implicit-local-fallback checks. Run lifecycle plus earlier PostgreSQL behavior tests. Commit exact task files.

## Task 5: Snapshot, atomic import, and full-content verification

**Files:** Create `scripts/__init__.py`, `scripts/migrate_state.py`, and `testing/test_state_migration.py`; extend the CLI-generated schema only through a new CLI-generated migration if its committed form genuinely needs correction; update `.gitignore` only for new private runtime paths not already covered by `data/`.

**Interfaces:**
- `snapshot(source: Path, output: Path) -> dict` creates an owner-only SQLite backup and manifest.
- `inspect_source(snapshot_path: Path) -> dict` returns schema/column/key/count information with no row content printed.
- `content_manifest(connection, dialect: str) -> dict` returns table counts and canonical digests, using fixed table/column allowlists.
- `import_snapshot(snapshot_path: Path, admin_dsn: str, expected_project: str) -> dict` validates and imports atomically.
- `verify_snapshot(snapshot_path: Path, admin_dsn: str) -> dict` compares full contents and published selection.
- `set_runtime_mode(mode: str, admin_dsn: str) -> None` performs privileged, guarded mode changes; `rollback_check(admin_dsn: str) -> dict` returns an `allowed` boolean and a sanitized reason.
- A `source_snapshot` fixture provides a SQLite `Path` containing all eight original tables with synthetic rows, a valid published version, and conversation ID 41; `pg_workspace.admin_dsn` supplies the disposable local connection string. Test identity `local-rehearsal` is accepted only for the loopback disposable database, never a hosted endpoint.
- CLI: `snapshot --source PATH --output PATH`, `import --snapshot PATH --expected-project REF`, `verify --snapshot PATH`, `control closed|intake|live`, `rollback-check`.
- Every PostgreSQL CLI operation reads `DATABASE_MIGRATION_URL` locally. It never accepts a password as a shell argument and never starts the FastAPI lifespan.

- [ ] Add snapshot and canonical-digest checks:

```python
def test_backup_includes_committed_wal_rows(tmp_path):
    source = tmp_path/'source.sqlite3'
    with sqlite3.connect(source) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE sample (id INTEGER PRIMARY KEY,value TEXT)')
        db.execute("INSERT INTO sample VALUES (41,'retained')")
        db.commit()
        snapshot(source, tmp_path/'backup.sqlite3')
    with sqlite3.connect(tmp_path/'backup.sqlite3') as db:
        assert db.execute('SELECT id,value FROM sample').fetchone() == (41,'retained')

def test_equal_counts_do_not_hide_changed_content(source_snapshot,pg_workspace):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.conversations SET answer='different' WHERE id=41")
    with pytest.raises(ValueError,match='content'):
        verify_snapshot(source_snapshot,pg_workspace.admin_dsn)

def test_first_new_intake_blocks_stale_rollback(source_snapshot,pg_workspace):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.runtime_control SET mode='intake',cutover_started_at='2026-10-15T00:00:00+00:00' WHERE id=1")
    store.enqueue_inbox('asia-chatbot','new-after-cutover','123@lid','new')
    assert rollback_check(pg_workspace.admin_dsn)['allowed'] is False
```

Keep low-level backup independent of the production-table validation so this check can use a minimal table; `import_snapshot` applies the strict eight-table validation. Run `venv/bin/python -m pytest testing/test_state_migration.py -q`; observe missing tooling.

- [ ] Create the backup using SQLite's `Connection.backup()`, not copying `admin.sqlite3` bytes. Set directory mode 0700 and files 0600. Stream the snapshot checksum and generate a manifest with a format version, source checksum, observed columns, keys, counts, and digests. Do not include data rows, DSNs, salts, token hashes, or message text in reports.
- [ ] Canonicalize typed cells so NULL, empty string, integer, float, text, and binary remain distinguishable. Preserve JSON text exactly. Hash ordered rows by declared primary key, including the inbox composite key. Reject unsupported/missing columns, missing required keys, duplicate keys, invalid JSON source fields, invalid acknowledgement values, or nonfinite numeric values before importing. The known pre-progress jobs schema may receive the documented empty `{}` progress value; do not guess defaults for unknown schema versions.
- [ ] Verify the target identity by both DSN project-bearing host/user and the confirmed project-scoped MCP before a production import. Inspect schema version, grants, and emptiness. An administrative DSN without recognizable project identity requires an explicit verified identity mapping in the runbook before execution; do not guess from the database name `postgres`.
- [ ] Import all eight tables in one transaction with explicit ordered columns, preserving IDs. Reset the identity sequence to the maximum imported ID, handling an empty table correctly. Write one `state_imports` row with the source checksum and digest manifest in the same transaction. The runtime control/schema metadata are excluded from the eight-table comparison.
- [ ] If the same import checksum already exists, compare the retained import manifest and report already-imported without inserting again. A subsequent live-data difference is not overwritten; `verify` reports it separately. If a different import exists or destination business data is nonempty without the matching ledger, abort without deletion. Rehearsal uses a separate disposable database with the same schema, never a production-table truncate.
- [ ] Implement verification and control commands. All control changes are privileged and serialized on runtime control. Enabling intake requires a matching verified import manifest; enabling live additionally requires the reconciliation completion record from Task 6. `rollback-check` returns blocked once `first_live_write_at` is set. It does not perform an unsafe automatic reverse migration.
- [ ] Add import transaction rollback, repeat import, wrong project, unexpected table/column, content mismatch despite equal counts, empty source, retained JSON/nulls, expired sessions, ID gaps, and publication-marker mismatch checks. Run the migration tests against synthetic source data and real disposable PostgreSQL. Commit exact task files.

## Task 6: WAHA maintenance history reconciliation

**Files:** Create `scripts/reconcile_waha.py` and `testing/test_waha_reconciliation.py`; use the existing `waha.api`, `Message`, and store operations rather than creating a second HTTP client.

**Interfaces:**
- `scan_interval(start: int, end: int, request) -> list[dict]`: request is a callable with the existing `waha.api` calling convention; production uses that helper, tests supply paginated synthetic replies.
- `reconcile_messages(messages: list[dict], session: str, write: bool = False) -> dict`: defaults to a dry run, compares original IDs/content, and optionally inserts missing validated inbound messages. It never calls `process`, `send_reply`, or any send endpoint.
- CLI: `scan --start ISO --end ISO --output PATH` and `replay --report PATH --write`; raw scan data is stored only in an owner-only ignored directory, while printed summaries contain counts/digests only.
- A reconciliation completion receipt, stored in privileged import metadata, records snapshot checksum, session, exact interval watermarks, and scan digest. Task 5 uses it before enabling live execution.

- [ ] Add LID, duplicate-page, and missing-message checks:

```python
def test_replay_preserves_sent_and_only_adds_missing(pg_workspace):
    store.enqueue_inbox('asia-chatbot','old','123@lid','old body')
    store.update_inbox('asia-chatbot','old',{'status':'sent','reply_ids':'["reply-old"]'})
    messages=[{'id':'old','from':'123@lid','body':'old body','fromMe':False,'timestamp':10},
              {'id':'new','from':'123@lid','body':'new body','fromMe':False,'timestamp':11}]
    summary=reconcile_messages(messages,'asia-chatbot',write=True)
    assert summary['inserted'] == 1
    assert store.get_inbox('asia-chatbot','old')['status'] == 'sent'
    assert store.get_inbox('asia-chatbot','old')['reply_ids'] == '["reply-old"]'

def test_scan_uses_closed_window_and_deduplicates_pages():
    seen=[]
    row={'id':'window-1','from':'123@lid','body':'new chat','fromMe':False,'timestamp':100}
    def request(method,path,payload=None,**kwargs):
        seen.append(path)
        if path.endswith('/chats?limit=100&offset=0'):
            return [{'id':'123@lid'}]
        if '/chats?' in path:
            return []
        if 'offset=0&' in path:
            return [row]
        if 'offset=100&' in path:
            return [row]
        return []
    rows=scan_interval(100,101,request)
    assert [item['id'] for item in rows] == ['window-1']
    paths=[path for path in seen if '/messages?' in path]
    assert any('offset=200&' in path for path in paths)
    assert all('downloadMedia=false' in path and 'filter.timestamp.gte=99' in path
               and 'filter.timestamp.lte=102' in path for path in paths)
```

Run `venv/bin/python -m pytest testing/test_waha_reconciliation.py -q`; observe missing functions.

- [ ] Enumerate chats including those first observed during maintenance; fetch stored messages using documented `/api/{session}/chats/{chatId}/messages` with `downloadMedia=false`, time filters, explicit limits/offsets, and a fixed closed interval. Include overlap at both ends and deduplicate by full provider ID. Validate the installed GOWS response shape and pagination termination during preflight; a missing or truncated history capability blocks cutover.
- [ ] Apply existing Pydantic message validation, fromMe/private-chat/empty filtering, and preserve `@lid`. Sort missing messages by original provider timestamp plus ID before inserting. Preserve original receipt time. On duplicate ID with different content, report conflict and refuse completion; never update an existing sent/uncertain item to queued.
- [ ] Reconcile known outbound reply IDs' acknowledgement states through read-only provider history; use monotonic acknowledgement writes and retain unknown status when unavailable. Do not promise historic ACK events that the provider no longer exposes.
- [ ] Require intake mode for production replay and take the runtime-control lock while checking it. Store reconciliation evidence only after all eligible messages in the closed interval are accounted for. Dry-run outputs cannot authorize live mode. New intake remains enabled; processing remains disabled until the operator enables live.
- [ ] Add checks for inclusive watermark overlap, unordered/duplicate pages, short pages with further offsets, new chats, malformed payloads, conflicting duplicates, uncertain messages, source content redaction, and zero send calls. Run the reconciliation tests; expected pass with HTTP mocked and PostgreSQL real. Commit exact task files.

## Task 7: Integrate, rehearse, and prepare the live cutover

**Files:** Modify `README.md` and `.env.example`; create `docs/runbooks/supabase-state-cutover.md`; adapt `testing/test_public_landing.py` only if its fixture requires the changed startup contract.

**Interfaces:** Consumes all commands and domain operations from Tasks 1–6; produces an operator runbook, sanitized rehearsal report under `data/migrations/`, and a backend runnable locally against Supabase. It does not produce a Vercel deployment.

- [ ] Document environment values without secrets:

```dotenv
DATABASE_URL=postgresql://chatbot_app.PROJECT_REF:PASSWORD@POOLER_HOST:6543/postgres?sslmode=require
DATABASE_MIGRATION_URL=postgresql://postgres.PROJECT_REF:PASSWORD@SESSION_POOLER_HOST:5432/postgres?sslmode=require
```

These are shapes, not connection strings to copy blindly. Obtain actual hosts/usernames from the confirmed project's Connect panel. Keep application secrets backend-only. Provision the application password locally over TLS; never put a real password in migration SQL, shell arguments, MCP prompts, docs, or frontend variables. Do not change `.env` until a verified runtime connection is available.

- [ ] Retain a private runnable copy of existing application code/config and working dependencies before changing the running environment. Include relevant uncommitted files without resetting the checkout. Keep source artifact directories in place throughout this database phase.
- [ ] Adapt and run the existing behavior checks with disposable PostgreSQL:

```bash
venv/bin/python -m pytest testing/test_postgres_state.py testing/test_state_migration.py testing/test_waha_reconciliation.py testing/test_state_lifecycle.py testing/test_admin_workflow.py testing/test_dashboard_progress.py testing/test_waha_integration.py testing/test_public_landing.py -q
```

Expected: no external provider calls or WhatsApp sends; existing behaviors preserved. Add an end-to-end synthetic rehearsal that snapshots all eight tables, imports, verifies, starts the application in intake mode, reconciles synthetic interval events, and refuses stale rollback after the first new write. PostgreSQL-specific checks cannot be replaced by SQLite or skipped fixtures.
- [ ] Rehearse against a disposable database using a private consistent source backup. Compare complete contents. Validate restoration of that backup. Delete only rehearsal-owned objects after recording the result. Do not exercise a production customer conversation as a rehearsal.
- [ ] Run read-only production preflight after credentials are configured: confirm project, schema, permissions, application-role connection, selected Pinecone namespace, and WAHA history completeness. Report any missing fact and keep the original backend active. Do not begin maintenance merely because code tests pass.
- [ ] Execute the accepted spec's scheduled maintenance procedure only when all preflight checks pass: stop new source requests, drain active work, stop all source writers, record start watermark, snapshot, apply schema, import, verify, start the new backend closed, and validate readiness without committed business writes. Maintenance is a temporary lack of chatbot availability; the runbook must say so.
- [ ] Record the cutover point, enable intake, record the end watermark after intake is confirmed, scan/replay the interval, and compare all eligible message IDs before enabling live. Keep already-sent/uncertain rows unchanged. Recheck the interval if intake experienced another interruption. A failed reconciliation leaves intake/maintenance active, never silently enables replies.
- [ ] Check login/session, playground history, published selection, progress visibility, and inbox state after cutover. Do not send unsolicited test messages; an actual WhatsApp send requires the user's authorized test recipient/session. Query Supabase to verify written state and use its advisors to inspect the final schema. Preserve backups and redacted evidence.
- [ ] Before the first new write, rollback may restore the preserved application and SQLite, followed by maintenance-message reconciliation. After new writes, stop: retain maintenance and repair PostgreSQL unless a separately verified reverse transfer carries all changed state back. The runbook must not suggest changing a DSN alone restores current data.
- [ ] Commit only the runbook/docs and any exact integration fixes owned by this task. Report what is implemented, what was verified locally/remotely, whether live cutover occurred, and why any required step remains blocked. Do not claim full Vercel readiness.

## Dependency order and execution handoff

Execute Tasks 1 → 2 → 3 → 4 → 5 → 6 → 7. Interfaces and lifecycle choices are coupled; do not assign concurrent edits to `store.py`, routes, jobs, or WAHA. Task commits must include only their owned changes and must not sweep up the existing landing/dashboard work.

Recommended execution method: **Native**, implementing the tasks in order in this session, with one independent review after the complete change. It avoids repeated context loading for tightly coupled persistence callers. Subagent-driven execution remains available if the user prefers per-task independent reviews.

Review this written plan and select the execution method before implementation, as required by the chosen brainstorming/writing-plans workflow. After that selection, continue through all unblocked tasks without requesting another general approval. Missing production credentials or failed preservation preflight stop only the dependent live operations; they do not prevent completing local implementation and synthetic verification.
