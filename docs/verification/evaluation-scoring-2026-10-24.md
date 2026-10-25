# Evaluation scoring repair and shared chatbot tuning

## Scope and evidence

This is local source and real-provider verification, not a production deployment. Provider probes and durable evaluations used the configured administration store and frozen knowledge snapshot; automated tests used a disposable loopback PostgreSQL instance. No production database was used by pytest. No schema, embedding model, embedding dimensions, or active knowledge namespace changed.

The original run `784c986345784eb1bc42eec807be6796` remains a historical record with ten saved answers and forty unavailable scores. LangSmith MCP verified the mandatory-reasoning HTTP 400 rejection and the subsequent output-token truncation. The root cause, canonical trace URLs, provider metadata, and primary-source research are recorded in [the investigation](../research/2026-10-24-evaluation-reliability.md).

Repaired baseline: `00d9137f1d4d404c988b6fa9f6015706`, derived from the saved-answer recovery `684f98a3cf884d30801b44262977877f`. All ten original answers, references, and retrieved contexts match the original record. All 39 previously valid scores match the recovery record; only its failed score was regenerated. Final baseline coverage is 40/40, with zero scoring errors.

The tuned comparison uses the same ten questions/references, knowledge snapshot `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, answering model `anthropic/claude-haiku-5.5`, judge `z-ai/glm-5.3-flash`, top-k 5, and prompt snapshot. The shared pipeline uses semantic candidate retrieval plus BM25/RRF reranking, and removes an unrelated image-unavailability prefix on ordinary nonvisual questions. This is an exploratory combined change, not an isolated causal experiment.

Both comparisons use low judge reasoning effort and the same metric rubrics/threshold. Successfully scored metrics retain their original judge calls. Failed contextual-precision calls are retried with concise-reason instructions and bounded truncation recovery; source/current judge settings are recorded. These output-style differences and judge variability limit strict comparability.

## Verification

- Backend offline suite: **284 passed, 11 skipped**. The skipped cases require paid-provider or reviewed-conversation opt-in.
- Frontend navigation/evaluation evidence tests: **12 passed**.
- Frontend lint and TypeScript/Vite build passed. Existing shared-component and hook warnings remain.
- `git diff --check` passed.
- Authenticated real baseline view showed all four metrics with 10/10 scores and zero errors.
- Desktop light and mobile dark screenshots inspected. Measured mobile document width equals viewport width, 390 px. Result reading, run identity, coverage, standard error, and small-sample limitations remain visible.
- Keyboard Tab/Shift+Tab reaches the return action with `:focus-visible` and a 3 px focus ring.
- Original history/filter/scroll, loading/empty/error, provider dropdown, and theme verification remains recorded in [the UI report](evaluations-ui-2026-10-23.md).
- Local backend restarted with the final implementation; existing frontend process retained. Disposable test PostgreSQL stopped after the suite.

## Anti Slop delivery gate for this extension

The complete per-rule UI delivery gate remains in the linked UI report. This extension was checked against each applicable item:

- R-02, R-15, R-16 PASS: added labels describe scoring, retries, coverage and uncertainty directly; no promotional copy or em-dash prose added.
- R-03, R-34, C-4 PASS: inspected light desktop/dark mobile; 390 px viewport has no horizontal overflow.
- R-17, R-36, R-38, C-5 PASS: percentages and counts come from saved provider results; errors remain unavailable and original evidence remains unchanged.
- R-18, R-23, R-28 PASS: no people, testimonials, visual assets or FAQ added.
- R-24, R-26, C-2 PASS: protected retry endpoint has authentication/CSRF/input tests and durable real-provider runs; return/export destinations retain existing handlers.
- R-25, R-32 PASS: existing theme text palette retained; actual keyboard focus ring verified. No new text color introduced.
- R-27 PASS: scoring failures now have explicit guidance and recovery; loading polls real job state and saved-answer retries say Reuse.
- R-33, R-35 PASS: source edits, successful build, offline suite, authenticated real-data browser verification and live provider recovery recorded above.
- R-01, R-04, R-06 through R-14, R-19 PASS: existing typography, flat metric grid, disclosure rows and semantic status styling retained; no decorative charts, gradients, glass, shadow, backgrounds, icons or animation added.
- R-37, Liveliness, C-1, C-3 PASS: calm paper-and-ink task direction retained; added detail makes scoring evidence interpretable.
- R-05, R-11, R-20, R-21, R-29 through R-31 PASS: established layout roles, radii, domain evidence and themes retained.

## Limits

Ten curated legacy cases cannot certify production accuracy. The means are not correctness probabilities; standard errors exclude judge calibration uncertainty. Human review and a broader independent benchmark remain necessary. No threshold was lowered, reference rewritten, or difficult case removed. A location branch reference and payment-policy case still have incomplete retrieval/reference agreement and remain visible as low recall scores.

## Final real-provider comparison

Final tuned result: `35f66aaf15a744dd835aabd63329e471`, retrying the single failed metric from `4b2b1b4ec01a47839615742ad4633218`. Both baseline and tuned runs have **40/40 valid scores, zero scoring errors, and completed status**.

| Metric | Repaired baseline | Tuned | Paired mean change | Paired standard error |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 100.00% | 100.00% | +0.00 pp | 0.00 pp |
| Answer Relevancy | 98.57% | 100.00% | +1.43 pp | 1.43 pp |
| Contextual Recall | 66.67% | 86.67% | +20.00 pp | 13.33 pp |
| Contextual Precision | 70.11% | 76.44% | +6.33 pp | 5.77 pp |

No significance or production-accuracy claim follows from these ten cases. Contextual precision fell on case 5 (70.00% to 63.89%); aggregate improvement does not erase this regression. Case 6 recovered the guarantee/reprint policy previously outside the retrieved top-five, raising contextual recall from 0 to 1.

LangSmith MCP verified the final repaired metric: complete five-context verdicts in 248 completion tokens, explanation in 79, both `finish_reason=stop`. [Final repaired metric trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a169e4-0554-7e30-bdbb-91d0fb948f41/run/01a169e4-0724-7f30-b8c0-24fdea4a7831?start_time=2026-10-23T17:51:54.148953Z).

The final tuned run was also opened in the authenticated result view: all four metrics displayed 10/10 case scores and zero errors, with no Scoring failed state. Browser task space closed after verification.
