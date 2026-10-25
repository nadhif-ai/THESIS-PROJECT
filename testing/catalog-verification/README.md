# Product catalog implementation verification

Verified 22 October 2026 against the approved context-aware product image specification. Deployment was not requested or performed. The hosted catalog feature remains disabled until the new application release is deployed and the operator enables it.

## Evidence

- Full offline backend suite: **249 passed, 11 skipped**, 2 existing dependency deprecation warnings. Command: `LANGSMITH_TRACING=false venv/bin/python -m pytest -q`. Tests use disposable PostgreSQL on loopback port 54585; no test fixture connects to hosted PostgreSQL. Paid DeepEval cases were skipped.
- JavaScript regression checks: **24 passed**, using `node --test testing/test_*.mjs`.
- Frontend `npm run lint` and `npm run build`: passed, with existing warnings in unchanged UI/hooks and knowledge-page files. TypeScript runs as part of build. No new catalog warnings.
- Catalog integrity verifier: 27 selected PNGs, seven groups, unique checksums and complete file mappings passed; two superseded drafts excluded. User approval is recorded in manifest and exports.
- Project-scoped Supabase MCP verified project `ndgfipshsgqmqnsmjhzz`, inspected schema/buckets and applied migrations `20261022144029_product_image_catalog` and `20261022145051_catalog_preview_history`. Hosted/local migration history agrees.
- Registry and public Storage contain exactly 27 selected assets across seven groups. `storage.json` records an **anonymous HEAD 200** for every image, matching MIME type and expected size. The importer also decoded and byte-verified every published object before activating its registry record. No image was embedded or inserted into Pinecone.
- `product-catalog` is public. `catalog-staging` and existing `knowledge-originals` are private. Image references and drafts were not uploaded to the public bucket.
- Browser verification used the built frontend and actual admin API against a separate disposable loopback database. Its factual knowledge was copied read-only from the active published snapshot; retrieval used the unchanged published Pinecone namespace.
- Browser Save changed a caption immediately from revision 1 to 2. Replacing the same image used a real signed private-staging upload, server decode/checksum verification and successful Save to revision 3. The replacement preview used a blob URL and displayed unsaved-change feedback. No runtime restart was needed for either Save.
- Browser catalog preview returned `roll-up-banner-hero` for a price inquiry using actual active knowledge. Playground returned `standing-banner-form-comparison` for an X/Y-banner comparison, displayed the image and decision reason, and sent no WhatsApp message. Screenshots: `desktop.png`, `preview.png`, `playground-comparison.png`.
- Mobile widths 390px and 320px had `document.scrollWidth === innerWidth`; dark theme and reduced motion were verified. Dialog opened with a labelled accessible title and input focus, then closed with Escape. Screenshots: `mobile.png`, `mobile-dark-320.png`.
- Impeccable mechanical detector returned no findings for the changed catalog and App targets. Existing DESIGN.md was preserved; its local ignored sidecar was refreshed.

## Durable delivery smoke

`live-self-smoke.json` records a controlled real-provider smoke using the WAHA account's **own identity**, not a customer selected from history. RAG generation and durable inbox/part writes used a disposable loopback database; no smoke inbox or conversation was inserted into the hosted administration store.

The real shared pipeline retrieved from the published namespace, generated the text answer, selected the roll-up hero and submitted **text first, then one image**. Both parts returned provider IDs. A read-only WAHA self-chat history lookup matched those IDs and observed **ACK 1 for each**. ACK 1 establishes server acceptance, not delivered/read confirmation. IDs are hashed in the committed report to avoid exposing the account's phone identifier; raw IDs were inspected locally.

## Automated behavior coverage

- Revision conflicts, immediate activation/disable, authenticated catalog access, CSRF rejection, invalid image rejection and idempotent 27-asset import preserving dashboard edits.
- Clear product inquiry for all 21 distinct product heroes, five comparisons and the kiss-cut detail; ambiguous stickers, topic changes, no product evidence, source-only materials/formats/decimal sizes, shipping/software questions and deterministic image choice.
- Same-product quantity follow-up, explicit resend, return-to-product suppression, independent preview attempts, reset and 24-hour inactivity boundaries; factual history remains available when media is first enabled.
- Shared RAG selector and legacy URL exclusion when catalog is enabled; pinned choice includes reason and catalog revision. WhatsApp focus is committed with the generated choice under its inbox lease.
- Text-before-image, explicit image-failure notice, no text replay after image failure, unknown text outcome stopping the image, asset disable after text, uncertain image suppression and crash/expired-lease handling. Existing queue, bot-disable and ACK regressions also passed.

Standards and spec reviews ran independently against the captured pre-implementation HEAD. Reported focus atomicity, history preservation, shipping-intent, preview repetition and source-only variant gaps were fixed and re-reviewed. Neither final review reported a remaining material blocker.

Supabase security advisors reported existing `public.rls_auto_enable()` SECURITY DEFINER execute warnings, unrelated to this change. No new catalog table exposure was reported; catalog tables are private with forced RLS and restricted backend-role policies. No unrelated database function was changed.
