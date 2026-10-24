# RAG precision study, 24 October 2026

## Questions and protocol

The optimization aim is Contextual Precision >=87% while retaining Contextual Recall around 86.67% and factual answer quality. The target is not a promise or a reason to alter thresholds, references, or perfect scores.

The original 10-question legacy benchmark remains unchanged. Answer model `anthropic/claude-haiku-5.5`, intent model from the captured existing configuration, scoring model `z-ai/glm-5.3-flash`, Nemotron 2048/cosine, requested top-k 5, character size 1000 / overlap 100 and the four DeepEval rubrics/threshold 0.7 remain fixed. Each phase captures its system prompt and knowledge namespace. Retrieval and source corrections were tested first under the original captured prompt; subsequent general information/handoff and grounding prompt fixes are separate phases. They cannot be described as a single isolated ranker experiment.

Baseline answers and ordered passages were frozen from `35f66aaf15a744dd835aabd63329e471`. A uniform fresh judge pass on those exact answers/passages separates evaluator movement from actual pipeline change. It produced 98.75% Faithfulness, 98.89% Answer Relevancy, 86.67% Recall, 89.56% Precision. The historical 76.44% precision baseline remains intact; its increase on rescoring alone is not a retrieval win.

A separate durable run `49a8037734a741c1b965d8b54b05111a` captured the old namespace before source activation and tested the first ranking/query repairs. It retains its original runtime context; the later product-history correction is recorded separately. The uniform baseline and phase-controlled research runs are the primary comparison, not selective failed-only judge retries.

## Verified causes and repairs

1. An address question was expanded into contacts and order workflow, diluting its retrieval intent. Explicit informational questions now keep their task; genuine handoffs retain their expansion.
2. Product-label enrichment replaced customer history and dimensions. Labels now append to the query; an explicit product change resets retrieval history to avoid old-product contamination.
3. RRF tied address and contacts, and BM25 counted negative product mentions. A bounded multilingual Pinecone BGE reranker follows the semantic/BM25 candidate pool. All genuine cosine distances are preserved; rerank scores are separate model scores, not confidence probabilities. Failures retain the RRF order and mark the fallback in evidence. No new dependency or embedding migration was introduced.
4. 83/139 passages inherited a separator as their root heading. Explicit sections-v2 fixes separator headings; sections-v1 still exactly reconstructs all 139 historical passages.
5. Live source headings mixed physical locations/contact channels and policy responsibilities. Source-backed restructuring and the previously business-confirmed Kiss Cut/manual distinction were staged through Knowledge Replace and activated through one existing Sync workflow. See the [source ledger](../../dataset/knowledge-revisions/2026-10-24/provenance.json) and [knowledge audit](2026-10-24-knowledge-audit.md). No old snapshot was overwritten.
6. The answer prompt treated branch selection as a prerequisite to giving available addresses. A general information-versus-order-handoff rule now answers available information directly.
7. Absence from retrieved context was incorrectly promoted to absence from the shop's whole catalogue. Grounding now scopes unavailable information to evidence actually retrieved and avoids unsupported product comparisons/unrequested alternatives.
8. A no-residue material property was incorrectly extended into a paint-safety guarantee. A general evidence rule now distinguishes stated material properties from unsupported safety or damage-free-removal guarantees.

## Knowledge activation

