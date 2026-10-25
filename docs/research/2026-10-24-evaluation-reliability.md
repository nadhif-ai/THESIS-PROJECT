# Reliable RAG evaluation and the October scoring failure

## Observed failure

Run `784c986345784eb1bc42eec807be6796` stored ten answers but zero of forty metric scores. Every metric recorded `BadRequestError`; this was a provider failure, not a zero-quality result.

The LangSmith MCP confirmed repeated HTTP 400 responses: the selected `z-ai/glm-5.3-flash` endpoint requires reasoning, while the application sent `reasoning.effort="none"`. The old adapter retried the same invalid request after removing its JSON schema. Removing that schema could not resolve a reasoning-parameter rejection.

Canonical trace evidence: [judge rejection](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/3529df21-01d9-4f91-bf4d-6d0f783665ea/trace/01a169ab-9e81-7ab0-91d4-424d66b71b64/run/01a169ab-9ea2-7fc1-a04a-6038b01f868a?start_time=2026-10-23T16:50:17.378201Z).

The case-one trace separates the working answer path from the failed judge: retrieval took approximately 3.29 seconds, answer generation approximately 3.97 seconds, and the complete case-answer trace approximately 12.75 seconds. Sampled judge rejections completed in milliseconds. The overall elapsed run time therefore cannot be interpreted as ten minutes of successful scoring.

A second live failure exhausted 4,096 completion tokens, including 1,422 reasoning tokens, before the contextual-precision verdict JSON was complete (11,859 visible characters). Raising the limit alone was inconsistent. The adapter now requests concise reasons while preserving every required verdict and the metric rubric, and retries token exhaustion once up to 8,192 tokens within the step deadline. Permanent HTTP errors are not retried. The repaired case returned all five verdicts with `finish_reason=stop` in 254 completion tokens, followed by its explanation in 120 tokens. [Successful verdict trace, verified through LangSmith MCP](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a169d9-f8ba-7ad3-8c5e-07fbeb09cf27/run/01a169d9-fa6f-78f3-9361-9c1a8617484b?start_time=2026-10-23T17:40:55.535093Z).

## Changes and invariants

- Keep the four named metrics and their thresholds. Do not lower thresholds, relabel historical measures, remove hard cases, or convert provider errors to zero.
- Use model-supported reasoning settings. Current provider metadata advertises `low` for all three offered judges; GLM advertises reasoning as mandatory. Unknown/custom judges retain their provider default.
- Keep structured output enforced. Permanent request/authentication/credit/model-access errors stop a durable evaluation after the first rejected metric, preserve evidence, and fail the job explicitly.
- Detect output-token exhaustion before accepting a response. Record only safe operator guidance and numeric diagnostics, without storing raw provider error bodies or credentials.
- Retry scoring as a separate durable run over the original answers, references, and retrieved contexts. Retain already available scores; retry missing/failed metrics only. Preserve the original result unchanged.
- Distinguish job completion, scoring coverage, answer errors, metric failures, and reporting failures in the UI.

## Interpreting percentages

The displayed percentage is an arithmetic mean of available case scores multiplied by 100. It is neither a pass rate nor the probability that an answer is correct.

The UI now reports the number of scored cases, error counts, and standard error of the mean (`sample standard deviation / sqrt(n)`). An approximate normal 95% interval is shown only for complete, varied samples with at least thirty scored cases. Thirty is a conservative display policy, not proof of adequate sample size. The interval assumes independent, representative cases and omits judge-calibration uncertainty. Correlated questions require clustered analysis; incomplete scoring can bias the observed mean even if its standard error looks small.

Ten curated questions remain useful regression cases, but are not a representative production-quality estimate. More questions should be independently reviewed across real task categories, including pricing/units, location, file requirements, returns, ambiguous inquiries, and unanswerable questions. Reference review and human judge calibration remain necessary; this change does not fabricate either.

## Tuning protocol

Compare original saved answers re-scored by the repaired judge against the shared pipeline after tuning. Freeze question/reference rows, synchronized knowledge snapshot, answering model, judge, top-k, and prompt snapshot. Record retrieval recipe and intent model separately. Do not compare a failed 0/40 run as if it were a zero baseline.

The observed return-policy failure had the relevant guarantee/reprint passage at semantic rank eleven, outside the five passages sent to the answer model. Candidate retrieval now considers a larger semantic pool and fuses cosine rank with BM25 term rank using reciprocal rank fusion, then returns the configured k. The original cosine distance is retained as a distance; an RRF rank is never presented as cosine similarity or confidence. No embedding/index migration or knowledge activation change is needed.

Ordinary questions whose product-image classification is unsupported or ambiguous no longer inherit an unrelated image-unavailability sentence when their action is `none`. Actual visual requests and failed intent extraction retain their guarded attachment path.

## Primary sources researched through Exa

- [DeepEval RAG evaluation](https://deepeval.com/docs/getting-started-rag): distinguish generator metrics from retrieval metrics and retain their required references/runtime context.
- [DeepEval Faithfulness](https://deepeval.com/docs/metrics-faithfulness) and [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision): metrics depend on semantic judge decisions; changing evaluation mode changes comparability.
- [OpenRouter reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens): mandatory reasoning cannot be disabled; reasoning consumes the output-token budget and can leave no visible JSON.
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs): model/endpoint support and schema enforcement matter; stripping a schema is not a general request-rejection recovery strategy.
- [Anthropic statistical evaluation guidance](https://www.anthropic.com/research/statistical-approach-to-model-evals): report standard errors, account for clustered questions, and use paired comparisons rather than interpreting means alone.
- [Anthropic evaluation design](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): stable environments, interpretable graders, and human calibration are prerequisites for trusting model-based grades.
- [Elastic hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid): lexical and semantic retrieval can complement one another; validate RRF on the actual dataset.
- [OpenSearch reciprocal rank fusion](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/): rank fusion combines incomparable relevance scales without inventing a common similarity score.

Final live comparison and verification: [40/40-score baseline and tuned results](../verification/evaluation-scoring-2026-10-24.md).
