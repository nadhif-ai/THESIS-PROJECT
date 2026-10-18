# Global knowledge base implementation

Approved 2026-10-18 after Q1–Q13.

## Contract

One source list and chunking configuration. Upload, replace, edit, enable/disable,
and delete are staged until Sync knowledge succeeds. A sync locks source edits,
builds a separate Pinecone namespace, verifies it, then atomically changes the
active pointer. Failure preserves the previous active data. Internal snapshots
remain for provenance, never as a selectable alternative for new evaluations.

TXT and selectable-text PDF originals live in private Supabase Storage. Browser
uploads use signed upload URLs, avoiding the Vercel request body limit. Scans
requiring OCR are rejected with actionable feedback. File type, size, encoding,
extracted text, and duplicate content are validated server-side.

WhatsApp, Playground and new DeepEval runs use the current active snapshot.
Evaluation submission captures the snapshot, cases and model configuration;
subsequent syncs cannot change a running evaluation. Empty active knowledge is
valid: factual questions receive “Maaf Kak, informasi tersebut belum tersedia
saat ini.” New evaluations require searchable active knowledge. Greetings and
reset remain available.

Indexing and evaluation run in bounded, checkpointed steps with database leases,
idempotent vector IDs, bounded retries and visible retry controls. Vercel Queues
wake the workers; local execution uses the same persisted state machine. Queue
publication failures remain visible and retryable. External provider calls may
repeat if execution stops before checkpointing; exactly-once billing is not
claimed. Preview deployments must not consume production jobs.

Cleanup protects configured sources (including inactive ones), active knowledge,
and unfinished jobs. A grace period protects ordinary in-flight retrieval.
Deleted originals and obsolete vectors are removed when no longer referenced;
evaluation results and their retrieval contexts remain available.

## Delivery checklist

- [x] Add private administration tables and Storage configuration.
- [x] Implement durable file storage, source validation and atomic source edits.
- [x] Implement safe, checkpointed synchronization and cleanup.
- [x] Pin and checkpoint evaluation execution; preserve metrics and LangSmith.
- [x] Replace version UI with the global source list; update Playground/evaluation.
- [x] Test regression, concurrency, empty KB, retry and authenticated file access.
- [ ] Migrate current active sources; verify new Pinecone namespace and retrieval.
- [ ] Review production configuration and release evidence.

## Credentials

Backend requires SUPABASE_URL and SUPABASE_SECRET_KEY (or legacy service_role).
Never expose this key through VITE variables or browser responses. Private file
access uses authenticated admin endpoints returning short-lived signed URLs.

## Migration and operation

1. Apply the checked-in Supabase migration (timestamp aligned with MCP history).
2. Configure the server Storage secret in local and production environments.
3. Run `venv/bin/python scripts/import_global_knowledge.py` on the machine holding
   active originals. It verifies factual passages against the active snapshot;
   it does not substitute bundled files for missing originals.
4. Run with `--apply` to upload and verify private originals. This stages the
   global source list and leaves the active pointer alone.
5. Deploy the backend and frontend together; both queue subscribers are declared
   in `pyproject.toml`. In production, click Sync knowledge and follow checkpoints.
6. Verify retrieval, Playground and a small evaluation before extending the corpus.

Limits: original 10 MB, PDF 300 pages, extracted text 1 MB per original, 5 MB of
active extracted source data, 5,000 indexed passages, overlap at most half the
chunk size. PDF extraction preserves page metadata. Originals and passage previews
are separate; PDF scans require OCR outside this workflow.

Evaluations checkpoint answers, individual metrics, and conversational pairs.
Conversations seed the previously saved turns into DeepEval and add at most one
pair per step, up to four pairs. The simulation recipe is recorded separately;
single-question metrics, references and thresholds are unchanged. Dataset review
decisions are saved in PostgreSQL, keyed to reference-file hashes, so review does
not require writes to the deployed filesystem. Stale/held reference gates remain.

Resume rejects a live execution lease. After expiry it issues a new sequence/key
while preserving the checkpoint. Embedding/index drift rejects synchronization
before another upsert or activation. Restore the recorded configuration to resume,
or change sources/settings and start a new synchronization.

Cleanup is scheduled on Queues after 24 hours. Each invocation removes a bounded
amount of eligible data and schedules continuation. Configured inactive sources
and unfinished/resumable evaluations keep their originals/snapshots. Cleanup
tombstones an original under the source lock before external deletion, preventing
a concurrent registration from attaching an object being deleted. Failed deletion
is retried; metadata and evaluation evidence remain.
