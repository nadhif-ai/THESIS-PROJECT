# Request-only product images — local verification

Verified 22 October 2026 against the approved request-only amendment and GitHub issue #12. This report covers local implementation, not a production deployment or fresh WhatsApp delivery confirmation.

## Result

The shared conversation pipeline selects at most one illustration only for a visual request, resolves the attachment before answer generation, and supplies a trusted availability state to the answer prompt. Requested replies present the image first, followed by separate knowledge-grounded price/details text. Customer requests can repeat an illustration or change product; uncertain old provider sends remain protected from replay.

No embedding, Pinecone, Storage policy, schema, image asset, or catalog Save behavior changed. Existing unrelated admin-session changes and local MCP configuration are excluded from the implementation commit.

## Requirement evidence

| Requirement | Evidence |
| --- | --- |
| Ordinary product, price, quantity, materials and text comparisons have no attachment | `test_price_and_quantity_questions_do_not_attach_images`; actual browser initial banner inquiry had zero product images |
| Indonesian suffixes, preview, contextual views, banner x/y aliases | `test_request_only_screenshot_conversation_and_repeated_visual_requests`; canonical alias changes; actual browser three-turn screenshot reproduction selected X-banner |
| Negation, artwork requirements, photo-printing terminology and shipping remain nonvisual | `test_negated_and_price_only_view_wording_never_requests_media`, `test_photo_printing_and_examples_of_specifications_are_not_visual_requests`, `test_artwork_requirements_and_negation_with_product_do_not_attach`, existing shipping regressions |
| Different products and explicit repeats are allowed | `test_contextual_requests_and_successive_products_can_repeat`; browser repeat produced a second requested X-banner illustration |
| One suitable comparison or no misleading substitute | Real 27-asset seed test covers 21 product heroes and five comparisons; ambiguous-product, source-only variant, numeric-size and no-evidence regressions remain passing |
| Answer knows selected illustration before generation; prices remain factual | Authenticated Playground coordination test checks selected-product status, published retrieval context, and absence of catalog-description price contamination in model input |
| Price/details even for image-only requests | Same authenticated test supplies separate factual prices/options, checks output and prompt instructions; shared visual-query enrichment requests prices/materials/sizes in the existing retrieval call |
| No invented exact price or preview link | Grounding and attachment instructions require factual options/clarification, prohibit fabricated URLs and selected-illustration denial; offline tests verify prompt contracts, not paid-model adherence |
| Failed generation does not expose a selected image or advance focus | `test_generation_failure_suppresses_selected_image_and_focus` |
| Image before detail text in both channels | Actual Playground DOM order check; catalog question preview order; WAHA transport regression assertions |
| Image failure/uncertainty does not block detail text | Catalog and legacy WAHA rejection/timeout regressions; explicit definitive failures include an independent notice |
| Image accepted then text fails/unknown, without duplicate image | `test_successful_image_is_not_replayed_after_text_timeout`, `test_text_failure_summary_remains_visible_after_successful_image` |
| Conservative recovery and visibility | Existing queue, lease, receipt and checkpoint regressions; independently persisted text/image/notice outcomes and combined inbox error summary |
| Disable fence, focus persistence, reset/inactivity and preview isolation | Existing catalog disable, atomic inbox focus/selection, 24-hour/reset and preview/customer isolation regressions |
| Legacy fallback cannot bypass request-only policy | `test_legacy_media_fallback_is_request_only_in_shared_rag`; old automatic pinned selection is suppressed in the delivery regression |

## Checks

- Full offline backend suite: `LANGSMITH_TRACING=false venv/bin/python -m pytest -q` **262 passed, 11 skipped**, 2 dependency deprecation warnings. Paid evaluations were skipped as intended.
- JavaScript regression suite: `node --test testing/test_*.mjs`: 24 passed.
- Frontend: `npm run lint && npm run build`: passed, including TypeScript. Ten existing lint warnings remain in unrelated components/hooks; no lint errors.
- `git diff --check`: passed.
- Two independent review axes: Standards and Spec. All reported findings were fixed and rechecked; neither axis reported remaining material findings.

## Browser verification

A disposable loopback PostgreSQL database on port 54585, local approved-image files, and deterministic retrieval/model fakes were used. No paid provider, hosted database, vector service, or WhatsApp send was used. Factual UI fixture text explains that price depends on materials/size; synthetic numeric tariffs in the authenticated API test test grounding plumbing, not current business prices.

Observed:

1. `Hi kak mau print banner dong`: no image.
2. `Mau liat yg banner x tegak`: X-banner image, then detail text; DOM order confirmed.
3. `Iyaa kak X-banner, kirimin preview gambarnya dulu dong`: another X-banner image, permitted despite prior appearance.
4. Images decoded successfully, retained alt text and full intrinsic proportions. The conversation viewport scrolls normally; screenshots may show a partially scrolled illustration.
5. At 390 px: document scrollWidth = innerWidth = 390; images fit the message area. At 320 px: document scrollWidth = innerWidth = 320.
6. Reduced-motion preference was enabled during the mobile check. Existing customer-question label and send accessible name remain available.

Screenshots: [desktop](playground-desktop.png), [mobile](playground-mobile.png). These are local fixture screenshots, not production evidence. Owned browser space/server and disposable UI databases were cleaned up afterward.

## Release boundary

Production deployment and live customer rollout remain outside this task. After a separately authorized deployment, verify the deployed commit and worker path, reachable public catalog URL, image-first provider identities, and actual receipt ACKs using a controlled test account. An enabled catalog or WORKING WAHA session alone is insufficient evidence of customer delivery. The existing `/api/sendImage` integration is used; this change adds no separate WAHA image-enable setting.
