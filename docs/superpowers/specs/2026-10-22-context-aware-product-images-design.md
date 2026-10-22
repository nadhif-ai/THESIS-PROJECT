# Context-aware product catalog images

Date: 2026-10-22, Asia/Jakarta.

Status: design approved by the user's final shared-understanding confirmation on 2026-10-22. All ten product decisions are settled. Implementation is complete and verified locally with hosted catalog Storage/registry provisioning and a controlled WAHA self-send. See `testing/catalog-verification/README.md` for evidence and rollout boundaries; the application has not been deployed by this task.

## Objective and confirmed decisions

Attach a relevant catalog illustration to text-based customer inquiries while keeping answers grounded in the existing published knowledge. Incoming customer-photo recognition is outside this release.

| Decision | Confirmed outcome |
| --- | --- |
| Search input | Customer text and conversation context only |
| Automatic attachment | First discussion of a clearly identified product, visually relevant comparison, or explicit request for an example |
| Initial approval | User approved all 27 selected assets; the two superseded drafts are excluded |
| Storage access | Public URLs in a dedicated approved-catalog bucket; private originals and references stay separate |
| Administration | Image management in the dashboard from the first release |
| Reply format | Text first, followed by at most one image with a short caption |
| Activation | Each successful Save becomes active immediately; no separate Publish stage |
| Repeat suppression | Same asset suppressed until reset or 24 hours of customer inactivity; an explicit request to resend can override known prior sends |
| Channels | WAHA delivery and shared-selector Playground preview; legacy Fonnte remains text-only |
| Definitive image failure | Notify only when the customer explicitly requested an image; automatic attachment failure adds no customer message |

Save is the administrator's confirmation of the edited asset and its customer use. File and metadata validation precede activation. A failed Save preserves the previous active record. Disabling an asset takes effect for subsequent selection and unsent image parts after the server confirms the change; an already submitted provider request cannot be recalled.

## Current architecture: verified source findings

| Surface | Current behavior and design consequence |
| --- | --- |
| `app/backend/models.py:12-21` | Runtime fixes `nvidia/nemotron-3-embed-1b:free`, 2,048 dimensions, L2 normalization. Preserve this identity. |
| `app/backend/vectorstore.py:11-31` | Checks knowledge embedding compatibility and Pinecone dimension/metric. Same dimensions alone are not proof of compatibility. |
| `app/backend/chain.py:488-527` | Retrieves from the active namespace and selects the first nonempty retrieved `media_url`. There is no product-aware, approval-aware, or repetition-aware selection gate. |
| `app/backend/history.py:7-32` | Bounded text history and short-question expansion exist, but there is no structured current-product focus. Old products can remain in retrieval context after a topic switch. |
| `app/admin/global_knowledge.py:94-125` | Chunk metadata lacks canonical product IDs. `[MEDIA: HTTP(S) URL]` becomes `media_url`; catalog files are not automatically indexed or served. |
| `app/integrations/waha.py:87-137` | Supports `/api/sendImage`, currently image before text, generic caption, one overall inbox status and a list of provider IDs. Changing ordering needs per-part checkpoints. |
| `app/admin/store.py:766-864` | Existing per-sender serialization, leases, uncertain-send handling and receipts must be preserved. Queue deduplication does not guarantee provider-send idempotency. |
| `app/admin/source_storage.py:9-60` | `knowledge-originals` is private, restricted to source-document types. It must not become the public catalog bucket. |
| `app/routes.py:249` | Legacy Fonnte sender accepts a media argument but currently sends text. It is outside the image-delivery release. |

The connected Supabase account did not expose the chatbot project. Hosted bucket configuration and current WAHA deployment health were not verified in this design review. Source inspection and provider documentation do not establish a successful live image send.

## Images, metadata and Pinecone are separate concerns

Use three existing responsibilities:

1. **Pinecone:** published knowledge passages for factual answers, including current prices and specifications.
2. **PostgreSQL administration state:** editable catalog metadata, active asset records, product focus and media delivery checkpoints.
3. **Supabase Storage:** publicly retrievable image bytes for approved catalog assets.

For 27 curated images, start with explicit product aliases, variant mappings and deterministic selection. No image embeddings, second vector database, extra LLM classification call, or additional service is required. Keep catalog descriptions out of the factual answer namespace: illustrative captions must not displace price/specification evidence.

If measured matching failures later justify semantic catalog retrieval, embed the textual image descriptions/aliases in a separate catalog namespace using a verified compatible text embedding contract. Return stable asset IDs and resolve them against the enabled registry. Pinecone stores vectors and metadata; it does not need the source image binary to return a matching asset reference.

### Nemotron 3.5 clarification

