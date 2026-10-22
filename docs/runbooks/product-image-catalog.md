# Product image catalog operations

The approved design is `docs/superpowers/specs/2026-10-22-context-aware-product-images-design.md`. Product facts and prices continue to use the active knowledge snapshot and existing Nemotron/Pinecone index.

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

The global Automatic catalog images switch controls rollout and emergency rollback. Every selection reads current catalog state; Save/Disable needs no restart or Pinecone Sync. Playground and catalog question previews share selection logic but never send WhatsApp messages or consume a customer's delivery allowance.

## Validate and enable

Run the offline suite against disposable PostgreSQL and frontend lint/build. Verify an initial product, quantity follow-up, material/form comparison, explicit resend, topic switch, ambiguous sticker inquiry, reset and 24-hour inactivity. Verify actual images and suppression reasons in Playground.

Use a controlled test account (or the WAHA account's own identity) for live sends. Verify text-before-image provider IDs and acknowledgements before enabling customer rollout. Do not use a customer from stored conversation history as a test recipient. The feature switch defaults off for initial provisioning.

## Delivery recovery

Each inbox item pins the selected asset revision/object and stores `text`, `image`, and, if needed, `notice` delivery parts. Provider acceptance is distinct from delivered/read ACK. `reply_ids` remains the provider receipt correlation list.

- A successful text part is never replayed to recover an image.
- A definitive automatic image failure adds no customer notice. An explicit image request gets a short failure notice, checkpointed separately.
- Timeouts, missing provider IDs and crashes during sending are uncertain outcomes. Expired sending leases become uncertain; queue redelivery does not resend them.
- Inspect WAHA/WhatsApp and provider receipts for an uncertain item. Do not flip it to queued as an automatic retry. A customer's new explicit resend is a new inbox action; retain the old uncertain record.
- Disable or a bot-replies fence skips unsent image parts. A provider request already submitted cannot be recalled.

For cleanup, retain public objects referenced by any active catalog record or pinned inbox selection. Remove only demonstrably unreferenced objects as explicit maintenance; never bulk-delete by an old filename prefix. Private expired staging uploads can be removed after their tickets expire. There is no automatic destructive cleanup job.
