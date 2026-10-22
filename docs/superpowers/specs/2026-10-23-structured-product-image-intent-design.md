# Structured intent for requested product images

Date: 23 October 2026, Asia/Jakarta.
Status: conversational design approved; written specification awaiting user review.

## Purpose and approved understanding

Customers should be able to request product illustrations in natural Indonesian, switch products, and request the same illustration again. The chatbot must choose the intended product, show at most one relevant image, then provide separate price/product details from the published knowledge version. Playground and WhatsApp share the same decision pipeline.

The user approved replacing regex-led intent recognition with LLM structured intent followed by deterministic asset selection. Metadata identifies valid products/assets and visual coverage; it does not interpret the customer's language. A representative hero may illustrate an X-banner requested at 60 × 160 cm without claiming the illustration verifies that exact size. If intent extraction fails or is ambiguous, omit the image, answer only the understood part, and ask one short clarification when useful.

This supersedes the intent-recognition and strict depicted-dimension rules in the 22 October request-only amendment. Request-only delivery, one image, image-before-details ordering, immediate dashboard Save, approved assets, and conservative uncertain-send handling continue.

## Evidence and limitations

Read-only reproduction against the current local selector and repository manifest found:

- “Hi admin kirimin foto preview plakat akrilik dong” returns `variant_not_depicted`. Tokenizing prose variant metadata incorrectly treats `akrilik` as an extra visual constraint instead of product identity.
- “Kirimin foto X-Banner tersedia ukuran 60 × 160 cm dengan rangka berbentuk X” selects the standing-banner comparison despite asking for one product. Dimension filtering removes the hero while allowing comparison.
- “Mau liat foto banner-x tegak dong” selects the correct X-banner hero locally, unlike the supplied screenshot. The live runtime version, catalog revision, and recorded decision must be checked before attributing that discrepancy to a particular cause.
- The screenshot contains unavailable-preview denials alongside actual attachments. Current code passes attachment status into the answer prompt, but prompt instructions alone are not an enforced output contract.

Previous offline mock-provider tests verified pipeline behavior; they did not establish actual model intent accuracy. No new production audit or live-model evaluation was performed during this design phase.

## Chosen approach and alternatives

Use a bounded LLM extraction step plus deterministic selection. Compared with more regex exceptions, this handles meaning and conversation context without making catalog validity depend on free-form generation. Compared with multimodal retrieval, it fits the current small, text-requested catalog and does not require changing the embedding/index or uploading image bytes to Pinecone.

No autonomous agent loop is needed. Use a schema-validated model call through the existing LangChain/OpenRouter integration. Confirm structured-output support for the configured model/provider before enabling this flow. Schema validity does not establish semantic correctness; evaluation and catalog constraints are still required.

## Shared flow

1. Existing reset/greeting/menu shortcuts retain their current behavior.
2. For substantive customer turns, extract product/visual intent using the current message, bounded conversation history, trusted product vocabulary, and last validated product focus. Do not use a regex gate to decide which substantive turns deserve semantic interpretation.
3. Validate the result against the product vocabulary and allowed enum values. Resolve ambiguity explicitly; do not accept invented product IDs, URLs, or assets.
4. Use resolved product intent to query the existing published factual knowledge and to select an illustration from the approved catalog. These operations share product identity but have separate sources of truth.
5. Build one response plan containing attachment availability, selected asset if any, product identity, illustration qualification, and factual answer context.
6. Generate relevant price/details from factual context, validate consistency with the response plan, and persist the coordinated result.
7. Playground renders the plan. WAHA sends image first, followed by text, using existing independent delivery checkpoints.

## Intent contract

The extraction result contains:

- Visual action: `none`, `show`, `compare`, or `repeat`.
- Requested canonical product IDs, including an empty list for unresolved identity.
- Requested view: representative hero, comparison, or finishing detail.
- Explicit customer attributes such as dimensions, material, finish, or named type, with their supporting phrase from the current message or relevant prior turn.
- Whether an exact visual property is requested, as distinct from specifying the intended order's size/material.
- Resolution status: resolved, ambiguous, or unsupported; a short clarification target when needed.
- Whether the current message explicitly changes product, so a previous focus cannot override it.

