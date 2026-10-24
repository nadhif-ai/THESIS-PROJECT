# Precision study verification, 24 October 2026

## Final outcome

The final legacy benchmark records **93.71% Contextual Precision, 86.67% Contextual Recall, 40/40 valid scores and zero scoring/answer errors**. Twelve development-validation cases record 93.75% precision, 100.00% recall and 48/48 valid scores. A separate eight-question untouched final hold-out records **98.96% precision, 96.88% recall and 32/32 valid scores**, with zero errors. All three samples exceed the 87% precision aim; legacy recall is preserved. This is a small benchmark outcome, not a calibrated probability of customer correctness. No metric was capped, threshold lowered, difficult case dropped, or legacy reference changed.

| Phase | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision |
| --- | ---: | ---: | ---: | ---: |
| Historical saved | 100.00% | 100.00% | 86.67% | 76.44% |
| Same answers, uniform judge | 98.75% | 98.89% | 86.67% | 89.56% |
| First query/ranking repairs; old knowledge | 100.00% | 97.78% | 76.67% | 91.10% |
| Ranking + knowledge; original prompt | 100.00% | 100.00% | 86.67% | 94.75% |
| Information-first prompt | 100.00% | 97.50% | 86.67% | 93.71% |
| Grounding correction | 98.57% | 100.00% | 86.67% | 93.71% |
| Final verified pipeline | 100.00% | 98.00% | 86.67% | 93.71% |

Historical→uniform baseline movement is entirely rejudging of the same answers/passages. Against the uniform baseline, final precision changes by **+4.15 percentage points**, not the full 17.26 points versus the historical saved mean. The intervening same-prompt pipeline phase reached 94.75%; the final 93.71% is retained under a generator-only grounding change. Absolute judge variation and source/reference conflicts limit causal claims.

Faithfulness and Answer Relevancy remain model-based ratios; the earlier 98.57% Faithfulness mean included a questionable case 6 penalty under source review. The final legacy Faithfulness target of greater than 95% but below 100% remains unmet: its raw ratio is 100.00%. Final Answer Relevancy is 98.00%, but the rejected fragments include isolated words extracted from coherent sentences; this is a calibration concern, not proof of a real 2% answer-quality defect. No perfect score was capped to force the desired interval.

## Per-case legacy evidence

| Case | Historical CP | Uniform CP | Final CP | Final CR | Final F | Final AR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 50.00% | 50.00% | 100.00% | 66.67% | 100.00% | 100.00% |
| 2 | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% | 100.00% |
| 3 | 100.00% | 100.00% | 80.42% | 100.00% | 100.00% | 100.00% |
| 4 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5 | 63.89% | 63.89% | 100.00% | 100.00% | 100.00% | 100.00% |
| 6 | 20.00% | 86.67% | 100.00% | 100.00% | 100.00% | 100.00% |
| 7 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 8 | 80.56% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 9 | 100.00% | 100.00% | 86.67% | 100.00% | 100.00% | 100.00% |
| 10 | 50.00% | 95.00% | 70.00% | 100.00% | 100.00% | 80.00% |

Each full answer, reference, ordered passage text/metadata, cosine/rerank scores, calculation verdicts, usage and trace URL is retained in [the complete evidence JSON](../../testing/comparisons/2026-10-24-precision-study.json). Final intent-model decisions were cross-checked against recorded evaluation conversations and are included.

## Development-validation contrasts

These 12 questions were initially frozen from source-only generation before optimized answers were inspected, with agent source validation rather than human business review. Their later findings informed general prompt fixes; they are development-validation, not a clean final hold-out. The knowledge-before phase already uses the BGE ranker; its comparison isolates knowledge changes, not a clean ranker ablation.

| Phase | F | AR | CR | CP | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Old knowledge, original prompt | 100.00% | 100.00% | 100.00% | 100.00% | 48/48 |
| New knowledge, original prompt | 100.00% | 96.67% | 100.00% | 97.22% | 48/48 |
| New knowledge, information-first prompt | 100.00% | 97.08% | 100.00% | 93.75% | 48/48 |
| Grounding correction | 100.00% | 100.00% | 100.00% | 93.75% | 48/48 |
| Final verified pipeline | 100.00% | 100.00% | 100.00% | 93.75% | 48/48 |

Development-validation precision falls from 100.00% to 93.75% on this small sample. This regression is preserved, despite remaining above target; no claim is made that all unseen intents improved.

| Development-validation case | Final F | Final AR | Final CR | Final CP |
| --- | ---: | ---: | ---: | ---: |
| retrieval-holdout-01 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-02 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-03 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-04 | 100.00% | 100.00% | 100.00% | 91.67% |
| retrieval-holdout-05 | 100.00% | 100.00% | 100.00% | 75.00% |
| retrieval-holdout-06 | 100.00% | 100.00% | 100.00% | 83.33% |
| retrieval-holdout-07 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-08 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-09 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-10 | 100.00% | 100.00% | 100.00% | 75.00% |
| retrieval-holdout-11 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-holdout-12 | 100.00% | 100.00% | 100.00% | 100.00% |

## Untouched final hold-out

After all source, ranker and prompt changes were frozen, eight new questions were generated from original source excerpts, agent-source-validated and frozen. They were evaluated once, with no further optimization after outputs were observed. No retrieved scores are reused for this fresh set. Labels are not human business-reviewed; this remains a small synthetic sample.

