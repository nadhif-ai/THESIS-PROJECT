# Judge calibration audit — 24 October 2026

## Evidence inspected

Saved run `35f66aaf15a744dd835aabd63329e471` (`/tmp/evaluation-tuned-final.json`), a failed-only scoring retry of `4b2b1b4ec01a47839615742ad4633218`, contains ten legacy QA cases and forty numeric scores with no metric errors. Its knowledge snapshot is `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, corpus SHA-256 `a2f9e7365454bcb8ac069fe599276bec21eca7d5179f553a68c8bcdb7a27ca49`, dataset SHA-256 `be04e9dc4d73e1c8a123e96a16452cf35999d7c6b33837297055e3b9fd37555b`, answering model `anthropic/claude-haiku-5.5`, judge `z-ai/glm-5.3-flash`, and top-k 5. The installed and recorded DeepEval version is 4.2.8; the evaluation recipe is `rag-four-metrics-v1`.

This audit made no provider calls and changed no saved scores, references, thresholds, or metric definitions. It inspected saved claims/statements, verdicts, reasons, retrieved passages, references, runner arithmetic, and installed library implementations/prompts. Saved evidence is an LLM assessment, not an independent staff assessment.

## Why the two answer metrics are 100%

Both raw means are exactly `1.0`; they are not values such as `0.999` rounded up. Every case's Faithfulness and Answer Relevancy score is exactly `1.0`. All answer-metric denominators are nonzero, so the library's empty-item convention did not cause these particular perfect scores.

| Metric | Yes verdicts | Borderline verdicts | No verdicts | Official macro mean |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 57 | 11 | 0 | 100.00% |
| Answer Relevancy | 54 | 23 | 0 | 100.00% |

The configured metrics use their library defaults: `strict_mode=False`, and Faithfulness `penalize_ambiguous_claims=False`. Both accept `yes` **and** `borderline`. The saved calculation traces faithfully reproduce that arithmetic. The threshold of 0.7 determines the pass indicator; it does not inflate a fractional score to 1.

The installed Faithfulness prompt uses `no` for direct contradiction and `borderline` for claims unsupported by the retrieved evidence, including unsupported but noncontradictory assertions. Answer Relevancy uses `borderline` for ambiguous/supporting information. Therefore these scores mean that no extracted item was judged a direct contradiction or irrelevant under the configured definitions. They do not establish that every claim is supported, every requested fact was answered, or every business assumption is correct.

The pooled borderline shares are 11/68 (16.18%) of Faithfulness verdicts and 23/77 (29.87%) of Answer Relevancy verdicts. These are diagnostic counts across items, **not replacement metric scores**, calibrated uncertainty estimates, or case-level means.

The library reason-generation stage excludes Faithfulness borderline reasons when `penalize_ambiguous_claims=False`; Answer Relevancy's reason stage also passes only `no` reasons to the final summarizer. With zero `no` verdicts, its prompts explicitly request a positive summary. Consequently the upbeat saved summaries omit substantive uncertainties visible in the item-level evidence. Treat the verdict details as necessary context for interpreting those summaries.

## Per-case calibration priorities

All F/AR scores below are 100.00%; the count pairs show **yes / borderline**. CR and CP are the saved official scores, without adjustment.

| Case | F counts | AR counts | CR | CP | Evidence needing independent review |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 — physical location | 3 / 1 | 4 / 0 | 66.67% | 50.00% | User asks for the address; answer names branches, asks which branch, and postpones supplying either address. AR measures relevance rather than required-answer completeness. The borderline reason says Maps links are absent, but rank 2 contains both Maps URLs: inspect the intermediate truth extraction/judge judgement as well as the answer. |
| 2 — DP versus pay on pickup | 10 / 0 | 4 / 5 | 0.00% | 100.00% | Retrieved policy says minimum DP 60%; legacy reference says 50–60%. This is an independently reviewable reference/source conflict, not a retrieval improvement to claim. Answer's remaining balance of 40% assumes exactly 60% was paid, although the source specifies a minimum. Five AR borderline items concern delivery, payment methods, or a quotation follow-up. |
| 3 — waterproof food-label pricing | 4 / 4 | 10 / 2 | 100.00% | 100.00% | Half of extracted claims are borderline: information needed for calculation, available kiss-cut tariff, calculation capability, and absent food-contact safety information. Some are appropriate uncertainty/clarification rather than harmful hallucinations. Check the distinction between absence from returned context and absence from the entire knowledge base. |
| 4 — file formats/JPEG | 9 / 0 | 4 / 5 | 100.00% | 100.00% | Extended TIFF/CDR/AI/PSD requirements, a spanduk-specific warning, and file-delivery advice are counted as supporting information. Independently assess excessive detail and whether the question needed a shorter direct JPEG answer. |
| 5 — Flexi 280 price | 5 / 1 | 6 / 2 | 100.00% | 63.89% | Prices and area arithmetic are supported; future calculation offer and quantity follow-up are accepted borderline. Check that the stated standard/High Resolution options remain explicit rather than silently defaulting a quality. |
| 6 — shop production error | 4 / 2 | 8 / 0 | 100.00% | 20.00% | Supported free reprint and physical proof are present. Admin investigation and checking ongoing orders are borderline. Preserve the production-error versus customer-file-error distinction. The relevant policy passage is rank 5. |
| 7 — three Flexi banners | 6 / 0 | 5 / 2 | 100.00% | 100.00% | Correct conditional standard-price arithmetic; unsolicited High Resolution alternative is accepted supporting information. Test quantities and print-quality choices independently. |
| 8 — 5×5 A3+ capacity | 1 / 2 | 2 / 2 | 100.00% | 80.56% | The 35-piece answer follows the recorded business confirmation. Manual-cut variability and advice to ask admin are borderline. Distinguish the approved kiss-cut table from generic grid calculations; do not substitute an old 40-piece estimate. |
| 9 — cards plus X-Banner | 6 / 0 | 3 / 4 | 100.00% | 100.00% | Rp100,000 matches the reference variant, but the question omits card stock/lamination. The audited dataset notes allow explicit assumptions or clarification. Check those assumptions and excessive upsell detail; relevance alone does not certify variant selection. |
| 10 — outdoor glass sticker | 9 / 1 | 8 / 1 | 100.00% | 50.00% | Source-supported alternatives include China vinyl as well as Ritrama/OWV, while the reference names Ritrama/OWV. The CP reasons also swap the actual rank-4/rank-5 evidence, described below. |

### Contextual Precision evidence-binding failure in case 10

The retrieved rank-4 passage describes **Cromo**, explicitly paper-based and not waterproof. Its saved CP verdict is `yes`, with a reason quoting **One Way Vision** and inward visibility, which are not in that passage. The retrieved rank-5 passage describes **One Way Vision**, including its outward graphic/inward-view properties. Its saved verdict is `no`, with a reason describing **Cromo**. Thus the judge appears to have swapped the last two evidence positions while returning the required five verdicts.

The arithmetic trace matches the returned array, but that does not validate the semantic binding of each decision to its actual ranked passage. The local runner passes plain strings; DeepEval's grouping implementation preserves their order. Its verdict schema contains only `verdict` and `reason`, without a returned passage identifier. The saved calculation validator checks verdict count and arithmetic, not quote-to-passage agreement.

This audit does **not** replace the saved labels, recalculate a more favorable score, or claim a corrected CP estimate. A new independently reviewed diagnostic must establish what went wrong before treating those labels as ranking targets. The case also illustrates that relevance to a question and exact membership in a narrow reference answer can differ: China vinyl's actual passage explicitly lists outdoor storefront glass as a use case, though the judge rejects it for not being a named reference option.

## Improvements that preserve the four official metrics

1. Display percentages as `(raw_score * 100).toFixed(2)`, without capping or rewriting values. A genuine `1.0` remains **100.00%**. A request for a score between 95% and 100% is a research aim, not permission to force a lower result or fabricate errors.
2. Expose the counts of yes, borderline, no, and empty-item cases alongside coverage. Warn that a perfect ratio can include unsupported/ambiguous items; keep the existing official arithmetic and threshold. Keep human business correctness and completeness assessments separate.
3. Freeze and record metric options, library version, template hashes, judge settings, answer prompt, dataset, and knowledge snapshot. The inspected result combines retained scores from the source run with failed-only retries using compact-reason output instructions. It records `source_judge_settings`, but it is not a uniformly rescored experiment. Use fresh complete runs under one frozen scoring protocol for the next controlled comparison.
4. Retain extracted truths/claims/statements and their expected and returned verdict counts. Verify count agreement before accepting diagnostic evidence. The installed library can drop invalid loose-JSON verdicts, and the two answer metrics return 1 for an empty accepted-verdict list; these are general risks, not observed causes of this run's 100% scores.
5. Audit passage binding separately from relevance. A diagnostic with explicit immutable passage IDs and a one-to-one returned ID mapping can catch missing/duplicate IDs and position swaps without changing the relevance rubric. Do not infer a semantic binding error from a simple failed exact-substring match: reasons may paraphrase or translate evidence. Keep a human review path.
6. Independently review the cases above against the actual source passages and intended task. Review reference/source conflicts on business evidence, record provenance, and version any accepted corrections. Preserve the legacy dataset and its historical results. Do not rewrite a reference to favor a generated answer or tune ranker rules to erroneous saved verdicts.

## Held-out validation design

Freeze development choices before selecting new held-out questions. Follow the existing DeepEval dataset generation/review workflow rather than treating hand-written unreviewed answers as goldens. Keep paraphrase families in the same split so the held-out sample is not merely a rewording already used during tuning. Use the same held-out questions and independently reviewed references for baseline and tuned runs.

Include contrasting intents, with both positive and negative policy outcomes:

- Physical branch addresses/Maps versus telephone, WhatsApp and file-submission email; named branch versus both branches; nearest branch without customer origin; hours versus address.
- Printed spanduk priced per square metre versus X-Banner package with frame versus print-only replacement; explicit dimensions, quantity, quality, and intentionally missing specifications.
- Production/operator error versus low-resolution or misspelled customer file; free reprint versus refund/cancellation; physical proof requirement versus an unsupported promise of automatic refund.
- A3+ kiss cut versus manual cut and square versus rectangular sizes; official approved quantities versus generic estimation; sheet price tiers versus piece counts.
- Material recommendation versus unit price versus total price; outdoor water resistance versus unsupported food-contact certification or safety guarantees.
- Out-of-scope requests, absent facts, contradictory supplied specifications, multi-turn corrections, and unsupported order/payment actions. A judge that gives every genuine negative control a perfect result needs calibration before the score is trusted.

Report case-level answer quality/completeness and judge agreement separately from the four official means. Preserve paired question IDs, ranked passage identities/text, knowledge-snapshot changes, references, model settings, and scoring coverage/errors. If a held-out mean remains 100.00%, report it and its limited coverage honestly; do not add incorrect content just to satisfy a requested open interval.

## Reproducible source pointers

- Local metric construction and options: [`testing/evals/metrics.py`](../../testing/evals/metrics.py).
- Saved derivation and accepted verdicts: [`testing/evals/calculations.py`](../../testing/evals/calculations.py), `judge_calculation`.
- Macro averaging and test-case parameters: [`testing/evals/runner.py`](../../testing/evals/runner.py) and [`testing/evals/durable.py`](../../testing/evals/durable.py).
- Original questions/references: [`testing/test_dataset.csv`](../../testing/test_dataset.csv); review guidance: [`testing/evals/qa-reference-candidates.json`](../../testing/evals/qa-reference-candidates.json).
- Installed DeepEval 4.2.8: `deepeval/metrics/faithfulness/faithfulness.py` (`_generate_verdicts`, `_generate_reason`, `_calculate_score`), `deepeval/metrics/answer_relevancy/answer_relevancy.py`, `deepeval/metrics/utils/qag.py` (`score_qag_verdicts`), `deepeval/metrics/base_metric.py` (`idk` alias), and `deepeval/templates/metrics/templates.json` plus `fragments/faithfulness_verdicts_guidelines_text_only.txt`.
- Public definitions: [DeepEval Faithfulness](https://deepeval.com/docs/metrics-faithfulness), [Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy), and [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision). Installed version/source and the frozen run artifacts determine the audited behavior.
