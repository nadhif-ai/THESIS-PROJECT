# Global knowledge verification, 18 October 2026

## Scope and implemented contract

See [approved design](../docs/single-knowledge-base.md). The dashboard has one
source list and saved chunking configuration. WhatsApp/Playground use synchronized
knowledge; new evaluation submission captures its current snapshot and models.
Immutable IDs remain in result provenance without a version selector.

## Executed checks

- `venv/bin/python -m pytest testing --ignore=testing/evals -q`: **164 passed**,
  two existing third-party deprecation warnings. Disposable PostgreSQL only.
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

Candidate `dpl_EUrUHdiiBsqYJm5SS982JPf513ok` is READY in `bom1`. Authenticated
catalog and private-original preview were checked through `vercel curl`, with
six sources and the original 95 active passages. Real queue execution and final
alias promotion remain pending; local execution is not cloud execution proof.

## Design gate

- Hard gate: current local light/dark captures show no document overflow; controls
  use accessible labels, and loading/empty/error states exist. Final click-through
  checks are recorded at release.
- Purpose: existing paper/ink tokens, proof-blue action and functional upload/refresh
  icons; no new decorative assets, typography system or palette.
- Liveliness: ENERGY 1 / RHYTHM 1 / MOTION 1, consistent with the existing admin
  direction. Source table and Sync action define the hierarchy.
- Craft: real observed counts and timestamps, no generated customer claims. Historic
  landing captures are explicitly labelled when their old UI appears.