NVIDIA documents Nemotron 3.5 Embed as accepting image or text passages with text queries. Its BF16 model card explicitly reports sharing the Nemotron 3 BF16 text embedding space through a frozen language component. OpenRouter also lists `nvidia/nemotron-3.5-embed-1b:free` as multimodal. Therefore, it would be inaccurate to claim that every 3-to-3.5 change necessarily invalidates every old text vector.

Nevertheless, this repository's exact identity guard and text-only embedding adapter do not support a silent switch. Provider behavior, preprocessing, query/passage contracts and compatibility with the active snapshot would need explicit verification and an approved compatibility/migration procedure. Image passage ingestion is a separate feature. None of that is necessary to select these catalog images from customer text.

## Catalog administration and metadata

Import the 27 selected records from `dataset/image-product/manifest.json` idempotently by asset ID and checksum. Preserve provenance, source sections, AI-illustration status, depicted versus source-only variants, and manual-review notes. The user's approval is recorded in the manifest and regenerated exports. The 27 approved records have been imported into the hosted registry with verified public objects; runtime dashboard edits are independent of the seed.

After import, PostgreSQL is authoritative for runtime dashboard edits. The repository manifest remains the seed/provenance package and an export format, not a second live writer. Export current catalog metadata for review and backup; imports must not overwrite later dashboard edits silently.

The dashboard needs one focused catalog page:

- List/filter by the seven groups, product, role and enabled status; show actual image previews and save errors.
- Upload a new image, replace an existing file, edit mapping/caption/alt text, and enable or disable an asset.
- Distinguish available business variants from variants visibly depicted by this asset.
- Preview a customer question with the selected asset or a suppression reason, using the shared selector without sending WhatsApp messages.
- Save activates immediately after validation; show unsaved changes and clear activation success/failure. There is no draft/publish workflow.

Keep generation prompts, checksums, object keys and dimensions read-only. Do not add price editing here: prices remain in the knowledge workflow. Require existing admin authentication and write protections; the browser does not access the private `chatbot` schema directly.

Suggested record contract, finalized in implementation rather than a new generic CMS:

| Field | Purpose |
| --- | --- |
| `asset_id`, `revision`, `enabled`, approval audit | Stable identity, optimistic concurrency, eligibility and traceability |
| `category_id`, `product_type`, `covered_product_types` | Seven-group navigation and precise product/comparison coverage |
| `role` | Hero, comparison, or detail |
| `depicted_variants`, `source_only_variants` | Prevent attaching an illustration as proof of an unpictured variant |
| `aliases`, retrieval keywords/exclusions | Indonesian terms and common product names; bounded matching hints |
| `description`, `alt_text`, caption | Accurate visual description and short customer wording |
| `object_key`, MIME type, dimensions, checksum | Verified immutable object reference; never a customer-supplied fetch URL |
| AI/provenance flags, review notes | Preserve illustration limitations and source traceability |

Comparison assets cover several products; a slug such as `standing-banner-comparison` is an asset purpose, not a new sellable product. The catch-all Other group must still distinguish each physical product. ID card and kartu nama are also separate products for matching and repetition.

Use a dedicated public bucket, for example `product-catalog`, with authenticated administrative writes. Upload only selected catalog images, not the whole dataset directory. Version object keys with asset identity and content hash; do not overwrite cached image bytes in place. Decode and validate PNG/JPEG uploads server-side, record real MIME/dimensions/checksum, and confirm object availability before atomically saving the active reference. Keep old referenced objects for in-flight deliveries; clean up only unreferenced objects through explicit maintenance. A public URL can remain accessible after an asset is disabled; disable controls bot use, not revocation of previously shared copies.

Catalog Save does not require knowledge Sync or a Pinecone reindex. A small catalog revision counter supports cache invalidation across workers. Each selection resolves the current revision and enabled state; a process-local cache alone cannot make Save or Disable reliably effective.

## Shared selection and conversation policy

Implement one selector in `app/backend/`, called from the shared RAG result path after successful answer generation. It receives the current question, bounded conversation focus, retrieved active-knowledge evidence, enabled catalog records and prior media attempts. It returns either a structured asset reference or a reason for no attachment. Playground uses exactly this decision logic.

Selection order:

