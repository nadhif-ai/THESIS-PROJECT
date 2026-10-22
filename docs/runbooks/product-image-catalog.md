# Product image catalog operations

The original design is `docs/superpowers/specs/2026-10-22-context-aware-product-images-design.md`, superseded for request policy and delivery order by `docs/superpowers/specs/2026-10-22-request-only-product-images-spec.md`. Semantic intent and response consistency now follow `docs/superpowers/specs/2026-10-23-structured-product-image-intent-design.md`. Product facts and prices continue to use the active knowledge snapshot and existing Nemotron/Pinecone index.

## Provision and import

Apply `supabase/migrations/20261022144029_product_image_catalog.sql` with the project-scoped Supabase MCP migration tool. Also apply `supabase/migrations/20261022145051_catalog_preview_history.sql` for isolated preview repetition state. Keep both versions aligned with hosted migration history. This is an additive migration; it does not alter knowledge activation or existing conversations. Never run tests against hosted PostgreSQL.

From the repository root, with the restricted runtime database role and backend Storage credentials configured:

```sh
venv/bin/python dataset/image-product/verify_catalog.py
venv/bin/python -m app.admin.catalog_import --approved-by user-Q3-2026-10-22
```

The import checks explicit approval, selected-image paths, decoding and checksums; it uploads immutable public objects and verifies bytes before inserting records. Repeating it preserves existing IDs, including subsequent dashboard edits. It never imports drafts, references or prices, and does not enable automatic attachments. Bucket provisioning is explicit operator/upload work, not startup DDL.

`product-catalog` is public and image-only. `catalog-staging` is private and receives short-lived signed uploads; the backend decodes and verifies a staged image before copying approved bytes to the public bucket on Save. `knowledge-originals` remains private and unchanged. Public URLs can remain accessible after Disable; Disable prevents new chatbot use, not distribution of previously shared copies.

## Manage images

Open `/admin/catalog`. Filter by group, product, purpose or enabled status; edit an image or add an approved PNG/JPEG up to 10 MB. Save activates the record immediately after validation, with an expected revision to reject stale edits. Upload or validation failure preserves the old active record. Images preserve their full proportions.

Set precise depicted variants, separately from available source-only variants. Keep actual prices and authoritative specifications in Knowledge. Captions describe illustrations and must not add price claims. A comparison's covered products must match what it shows; Other Physical Printing Products still contains distinct products.

Export metadata from the catalog page or authenticated `GET /admin/api/catalog/export` for review and backup. PostgreSQL is the runtime authority after import; the repository manifest is the approved seed/provenance package. Do not replace dashboard records by rerunning a seed import with overwrite behavior.

The global Requested catalog images switch controls rollout and emergency rollback. Images attach only to visual requests, including contextual previews and explicit repeats. Product, price, material and textual comparison inquiries alone receive no attachment. A suitable reply contains one illustration first, then a separate price/detail text grounded in active knowledge. Several requested products use one suitable comparison or a clarification. Every selection reads current catalog state; Save/Disable needs no restart or Pinecone Sync. Playground and catalog question previews share selection logic but never send WhatsApp messages or consume a customer's delivery allowance.

## Validate and enable

Run the offline suite against disposable PostgreSQL and frontend lint/build. Verify an initial product, quantity follow-up, material/form comparison, explicit resend, topic switch, ambiguous sticker inquiry, reset and 24-hour inactivity. Verify actual images and suppression reasons in Playground.

