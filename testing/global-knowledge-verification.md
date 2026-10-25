# Global knowledge verification, 18 October 2026

## Scope and implemented contract

See [approved design](../docs/single-knowledge-base.md). The dashboard has one
source list and saved chunking configuration. WhatsApp/Playground use synchronized
knowledge; new evaluation submission captures its current snapshot and models.
Immutable IDs remain in result provenance without a version selector.

## Executed checks

- `venv/bin/python -m pytest testing --ignore=testing/evals -q`: **166 passed**,
  two existing third-party deprecation warnings. Disposable PostgreSQL only.
  Repeated against isolated release commit `ac91bfa` with dummy provider credentials:
  **166 passed**, so concurrent prompt-editor work in the shared checkout was not
  included in this release's test claim.
- `node --test testing/test_admin_navigation.mjs`: **7 passed**.
- `npm run build`: TypeScript and Vite production build passed.
- Ruff undefined/unused checks on the new backend modules passed.
- `git diff --check` passed.
- Vercel dry manifest contains both subscribers and evaluation references, and
  excludes `.env`, data, venv, agent configuration and documentation directories.
- Private Supabase Storage: signed direct upload 200, byte verification matched,
  scoped download 200, temporary diagnostic object removed.
- Active-source preflight: six TXT originals reproduce all 95 stored factual
  passages. The original absent chunking metadata means legacy 1,500/200; the
  import preserves that configuration rather than silently changing preprocessing.
- Six originals uploaded and downloaded again to verify their SHA-256 values.
  Staging leaves the existing active pointer unchanged.

## Browser evidence

Ego Browser, isolated local database on port 8011; real private Storage and an
isolated Pinecone namespace, never customer knowledge for the UI mutations.

- Multiple TXT/PDF upload, original URL, extracted PDF text and page-aware passage
  preview succeeded. Sync completed and Playground retrieved both source formats.
- One sample answer used both files, recorded 6.583 seconds including external
  providers. This is an integration check, not a latency or answer-quality claim.
- TXT inline edit saved as a replacement original and left active knowledge alone.
- Desktop screenshot and light/dark mobile screenshots inspected.
- 390px and 320px viewport checks: document scroll width equals viewport width.
- Reduced-motion emulation used; the existing shell respects that preference.
- PDF replacement, keyboard switch, delete/cancel, and source deletion succeeded.
  Modal focus returned to Delete after cancellation. Empty synchronization produced
  zero searchable passages; Playground returned the exact agreed fallback and the
  new-evaluation button was disabled.
- Native PDF preview rendered its page and toolbar; the signed response was
  `application/pdf`, HTTP 200. Saving chunk size 900 / overlap 100 showed the
  staged-change confirmation without changing active knowledge.
- Measured light body text contrast: 5.74:1. Dark headings, body copy and primary
  controls measured 7.42:1 or higher. Keyboard labels and modal focus were checked.

Screenshots are local diagnostic artifacts under
`data/diagnostics/global-knowledge-qa/`, intentionally excluded from deployment/git.

## Test isolation incident and recovery

A pre-existing startup test lacked a database fixture. After initialization was
changed to inspect empty knowledge first, that test opened the configured `.env`
pool; the following test reused it and briefly selected a synthetic empty snapshot
in production. The original `nemotron-08921960cce9` selection (95 passages) was
restored atomically and the synthetic snapshot removed. The inbox audit found
zero recorded WhatsApp changes in the surrounding 20-minute window. No vectors,
original files, saved evaluations or customer conversation records were deleted.

The test now uses its disposable fixture. An autouse boundary clears inherited
pools, removes provider credentials and rejects non-loopback PostgreSQL connections
through both the application pool and direct psycopg calls. Pool connections must
also target a `chatbot_test_` database. Dedicated rejection tests pass. Explicit
paid evaluation tests are the only opt-in exception. The complete suite was rerun
successfully after this correction.

## Production release

Candidate `dpl_SrpgR3bki95iQPcPSA2cTRXj7Nje` (commit `649b903`) is READY in
`bom1` and was promoted to the public domain. Authenticated catalog and private
preview were checked through `vercel curl`; public routes were then checked on
`https://chatbotta-nadhif.vercel.app`.

- Public sync job `25f39a6805154e86a7507bb93ce1c758` completed through the private
  Vercel subscriber in `bom1`, from prepare through embedding, ID verification,
  query verification and activation. No local administration executor was used.
- Active namespace is `kb-25f39a6805154e86a7507bb93ce1c758`, index
  `chatbot-nadhif`, Nemotron/OpenRouter 2,048 dimensions, legacy 1,500/200 split.
  Six sources and 95 passages; symmetric `EXCEPT ALL` comparison found **zero
  changed passage texts**. Applied revision equals source revision 6.
- Public Playground answered the address question, HTTP 200, 7.75 seconds
  including external providers. This is not a sub-second answer claim.
- One legacy evaluation, `bbad84a5ecb345df91d354f6942d2e0e`, completed all five
  metrics and five checkpointed feedback writes through Vercel Queues, with no
  reporting error. Reading each feedback back from LangSmith confirmed persistence.
  Snapshot/model/reference provenance is saved in the result.
- Sample scores: faithfulness 1.0, answer relevancy 0.5, contextual precision 0.7,
  contextual recall 1.0, business correctness 0.9. **One case is an integration
  check, not a thesis benchmark or evidence of overall answer quality.** Answer
  relevancy is below the unchanged 0.7 threshold and requires content/prompt work.
  [LangSmith experiment](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/d3611ed3-0559-49ac-93a8-73be67a60922).
- User-triggered WhatsApp test: webhook received at 15:07:37 UTC, Vercel queue
  claimed/generated/sent the reply, delivery ACK **2** at 15:07:52 UTC. LangSmith
  trace `01a14f8d-e526-7f71-ae04-2acbf12c6268` records the new active namespace
  and no error. Local customer backend remained stopped.
- Browser public Knowledge shows Up to date, six sources and 95/95 verified.
  Source preview pagination advanced from page 1 to page 2 of 3. Evaluation
  history displays the new completed run without a knowledge version selector.
  Inspect results rendered the saved scores; authenticated JSON export returned
  HTTP 200 with the matching run ID, one case and all five metrics.
- Isolated QA server stopped; two QA namespaces, four QA originals and the QA
  database removed after checking zero production references. An absent namespace
  returns Pinecone 404; cleanup now treats only **Namespace not found** as an
  already-completed deletion, while propagating unrelated 404 failures.

Production cleanup is scheduled after 24 hours; its grace-period deletion has not
been claimed as already observed. Current and pinned snapshots remain protected.

`SUPABASE_SECRET_KEY` is configured as a sensitive Production environment value;
`SUPABASE_URL` is backend configuration. The legacy `service_role` credential
is accepted, and only scoped file URLs reach the browser. Rotate the credential
shared in chat through Supabase and replace its backend environment value.

## Design gate

- PASS — Hard gate: light/dark captures show no document overflow; controls
  use accessible labels, and loading/empty/error states exist. Source controls,
  PDF rendering, settings save, pagination and modal focus were exercised.
- PASS — Purpose: existing paper/ink tokens, proof-blue action and functional upload/refresh
  icons; no new decorative assets, typography system or palette.
- PASS — Liveliness: ENERGY 1 / RHYTHM 1 / MOTION 1, consistent with the existing admin
  direction. Source table and Sync action define the hierarchy.
- PASS — Craft: real observed counts and timestamps, no generated customer claims. Historic
  landing captures are explicitly labelled when their old UI appears.
