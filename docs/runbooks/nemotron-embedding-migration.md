# Nemotron embedding migration

## Scope and invariants

- Active model: `nvidia/nemotron-3-embed-1b:free` through the existing OpenRouter credentials; 2048 dimensions, L2 normalization, `query` / `passage` input types.
- Pinecone: `chatbot-nadhif`, cosine. Never query old E5 vectors with Nemotron embeddings.
- Eight original versions remain archived. Seven indexed versions are cloned with exactly the same chunks; the draft is rebuilt from its files and remains draft. Preparation creates 1,054 vectors across eight namespaces.
- Published E5 knowledge continues serving during preparation and evaluation. Only its migrated replacement is activated during maintenance.
- Each of the seven ready Nemotron versions receives one legacy10 evaluation: 70 primary cases and 350 final metric scores. Judge calls can exceed that number; failed attempts and bounded corrective retries are recorded separately. The answering model, judge, top-k, and prompt remain fixed. No new E5 evaluation is performed.
- Model failures have bounded retries. There is no automatic embedding/provider fallback.

## Runtime storage

PostgreSQL stores version manifests, chunk IDs, text, and metadata. New Nemotron vectors live in Pinecone; duplicating all 2048 floats per chunk in PostgreSQL caused slow snapshot writes. Historical E5 snapshots retain their vectors.

The active requirements no longer require PyTorch, Transformers, Sentence Transformers, or the Hugging Face embedding adapter. The existing development environment may still have these installed; LangChain optionally imports them when present. FastAPI import was also checked with these packages made unavailable. Historical reproduction uses the baseline dependency file and archived code/configuration in a separate environment.

## Preparation and evaluation

Run from the repository root with the existing private `.env`:

```sh
venv/bin/python -m scripts.migrate_embeddings prepare
venv/bin/python -m scripts.migrate_embeddings evaluate
```

These commands select the Nemotron profile only in their own process. They do not change the running bot's environment or published pointer.

Private checkpoints are under `data/migrations/nemotron-20261016/`, with restricted permissions. Preserve them: they contain source snapshots, the passage embedding cache, the source-to-target map, and evaluation job IDs. Do not commit or share this directory. Preparation resumes from its checkpoint; evaluation refuses to repeat an existing partial/failed paid attempt automatically. Use one coordinator per migration. The runner reloads job reservations between versions so a long evaluation cannot overwrite newer reservations with its stale checkpoint.

Scores and traces use the existing DeepEval metrics and LangSmith reporting. Inspect per-case errors and coverage before interpreting averages. A completed job alone does not imply good answers or complete metric measurements. Legacy10 is a small historical dataset; these results are not a controlled comparison with newly evaluated E5 runs or evidence of statistical superiority.

## Controlled activation

1. Verify all eight namespaces and inspect all seven evaluations. Check the replacement of the original published version with real business questions.
2. Drain active jobs and message generation/sending. Enter `intake` with the existing privileged maintenance helper; keep its recorded watermarks.
3. Stop the old backend gracefully. The intake interval requires a WAHA history scan because webhooks can arrive while the backend is stopped.
4. Run `venv/bin/python -m scripts.migrate_embeddings activate`. It requires intake mode, no active execution, complete evaluations, and the unchanged original published pointer. The status/pointer swap and marking original versions as read-only archives are one PostgreSQL transaction. New drafts can still be cloned from an archive.
5. Set only these `.env` keys, preserving all other configuration:

   ```dotenv
   EMBEDDING_MODEL=nvidia/nemotron-3-embed-1b:free
   EMBEDDING_DIMENSIONS=2048
   PINECONE_INDEX_NAME=chatbot-nadhif
   ```

6. Start one backend process in intake mode. Startup rejects an incompatible published model/index.
7. Use `scripts.reconcile_waha` to scan and reconcile the full recorded maintenance interval. Record the reconciliation receipt, then use the existing helper to enter live mode. Never bypass the receipt requirement.
8. Verify health, Playground retrieval, and a newly sent WhatsApp message with its observed delivery acknowledgement. Do not replay historical failed or uncertain deliveries.

The runtime database role cannot change maintenance mode. Privileged credentials remain local and must not be added to the browser or a runtime deployment.

## Failure handling

Before activation, a failed staging/evaluation request leaves E5 serving and the published pointer unchanged. Inspect the private checkpoint and logs; resume only the unfinished work. Do not silently substitute a paid model or reuse vectors from another embedding space.

If activation or restart fails, remain in intake and repair forward. A return to E5 requires its archived application/dependencies, matching environment/index, an explicit pointer transition, and the same reconciliation procedure. Setting only the old model name is insufficient in the new Nemotron runtime.

The free OpenRouter endpoint can become unavailable or rate limited. This migration does not guarantee a response-time target or make the application ready for Vercel deployment by itself.