Use a controlled test account (or the WAHA account's own identity) for live sends. Verify image-before-details provider IDs and acknowledgements before enabling customer rollout. Do not use a customer from stored conversation history as a test recipient. The feature switch defaults off for initial provisioning.

## Delivery recovery

Each inbox item pins the selected asset revision/object and stores `text`, `image`, and, if needed, `notice` delivery parts. Provider acceptance is distinct from delivered/read ACK. `reply_ids` remains the provider receipt correlation list.

- A successful image or text part is never replayed to recover another part. A new explicit customer request may reuse the same illustration; this is separate from recovering an old inbox item.
- A definitive image failure on a visual request gets a short failure notice after available detail text, checkpointed separately. This includes legacy knowledge-media fallback. Failed or uncertain images do not block detail text; failed or uncertain text is recorded independently.
- Timeouts, missing provider IDs and crashes during sending are uncertain outcomes. Expired sending leases become uncertain; queue redelivery does not resend them.
- Inspect WAHA/WhatsApp and provider receipts for an uncertain item. Do not flip it to queued as an automatic retry. A customer's new explicit resend is a new inbox action; retain the old uncertain record.
- Disable or a bot-replies fence skips unsent image parts. A provider request already submitted cannot be recalled.

For cleanup, retain public objects referenced by any active catalog record or pinned inbox selection. Remove only demonstrably unreferenced objects as explicit maintenance; never bulk-delete by an old filename prefix. Private expired staging uploads can be removed after their tickets expire. There is no automatic destructive cleanup job.

## Semantic intent rollout (2026-10-23)

The shared RAG pipeline interprets substantive turns using `PRODUCT_INTENT_MODEL` (default `openai/gpt-4.1`). The answering model remains independently configurable. Structured calls require native JSON schema through OpenRouter, require compatible provider parameters, have no automatic model retry, and validate canonical IDs with Pydantic. Do not change the Nemotron embedding or Pinecone index for catalog matching. Restart the backend after environment changes.

The LLM resolves action, product, requested view and attributes; a deterministic selector chooses at most one enabled catalog asset. Nonvisual requests attach nothing. Repeats are allowed; comparison assets require visual comparison intent. Product identity does not depend on whether its name appears in the retrieved top-k passages. Explicit exact-appearance requests require verified visual attributes; unsupported comparisons are not substituted with another material.

`visual_attributes` is optional metadata in the existing catalog JSONB. No schema migration is needed. Before deploying this resolver to an existing catalog, fill the four approved comparison records without overwriting dashboard changes:

```sh
venv/bin/python -m app.admin.catalog_import --backfill-visual-attributes --approved-by user-Q3-2026-10-22
```

This operation only fills records missing the field entirely, with the original approved checksum, product and role. Records with existing fields or replaced images are preserved for manual review in Catalog. Empty fields are conservative: exact visual matching is unavailable until an operator verifies the depicted attributes. Values describe illustration labels/appearance, not proof of real material, stock, dimensions, or price. The original selected image bytes and checksums are unchanged.

Application text owns attachment availability and illustration qualification. Generated product details are checked against the pinned product/view, verified coverage and retrieved facts. A failed check uses controlled prose without invented prices. Failure to parse intent does not fall back to regex. Playground exposes resolved product, asset/catalog revision, model, prompt hash, app version, latency and answer-check outcome. Conversation usage JSON also retains the image decision and stage usage for subsequent diagnosis. The answer output budget is 2,048 tokens; visual-detail outputs ending at the provider token limit use controlled complete prose instead of partial prices. Total reported token usage includes intent, answering and consistency checking; failed/unreported provider usage is unknown, not an estimate of zero billing.

For pending pre-upgrade jobs without an explicit pinned image decision, unsent legacy media is suppressed conservatively; available text is still sent. Existing image uncertainty remains visible even when the image is no longer eligible. New legacy knowledge-image requests carry their semantic decision in the checkpoint.

WAHA GOWS supports the existing `POST /api/sendImage` request with a public URL, MIME type and filename; no extra intent-specific WAHA setting is required. Keep the session WORKING, public Storage URLs reachable from the WAHA host, and the existing webhook/worker configuration. Production deployment and a controlled WhatsApp receipt test remain separate from local Playground evidence. Sources: [WAHA media delivery](https://waha.devlike.pro/docs/how-to/send-messages/) and [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).