1. Skip greetings, thanks, reset acknowledgements, errors, unavailable knowledge and non-product questions.
2. Resolve explicit current-turn product names first. A clear topic change replaces previous focus. An implicit follow-up inherits only an unambiguous current product. Bare “stiker” may need clarification rather than a guess between meteran and A3/kiss cut.
3. Require agreement between the resolved inquiry and relevant product evidence from the active knowledge. Do not infer eligibility from an entire mixed-product chunk containing a keyword somewhere. Initially match aliases within relevant sections/passages; canonical product tags can be added during a later normal Sync if useful, without requiring a forced reindex for this release.
4. Apply the confirmed trigger policy. Initial “harga roll up berapa?” can get its hero. Same-product “kalau 5 pcs?” gets text only. A question comparing materials/forms can get a comparison image. Variant questions do not automatically repeat a generic hero.
5. Match role and actual depicted coverage. Prefer an appropriate comparison for comparison intent, an appropriate detail for explicit visual-detail requests, otherwise a hero. A source-only variant is not a pictured variant. If no asset depicts the requested distinction, answer from knowledge and omit the image rather than imply visual proof.
6. For multi-product questions with no suitable comparison, attach none unless the user clearly identifies one product as the visual target. Keep the one-image limit; do not choose an arbitrary first product.
7. Apply enabled/approval gates and durable repetition suppression. A stable tie-breaker handles equally suitable approved assets. Do not use an uncalibrated cosine threshold as the sole confidence gate.

Negative keywords are contextual hints, not blanket exclusions that accidentally reject valid cross-product comparisons. User text and model output may identify an approved asset, but must not supply an arbitrary delivery URL. For the new catalog flow, legacy `[MEDIA:]` URLs do not bypass these gates; old knowledge text remains usable, while catalog selection becomes the only automatic image source when the feature is enabled.

Track current focus, last inbound customer activity and a reset epoch using persisted conversation state. Scope WhatsApp media state to WAHA account/session plus normalized sender; preserve existing RAG history identifiers unless separately required. Track preview conversations separately so Playground never consumes a customer's send allowance.

Twenty-four hours means inactivity since the last customer message, not time since the image was sent. Reset or that inactivity boundary clears media suppression and stale product focus. Within the boundary, successful or uncertain attempts suppress automatic repeats of the same asset; saving a new metadata revision must not accidentally bypass suppression. A known successful send can be resent when explicitly requested. A new explicit resend after an uncertain attempt is a new customer action, not an automatic retry of the old job; preserve the old uncertain outcome for operator review.

## Delivery and fallback behavior

Extend the existing WhatsApp inbox checkpoint rather than create another delivery queue. Persist the selected asset identity/revision/object reference and selection reason once before sending. A retry must not choose a different asset after a dashboard edit.

Record text and image parts separately with status, provider ID and safe error information. Suggested statuses: pending, sending, sent, failed, skipped and uncertain. The existing overall status is a summary and must not be the sole recovery decision. Provider acceptance and delivery/read acknowledgement remain distinct.

1. Claim the existing lease and enforce the bot-enabled fence.
2. Persist text-part sending state, send text, and checkpoint its provider ID immediately.
3. If text outcome is unknown, stop; do not send the image or replay the text automatically. If text definitively fails, do not send an orphan image.
4. Recheck asset enabled state and bot policy before sending the pending image. Resolve its pinned object key to the controlled public URL.
5. Persist image-part sending state, send the one image with accurate MIME/filename and a short caption, and checkpoint its provider ID.
6. On a definitive image failure, retain the successful text state. Notify briefly only for an explicit image request. If that notice itself is sent, checkpoint it as a separate delivery part as well.
7. On timeout, lost response, missing provider identity, or a crash during a sending state, record uncertain outcome. Do not blindly resend any uncertain part. Preserve existing operator inspection and receipt reconciliation behavior.

A caption can be “Ilustrasi roll up banner.” Add a qualification when a specific depicted form could be mistaken for exact stock. Captions must not invent prices, dimensions, capacities or material performance. Delivery failures must not cause a second full answer to be sent.

Media state represents attempted/sent outcomes, not merely a selected asset or text stored in conversation history. A skipped or definitive failed attempt does not become a claimed successful delivery. Reset does not authorize automatic replay of an old uncertain inbox job.

## Implementation sequence

These agreed work packages have been implemented. Their verification evidence is recorded in `testing/catalog-verification/README.md`.

| Step | Work and likely seams | Completion evidence |
| --- | --- | --- |
| 1. Registry and storage | Ordered Supabase migration, `app/admin/store.py`, a dedicated catalog storage helper, idempotent seed/import and metadata export | 27 selected assets mapped; drafts excluded; failed replacement preserves old active asset; unrelated private bucket untouched |
| 2. Admin API and dashboard | Authenticated catalog routes, upload/metadata validation, focused React catalog page and API types | Upload/replace/edit/disable/preview work; Save activates without restart; stale concurrent Save rejected; browser has no storage/admin secrets |
| 3. Shared selector | New bounded catalog matching module, `RAGResponse` structured media reference, `app/backend/chain.py`, persisted focus/reset handling | Offline multi-turn matrix selects expected asset or none; no catalog text enters factual answer context |
| 4. Delivery checkpoints | Extend existing inbox persistence and `app/integrations/waha.py`; preserve queue/lease/ACK contracts | Text-first ordering; one image; no repeat text after image failure; expired sends remain uncertain; pinned choice survives catalog edits |
| 5. Playground and rollout | Decision preview with reasons, feature switch, operator recovery documentation | Test-account WAHA text/image provider IDs and receipts; no customer rollout until controlled end-to-end evidence |

