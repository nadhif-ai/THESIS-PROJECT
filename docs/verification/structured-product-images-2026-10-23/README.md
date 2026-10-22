# Structured product-image verification

Verified on 23 October 2026 (Asia/Jakarta), against baseline `509f94e` plus this implementation. The approved design is [structured product-image intent](../../superpowers/specs/2026-10-23-structured-product-image-intent-design.md).

## Result and scope

All **54 browser regression turns passed** their expected attachment assertions: 38 independent Indonesian requests and 16 connected conversation turns. They exercised all **27 approved assets across seven product groups**. Selected images loaded successfully in the actual authenticated Playground, operated with ego-browser. The pipeline used real OpenRouter models and the active Pinecone knowledge namespace, with an isolated loopback PostgreSQL catalog/history and existing public Storage images. No customer conversations or hosted database records were modified by these tests.

The four reported screenshot cases now select the plakat hero, banner hero, X-banner hero and X-banner hero respectively. Representative X-banner dimensions do not force a comparison image. No wrong-product attachment or unsolicited attachment was observed in the retained regression run. Answers were inspected for image-availability contradictions; the consistency guard used one controlled fallback for an unavailable exact plakat appearance.

The application now interprets intent with a schema-validated LLM call and chooses images deterministically. It does not recover failed intent extraction with regex. Images precede separate factual detail text; contextual requests, product switches and explicit repeats are allowed. Prices still come from published knowledge, not catalog illustrations.

## Reproducible evidence

- [Independent request dataset](../../../testing/datasets/product-image-intents.json): 38 cases covering every asset, slang, negation, artwork questions, ambiguity, dimensions and exact visual constraints.
- [Conversation dataset](../../../testing/datasets/product-image-conversations.json): 16 turns covering factual focus, product switches, repeats, comparison repeats, clarification and reset.
- [Retained results](playground-results.json): questions, expected/actual assets, answers, decision diagnostics, source filenames, model usage and latency. Source hashes identify the tested implementation; runtime notes distinguish the final transport/checkpoint refinements from the earlier independent batch.
- [Desktop screenshot](playground-desktop.png): complete X-banner illustration followed by price details.
- [Mobile screenshot](playground-mobile.png): 390 × 844 viewport, reduced motion enabled, 302 px image and document width 390 px without horizontal overflow. The scrollable conversation preserves the full image proportions.
- [WAHA connection check](waha-readiness.json): read-only check recorded WORKING / GOWS with a connected account. No message was sent.

The catalog editor was also exercised through the real UI against disposable PostgreSQL: Save normalized ` GLOSSY ` and `doff` to `glossy` and `doff`; reopening showed revision 2 and no unsaved changes. This was an additional UI check, outside the 54 regression turns.

## Models, latency and cost

| Measurement | Observed result |
| --- | --- |
| Intent and consistency model | `openai/gpt-4.1` |
| Factual answer model | `anthropic/claude-haiku-5.5` |
| Embedding | Existing Nemotron, 2,048 dimensions, cosine |
| Knowledge namespace | `kb-b137be22405b4e2fb10f36ab352240ca` |
| Local catalog revision | 28, before the additional editor check |
| Median / p95 response latency | 7.52 s / 18.24 s |
| Maximum latency | 23.12 s |
| Logical model calls | 151 |
| Reported model cost | US$0.328388 |

Latency includes the reset shortcut, which took zero seconds. Cost covers only the 54 retained regression turns and excludes embedding calls, development probes and additional layout/editor checks. All retained model stages reported cost; OpenRouter did not expose individual upstream provider identities in the retained metadata.

An earlier mini-model run passed 34/35 cases, and a refined 38-case run passed 37/38, missing a Yasin preview request. Refinements addressed product ambiguity, preview intent and answer truncation; the final GPT-4.1 configuration passed 38/38 independent cases and 16/16 conversation turns. Both prompt and model changed, so the improvement cannot be attributed solely to the model. The same cases informed refinement: these are regression results, not held-out accuracy estimates or a guarantee for arbitrary requests. This is not a DeepEval four-metric assessment.

## Automated checks and review

- `LANGSMITH_TRACING=false venv/bin/python -m pytest -q`: **269 passed, 11 skipped**, two warnings, 56.59 s. Paid DeepEval tests remained skipped. Database fixtures used disposable PostgreSQL on loopback port 54585.
- `node --test testing/*.mjs`: **24 passed**.
- `npm run lint` and `npm run build` in `frontend/`: passed; lint retained ten existing warnings. Build includes TypeScript checks.
- `venv/bin/python dataset/image-product/verify_catalog.py`: all 27 image files/checksums valid across seven groups. Existing selected image bytes are unchanged.
- `git diff --check`: passed.

Spec review covered the approved behavior and delivery guarantees. Findings fixed before completion included 24-hour intent-history expiry, product/view pinning in answer validation, clarification for missing multi-product comparisons, and preserving prior uncertain image submissions after eligibility changes.

Standards review covered failure behavior, persistence and maintainability. Findings fixed included retaining the existing empty-knowledge response, accounting for intent/check usage, persisting diagnostics, and setting structured-call timeout/retry bounds on the actual model client constructor. Offline tests also cover invalid intent IDs, provider failure, answer contradictions/truncation, legacy media, disable fences and independent delivery checkpoints.

## WhatsApp readiness and release boundary

The shared RAG result is exercised through the WAHA worker with mocked transport, verifying image-before-text order, failure notices, pinned selections and uncertain-send protection. The real provider connection was checked read-only. **This implementation has not been deployed, and live WhatsApp acceptance/delivery ACKs for this version have not been verified.** Playground success and a WORKING provider session do not establish end-to-end production delivery.

Follow the [catalog runbook](../../runbooks/product-image-catalog.md#semantic-intent-rollout-2026-10-23) when releasing: backfill verified attributes for unchanged approved comparison records, deploy/restart the backend, verify the requested-images feature switch, then use an authorized controlled account to inspect image and text receipts. There is no SQL schema or embedding migration. WAHA needs no new intent-specific setting; its session, public Storage URL reachability and existing webhook/worker path must remain healthy. Uncertain submissions must not be automatically replayed.