No prices, asset IDs, object keys, or URLs are generated by this step. The backend validates all product IDs and enum values. A model confidence number is not sufficient authorization to attach media.

Examples:

- “preview plakat akrilik” → show / plakat-akrilik / hero.
- “banner-x tegak” in a visual request → show / x-banner / hero.
- “X-banner 60 × 160” → x-banner with an order-size attribute; this alone does not request comparison or certify depicted dimensions.
- “lihat perbandingan X dan Y banner” → compare / x-banner + y-banner.
- “kirim itu lagi” → repeat only if prior validated context identifies the illustration/product unambiguously.
- “berapa resolusi foto untuk cetak banner?” → no visual action.
- “fotonya jangan dikirim” → no visual action.

## Product context

Explicit current-turn identity takes precedence over prior product focus. An implicit request may inherit an unambiguous prior product. Ambiguous, unsupported, or failed extraction must not overwrite validated focus with a guessed identity.

A normal factual discussion can establish focus without attaching an image. Reset and the existing 24-hour inactivity boundary clear catalog context. An explicit repeat is a new customer request and is allowed; it does not authorize replay of an old uncertain delivery job.

## Deterministic selection and catalog semantics

The selector accepts validated intent, not the raw message for independent keyword interpretation. It must:

- Consider only currently enabled, approved catalog images.
- Match canonical product identity before ranking candidates.
- Choose a single-product hero for a representative single-product request.
- Permit comparison assets only for an explicit comparison request; never use comparison as an incidental fallback for a single-product size request.
- Use finishing-detail assets when that view is requested and supported.
- For multiple products without a suitable single comparison, ask which to show first.
- Return selected, unavailable, or clarification-required, with a stable decision reason.

Separate canonical product identity, available order specifications, and visually verified attributes. Do not convert arbitrary words in free-text variant descriptions into mandatory constraints. Existing metadata remains usable for labels/provenance, but decision-critical visual attributes need normalized, explicitly validated fields. Any necessary schema/API migration is limited to these fields, preserves existing data and dashboard editing, and is planned before implementation; no startup schema creation.

Representative fallback is allowed only within the correct product and compatible visual form. An unverified size may receive a hero with “Ilustrasi bentuk; ukuran mengikuti spesifikasi pesanan.” If the customer explicitly wants to inspect a particular finish, exact shape/type, or material difference that no image shows, state that limitation and clarify; a generic hero must not imply visual proof. Source-only specifications remain factual knowledge, not image evidence.

## Factual retrieval and response consistency

PostgreSQL catalog records establish illustration availability. Pinecone retrieval against the published knowledge version establishes prices and authoritative specifications. An appropriate approved illustration does not require its product name to appear in the particular top-k factual passages returned. If factual detail is unavailable, the correct illustration may still be shown with an honest statement that price/details require confirmation.

Resolved product identity informs the factual query so previous-product history does not contaminate the next product's answer. Keep the current embedding identity, dimensionality, Pinecone index, publication workflow, and knowledge provenance.

The application owns statements about attachment availability and illustration qualification. The model supplies grounded product/price details, not independent photo-link availability claims. The response plan is the single source of truth for both media and text.

Validate the candidate answer before delivery: it must not deny a selected illustration, invent a preview URL, assert delivery has already occurred, or present an unavailable exact variant as depicted. On a detected contradiction, allow at most one bounded repair using the same pinned plan and factual evidence. If consistency cannot be established, omit the conflicting prose and use an application-controlled explanation or clarification without invented prices. This is a bounded safeguard, not a claim of perfect semantic detection.

Prices are never inferred from image pixels, captions, or illustrative metadata. Provide applicable factual options; ask for missing order specifications rather than inventing an exact quote.

## Failure and delivery behavior