| Sample | F | AR | CR | CP | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Untouched final eight | 100.00% | 100.00% | 96.88% | 98.96% | 32/32 |

| Case | F | AR | CR | CP |
| --- | ---: | ---: | ---: | ---: |
| retrieval-final-holdout-01 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-final-holdout-02 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-final-holdout-03 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-final-holdout-04 | 100.00% | 100.00% | 100.00% | 91.67% |
| retrieval-final-holdout-05 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-final-holdout-06 | 100.00% | 100.00% | 100.00% | 100.00% |
| retrieval-final-holdout-07 | 100.00% | 100.00% | 75.00% | 100.00% |
| retrieval-final-holdout-08 | 100.00% | 100.00% | 100.00% | 100.00% |

The JPEG case’s recall penalty comes solely from the reference greeting “Halo!” being absent from source passages; all three technical requirements occur at rank 1 and received attributable verdicts. Its raw 75.00% case recall is preserved. Faithfulness and Answer Relevancy remain 100.00% on this sample, so both below-100% aims are unmet. These are accepted-verdict ratios, not calibrated correctness probabilities.

The final Ritrama trace was inspected through LangSmith MCP: [recorded final case and scores](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a16a1a-0c71-75f0-819e-cbabe006b72d/run/01a16a1a-0c71-75f0-819e-cbabe006b72d?start_time=2026-10-23T18:50:54.449781Z).

Dataset SHA-256: `0741633ac4777163f5611e4843a786299f9ec8391e37c2ddced5c63f45751965`. The final configuration is identical to the verified development run. Source-only generation provenance and all raw questions, references, answers, ordered passages, scoring calculations and trace URLs accompany the evidence artifact. Eight observations do not establish general production accuracy.

## Paired changes and uncertainty

| Metric | Final minus uniform baseline | Paired standard error |
| --- | ---: | ---: |
| Faithfulness | +1.25 pp | 1.25 pp |
| Answer Relevancy | -0.89 pp | 2.39 pp |
| Contextual Recall | +0.00 pp | 0.00 pp |
| Contextual Precision | +4.15 pp | 7.45 pp |

These standard errors exclude calibration error and dependence between related questions. No significance claim or 95% production-confidence interval is justified. Two diagnostic cases scored by DeepSeek show directional rank improvements but disagree with GLM on relevance. The complete diagnostic and source review are preserved.

## Verification and state

- Sync job `0a4b41713f9e423799b20387bda6597b` completed; active/applied revision 15, 142 passages, no pending changes. Old snapshots remain available.
- Historical all-failed run remains unchanged with 40 unavailable scores. All uniform baseline answers/references/ordered contexts exactly match the historical saved evidence.
- Final generator-only round retains 44 contextual scores only after exact question/reference/ordered-passage equality checks; 44 Faithfulness/Relevancy scores were freshly measured on 22 new answers. Reuse links point to the original judge traces.
- Final offline backend suite: 304 passed, 11 skipped. Final prompt/print-inquiry checks: 25 passed. Focused reranker malformed-response fallback: 4 passed. Frontend navigation/evidence/rounding/borderline tests: 15 passed. Lint and TypeScript/Vite build pass with existing shared-component/hook warnings.
- Authenticated result UI shows two decimal places, exact scoring coverage and accepted-borderline counts. Desktop dark/light and 390px mobile inspected; measured document width 390px, no horizontal overflow.
- Backend restarted with final source and tracing; no application deployment, schema migration, embedding migration, or WhatsApp customer send was performed.

## Anti Slop delivery gate for the numeric/evidence extension

- R-02/R-15/R-16 PASS: task-specific scoring and borderline copy; no promotional copy introduced.
- R-03/R-34/C-4 PASS: dark/light desktop and mobile checked; 390px document width matches viewport.
- R-17/R-36/R-38/C-5 PASS: percentages derive from raw records; perfect scores, judge variance and held-out regressions remain visible.
- R-18/R-23/R-28 PASS: no fictional people/assets/FAQ introduced.
- R-24/R-26/C-2 PASS: existing result, export, history and theme controls retained; authenticated Replace and Sync exercised.
- R-25/R-32 PASS: existing semantic theme colors/focus components retained; no new color or keyboard behavior introduced.
- R-27 PASS: existing loading/error/empty flows retained; missing scores remain unavailable.
- R-33/R-35 PASS: source edits, 304 offline tests, 15 frontend tests, build and real-data browser verification recorded.
- R-01/R-04/R-06 through R-14/R-19 PASS: existing typography/flat metric grid retained, no decoration or motion added.
- R-37/Liveliness/C-1/C-3 PASS: established paper-and-ink task direction retained; additions clarify evidence.
- R-05/R-11/R-20/R-21/R-29 through R-31 PASS: established component roles, radii, domain evidence and theme system retained.

## Reproduction and limits

See [the study protocol and primary-source research](../research/2026-10-24-rag-precision-study.md), [source audit](../research/2026-10-24-knowledge-audit.md), [judge calibration](../research/2026-10-24-judge-calibration.md), and [independent quality review](../research/2026-10-24-precision-study-quality-review.md). Full manifests and raw evidence accompany the linked JSON. These are source-controlled local research results, distinct from a deployment or human acceptance study.