Original namespace: `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, 139 passages, revision 10. Sync `0a4b41713f9e423799b20387bda6597b` embedded and verified 142 passages, then atomically activated `kb-0a4b41713f9e423799b20387bda6597b` at revision 15. The old namespace served throughout build. Source/preprocessing changes are intentional experimental variables; size/overlap and embedding identity are unchanged. The later live phone value was preserved. Canonical source 03 and legacy evaluation references were not rewritten.

## Judge audit and limitations

100% Faithfulness and Answer Relevancy were real raw 1.0 means, not rounding. The recorded configuration accepted 11 borderline Faithfulness verdicts and 23 borderline Relevancy verdicts. Truth extraction also dropped shop-error examples in a later pass, causing a false penalty on a supported claim; passage evidence was sometimes attached to the wrong contextual-precision rank. See [the calibration audit](2026-10-24-judge-calibration.md) and [independent source review](2026-10-24-precision-study-quality-review.md).

Four diagnostic DeepSeek judge calls independently scored saved/tuned cases 6 and 10. They corroborate directional ranking improvements, but absolute scores differ. They are a separate diagnostic and never replace the official GLM means. Displayed percentages use two decimals and show accepted-borderline counts; no perfect score is capped to meet a target interval.

Legacy case 2 still has minimum 60% DP in the active business source versus 50–60% in the reference; case 1's reference also includes hours that the question does not ask for. These remain visible limitations, not references silently changed to favor the bot.

## Development-validation and untouched final hold-out

Twelve additional development-validation questions were generated with DeepEval from exact pre-change source excerpts and frozen before optimized answers were inspected. Contrasts include addresses versus contact numbers, area printing versus packages/frame-only, shop versus customer-file errors, and Cromo/Vinyl/OneWayVision. Three invalid initial generations were replaced before freezing; all provenance is retained. Labels have agent source validation, not independent human business review. This small, synthetic, scoped sample is not production accuracy. See [generation protocol](2026-10-24-retrieval-holdout-generation.md). Their findings informed later prompt fixes, so these twelve cases are not a clean final unseen sample.

The old/new knowledge pair uses identical BGE ranking and original prompt on both snapshots, isolating knowledge changes rather than claiming a clean reranker gain. Later final-prompt validation uses the same frozen questions. If contextual-only metric inputs (question, reference, ordered passage texts) are identical after a generator-only prompt change, those recorded scores may be retained with their original trace URL; otherwise they are recomputed. Faithfulness/Relevancy are always evaluated on the new answer. All reuse is explicit in case evidence.

After the final source, ranking and prompt configuration froze, eight new source-only questions were generated, source-validated by an agent and frozen. They were evaluated once, without subsequent tuning or reference changes. All 32 scores are fresh and valid: precision 98.96%, recall 96.88%, Faithfulness and Answer Relevancy both 100.00%. The recall shortfall is the judge rejecting a reference greeting, while all technical JPEG facts are present. Scores and references remain unchanged. See [final generation provenance](2026-10-24-retrieval-final-holdout-generation.md) and the independent review. Eight synthetic cases cannot establish production accuracy.

## Primary-source research via Exa and Context7

- [DeepEval Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision): ordering relevant nodes above irrelevant nodes is the metric's purpose; weighted precision differs from fraction of all passages relevant.
- [Pinecone reranking](https://docs.pinecone.io/guides/search/rerank-results): query-plus-candidate second-stage relevance ranking, provider model API and index mapping.
- [Pinecone multilingual BGE model](https://docs.pinecone.io/models/bge-reranker-v2-m3): model contract and truncation behavior; no app-specific performance guarantee.
- [Anthropic contextual retrieval](https://www.anthropic.com/engineering/contextual-retrieval): preserve useful chunk context and evaluate reranking tradeoffs rather than assuming a general gain.
- [Anthropic statistical evaluation guidance](https://www.anthropic.com/research/statistical-approach-to-model-evals): paired comparisons and uncertainty; ten curated cases, twelve development-validation cases and eight final source-generated cases cannot certify customer correctness.

## Reproduction

`testing/evals/precision_study.py` is a paid operational evaluator through the shared pipeline, not a separate customer retrieval path or an offline database test. Frozen manifests capture configurations, questions, references, namespaces and prompt snapshots. It writes visible per-case JSON and resumes exact completed cases by fingerprint rather than regenerating them. Example from repository root:

```sh
LANGSMITH_TRACING=true venv/bin/python -m testing.evals.precision_study manifest.json output-directory
```

The repository's normal paid pytest evaluation remains available through `venv/bin/deepeval test run testing/evals/test_chatbot.py`. Offline pytest never runs this research operation. Final metrics, complete evidence, paired changes and verification are recorded in [the study verification report](../verification/rag-precision-study-2026-10-24.md).