On extraction timeout, provider error, invalid structured output, or unresolved ambiguity, no image is selected and regex must not take over silently. Answer only independently supported parts and ask one short clarification if needed. Do not claim the catalog lacks an image merely because intent extraction failed.

Preserve the existing inbox lease and atomic persistence of generated answer, selected asset revision/object, and focus. Recovery reuses the pinned response plan; it does not rerun selection and substitute a different asset after delivery begins. Recheck enable/disable fences before an unsent image is submitted.

Keep image, text, and notice checkpoints independent. Image failure or uncertainty does not prevent the available text from being attempted. Definitive explicit-image failures receive a brief notice. Uncertain submissions are inspected rather than automatically replayed. Preserve provider identities, ACK correlation, and the distinction between acceptance and delivered/read receipts.

Playground uses the same resolver, selector, response plan, and presentation order. Preview state stays isolated from customer delivery state. Expose intent outcome, canonical product, asset/revision, decision reason, application version, and extraction latency for diagnosis; do not log credentials or hidden reasoning.

## Verification and release gates

Prefer the existing shared conversation result/authenticated Playground seam, plus WAHA transport tests for send order and recovery. Do not add test-only public endpoints.

Offline tests cover all supplied screenshot turns, product A → B → A, immediate repeats, slang/typos, implicit references, negation, artwork questions, failed extraction, invalid IDs, ambiguous products, unavailable assets, dimensions, exact visual constraints, comparison intent, generation inconsistency, disable fences, and uncertain-part replay protection. The screenshot cases must select plakat hero, banner hero, X-banner hero, and X-banner hero respectively when representative illustrations are requested and enabled.

Build a reviewed, versioned set of realistic Indonesian conversation cases with expected intent, acceptable asset IDs or no-image outcomes, and factual-answer constraints. Evaluate actual configured-model outputs rather than only canned mocks. Record model/provider identity, prompt version, catalog revision, application commit, request count, accuracy by case class, unsolicited-image errors, wrong-product errors, answer/attachment contradictions, fallback rate, and latency distribution. Report costs and measured outcomes, not assumed improvement. Live paid evaluations require explicit execution authorization under the repository rules.

Release gates: all deterministic regressions pass; all four reported screenshot scenarios pass with the real model; reviewed critical negation, wrong-product, and ambiguous-request cases produce no incorrect attachment; all observed attachment contradictions are resolved before rollout. Measure broader accuracy and latency on the reviewed dataset and present them for release assessment rather than inventing an unmeasured target.

Run focused tests, full offline backend suite, JavaScript checks, frontend lint/typecheck/build, and desktop/mobile Playground verification. Preserve unrelated worktree changes. Production deployment and controlled-account WhatsApp verification require separate authorization and fresh deployed-runtime evidence.

## Scope and trade-offs

Included: semantic intent extraction, canonical context handling, explicit visual coverage, deterministic selection, consistent response composition, diagnostic evidence, and meaningful regression/evaluation coverage.

Excluded: customer-uploaded photo recognition, new generated assets, multiple images per reply, multimodal embedding migration, new vector stores, autonomous agents, broad dashboard redesign, Fonnte media support, and automatic production deployment.

One bounded extraction call per substantive turn adds latency and provider cost. Avoid duplicate extraction per channel and unbounded repair loops; measure the impact. Caching across conversations is not part of this design because context affects intent.

## Documentation basis

- [LangChain model structured output](https://docs.langchain.com/oss/python/langchain/models): structured output without an agent, Pydantic validation, provider-dependent methods, and parsing-error visibility.
- [LangChain structured output](https://docs.langchain.com/oss/python/langchain/structured-output): constrained response formats and provider capabilities.
- [Pinecone metadata filtering](https://docs.pinecone.io/guides/search/filter-by-metadata): metadata constraints if semantic catalog search is later justified; it is not required for this release.

These primary sources were located through Exa and checked with Context7 during the preceding design discussion. The chosen architecture is a project-specific recommendation, not a claim that those documents prescribe this exact flow.