Use required repository skills before implementation: Supabase plus Postgres best practices for migrations, FastAPI for routes, LangChain RAG for retrieval integration, shadcn/interface-design for the dashboard. Run Python from the root with Python 3.12 and frontend checks in `frontend/`. No startup schema creation, SQLite fallback, new microservice, paid evaluation, deployment or live customer test is implied by this design review.

## Verification matrix

| Scenario | Expected result |
| --- | --- |
| First clear price inquiry for each of the seven groups | Accurate text from active knowledge; correct approved hero where a single product is clear |
| “Stiker” without enough context | Clarify; no guessed attachment |
| Meteran → A3 kiss cut topic change | New product wins over history; correct asset only if clear |
| “Kalau 5 pcs?” on same product | Text only; no repeated hero |
| “Bedanya X, Y, roll up?” | One standing-banner comparison |
| Unsupported or unpictured specific variant | No misleading visual; answer/follow-up from active knowledge |
| ID card → kartu nama; tumbler → stempel | Distinct products even within the same group |
| Return to a previously pictured product inside current boundary | No automatic duplicate |
| Explicit “kirim contoh itu lagi” | One explicit resend, separately tracked |
| Reset or 24 hours of customer inactivity | New focus/suppression boundary; no replay of old inbox jobs |
| Save/disable concurrent with selection/send | Current enabled gate respected; persisted old choice never silently replaced |
| Upload fails or concurrent stale Save | Prior active catalog reference preserved |
| Text timeout/crash after provider acceptance | Uncertain text; no blind resend and no image |
| Text succeeds, image fails or times out | Text not repeated; failed versus uncertain image distinguished |
| Queue redelivery, expired lease, missing provider ID | No duplicate known or uncertain part |
| No knowledge, model error, greeting, non-product question | No image |
| Playground preview | Same selector result/reason; no WAHA send and no customer dedupe mutation |

Test database behavior only on disposable local PostgreSQL. Run focused backend checks, then the relevant offline suite and frontend lint/build. Validate dashboard keyboard/mobile behavior within the existing design system. Provider integration tests use mocks until an explicitly controlled live test. Reuse the four established answer-quality metrics if a later authorized paid regression run is needed: Faithfulness, Answer Relevancy, Contextual Recall and Contextual Precision; image selection has its own expected-asset/none cases.

## Operational boundary and illustration limits

- Project-scoped MCP verified hosted registry/Storage provisioning, all 27 anonymous public image URLs and aligned migrations. WAHA was WORKING; a controlled self-send returned text/image provider IDs and observed ACK 1. This is server acceptance, not delivered/read confirmation. Customer attachments remain disabled until the new application release is deployed and the operator enables them.
- All 27 selected images now have user approval, but are still illustrations. Y-frame construction, exact souvenir models, stock textures, A3 printable areas, NCR sheet/set interpretation and e-money issuer/balance details cannot be authenticated from them. Keep these limitations in metadata; current knowledge remains authoritative.
- Seed approval flags and exports now record user approval. Seed runtime flags intentionally remain disabled: effective catalog eligibility and the rollout switch live in PostgreSQL, rather than in the seed manifest.
- The user confirmed shared understanding on 2026-10-22, completing the interview required by the explicitly invoked grilling skill. No design decisions remain open; implementation verification is recorded separately from deployment and customer rollout.

## Primary documentation consulted

Current documentation was checked through Context7 and Exa during this review; no embedding-provider calls were needed.

- [Pinecone data modeling](https://docs.pinecone.io/guides/index-data/data-modeling): vector records, IDs and metadata.
- [Supabase bucket fundamentals](https://supabase.com/docs/guides/storage/buckets/fundamentals): public reads versus controlled mutations.
- [Supabase serving downloads](https://supabase.com/docs/guides/storage/serving/downloads): public and signed delivery options.
- [WAHA sending messages](https://waha.devlike.pro/docs/how-to/send-messages/): image URL/data payload and engine support.
- [NVIDIA Nemotron 3.5 model card](https://build.nvidia.com/nvidia/nemotron-3_5-embed-1b/modelcard): multimodal passage embedding.
- [NVIDIA Nemotron 3.5 BF16 card](https://huggingface.co/nvidia/Nemotron-3.5-Embed-1B-BF16): frozen language component and shared text space.
- [OpenRouter Nemotron 3.5 Embed](https://openrouter.ai/nvidia/nemotron-3.5-embed-1b:free): provider model listing.
- [OpenRouter embeddings API](https://openrouter.ai/docs/api_reference/embeddings): supported text and multimodal request contracts.
