# Precision study: source and judge review — 24 October 2026

## Review status and scope

This is a **completed, unblinded agent review**, not human business validation. It inspects saved completed output JSON under `data/evaluations/precision-study-2026-10-24`, original source excerpts and recorded LangSmith evidence. It makes no paid model calls, rewrites no outputs, and changes none of the four official metric definitions or scores.

**Sample classification:** the original twelve questions in `.retrieval-holdout.json` are now development-validation. Their results informed a later general grounding guard, so they cannot be called the final unseen hold-out. Historical phase/file names containing `heldout` below are retained for provenance. A separate eight-case `.retrieval-final-holdout.json` was generated after the final application prompt froze; its generation/provenance report is [recorded separately](2026-10-24-retrieval-final-holdout-generation.md).

Completed phases reviewed: ten uniform baseline rescoring cases, ten tuned cases, twelve `knowledge_before` validation cases, twelve paired `knowledge_after` cases, ten information-first prompt cases in `final`, twelve corresponding `final-heldout` validation cases, ten grounding cases in `grounded-main`, twelve corresponding `grounded-heldout` validation cases, ten final-guard cases in `verified-main`, twelve corresponding `verified-heldout` validation cases, eight final previously unobserved cases in `untouched-final`, and four separate DeepSeek judge diagnostics. All reported phase means below come from complete saved artifacts.

The baseline is the saved `35f66aaf15a744dd835aabd63329e471` answer/context/reference set, freshly scored using one current protocol throughout. Exact string comparison verified that **all ten answers, all ten references and all fifty ordered passage texts** are unchanged between that saved result and `baseline-uniform`. This makes changes between those two score sets judge/protocol effects, not retrieval improvements.

## Completed phase scores, unchanged

| Phase | Cases | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision | Valid / expected scores | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Historical mixed-call saved result | 10 | 100.00% | 100.00% | 86.67% | 76.44% | 40 / 40 | 0 |
| Uniform baseline rescoring | 10 | 98.75% | 98.89% | 86.67% | 89.56% | 40 / 40 | 0 |
| Tuned knowledge/ranking, original prompt | 10 | 100.00% | 100.00% | 86.67% | 94.75% | 40 / 40 | 0 |
| Held-out `knowledge_before` | 12 | 100.00% | 100.00% | 100.00% | 100.00% | 48 / 48 | 0 |
| Held-out `knowledge_after`, original prompt | 12 | 100.00% | 96.67% | 100.00% | 97.22% | 48 / 48 | 0 |
| Information-first prompt (`final`) | 10 | 100.00% | 97.50% | 86.67% | 93.71% | 40 / 40 | 0 |
| Information-first prompt (`final-heldout`) | 12 | 100.00% | 97.08% | 100.00% | 93.75% | 48 / 48 | 0 |
| Latest grounding prompt (`grounded-main`) | 10 | 98.57% | 100.00% | 86.67% | 93.71% | 40 / 40 | 0 |
| Latest grounding prompt (`grounded-heldout`) | 12 | 100.00% | 100.00% | 100.00% | 93.75% | 48 / 48 | 0 |
| Final property-inference guard (`verified-main`) | 10 | 100.00% | 98.00% | 86.67% | 93.71% | 40 / 40 | 0 |
| Final guard, original development-validation12 (`verified-heldout`) | 12 | 100.00% | 100.00% | 100.00% | 93.75% | 48 / 48 | 0 |
| Untouched final eight, one evaluation | 8 | 100.00% | 100.00% | 96.88% | 98.96% | 32 / 32 | 0 |

For the complete ten-case uniform comparison, the recorded CP change is **+5.19 percentage points**, with unchanged recall. Comparing 76.44% directly with 94.75% would combine a large judge/protocol effect with the pipeline change and overstate the evidence for retrieval improvement. The observed uniform baseline already exceeds the 87% target; that does not make its judgement errors disappear or establish production precision.

The baseline/tuned comparison holds answering model `anthropic/claude-haiku-5.5`, intent model `openai/gpt-4.1`, judge `z-ai/glm-5.3-flash`, top-k 5, reference questions and answer prompt hash `b45b5586bf541dcec270f392cae31386d6ee4e154c82cd927e650666c0cecba5` fixed. It changes the knowledge snapshot, section preprocessing and ranking together, so it is a combined intervention, not an isolated reranker experiment. Snapshots are old `kb-ecaf24265cfa46cab72f1d24f2c29ce0` and new `kb-0a4b41713f9e423799b20387bda6597b`.

The information-first phase separately changes the answer prompt to hash `588bc15082a31c6680e6be298bd0c97104e05abdb59347fd07fe5ade908a2978`. It supplies both real branch addresses immediately in development case 1, resolving the observed completeness failure. The latest grounding-prompt hash is `3dab5af91a992b8c29d03b4a00272a623f6ae3976e135448c52d569bb3ba5190`; that separate phase scopes missing-information claims to the returned context and prohibits unsupported comparisons. Its results are recorded separately from earlier answer phases.

## Judge variance and evidence failures

### Case 6: CP 20.00% → 86.67% without changing retrieval

The historical CP verdict array is `[no, no, no, no, yes]`: the explicit shop-error/free-reprint policy is at rank 5, producing `1/5 = 20.00%`.

The uniform rescore of those **same passages in the same order** returns `[yes, yes, no, no, yes]`, producing `(1 + 1 + 3/5) / 3 = 86.67%`. It now calls rank-1 print-readiness/blurred-file guidance and rank-2 customer-file-error exclusions remotely useful. The actual shop-error policy remains rank 5. This is a changed relevance interpretation, not recovered evidence or better ranking. DeepEval's prompt asks whether a context is *remotely useful*, so supporting contrasts can receive a different verdict even when the main answer passage has not moved.

The tuned result does have a real rank change: the customer-file exception is first and the shop/production free-reprint policy second. Its array is `[yes, yes, no, no, no]` and CP is 100.00%. The relevant policy is now earlier than unrelated finishing/price passages, independently of whether one agrees with every broad relevance decision.

### Case 6: Faithfulness 87.50% includes an apparent false contradiction

The uniform baseline's only `no` Faithfulness verdict rejects the claim that **shop-originated errors** include wrong size/material, machine defect or severe banding. The actual retrieved policy explicitly lists exactly those examples under operator/store errors. A separate passage excludes wrong dimensions in the **customer's submitted file**. The answer distinguishes those origins rather than conflating them.

[LangSmith's actual verdict-call input](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a169fd-fc72-7390-a4c6-0141b9bf96e3/run/01a169fe-21fa-7ea2-a7ae-b5486fe81bd9?start_time=2026-10-23T18:20:24.954872Z) confirms the intermediate extracted truths omit the shop-error examples, reducing that policy to operator negligence/free reprint, while preserving customer-file wrong-size exclusions. The verdict then treats the supported shop-size claim as a contradiction. Thus lossy truth extraction plus origin conflation is observable in the scoring path; a raw Faithfulness mean between 95% and 100% is not automatically a more accurate or calibrated result.

The 87.50% case score and 98.75% mean remain recorded unchanged. This review identifies a calibration concern; it does not replace them with a favorable score.

### Case 10: binding and reference-scope differences

The historical case-10 CP score of 50.00% swaps the last two evidence positions in its reasons: actual rank 4 is Cromo, but its `yes` reason quotes OWV; actual rank 5 is OWV, but its `no` reason describes Cromo. The count is still five, so arithmetic/count checks do not detect the semantic binding failure.

The uniform rescore returns 95.00%, with `[yes, yes, yes, no, yes]`; the Cromo/OWV rank-4/rank-5 mapping now agrees with the actual passages. It nevertheless has a remaining reason error: rank 1 contains China vinyl and a trailing Ritrama heading, while its reason attributes Ritrama's no-residue property to that rank. That property appears in rank 2. A `yes` verdict at rank 1 can be defensible because the China passage explicitly supports outdoor storefront glass, but its stated supporting evidence is misbound.

In the tuned phase, the array is `[yes, no, yes, yes, yes]`, CP 80.42%. China, transparent vinyl, Ritrama and OWV are treated as useful; Cromo is not. These results also depend on the reference's scope: the reference names Ritrama/OWV, whereas China and transparent vinyl are real source-backed storefront-glass alternatives. Keep the reference fixed for the comparison; source-backed alternatives are a topic for independent reference calibration, not permission to rewrite it in favor of a generated answer.

### Other sensitivity

Case 8 CP changes from 80.56% historically to 100.00% on identical passages. Generic area/formula material is newly accepted as remotely useful, although only the official 35-piece table directly supplies the required kiss-cut quantity. The tuned official table is genuinely at rank 1, versus rank 3 before.

Uniform baseline Faithfulness marks all three case-8 claims borderline, including the 35-piece kiss-cut statement, while its final explanation says every claim is supported. Raw passage heading explicitly says `KISS CUTTING`; this is another warning that extracted-truth or judgement summaries can overlook source details. A final explanation is not a substitute for inspecting the complete claim/context evidence.

Exact dependency comparison also verifies that all questions, references and ordered passage texts are identical between `tuned` and `final` and between `knowledge_after` and `final-heldout`. Nevertheless CP case 10 changes 80.42% → 70.00%, held-out 06 changes 100.00% → 83.33%, and held-out 10 changes 100.00% → 75.00%. Contextual Precision does not use the actual answer, so these changes cannot be attributed to the information-first answer prompt or a different retrieval result. They demonstrate judge reclassification under repeated calls.

### Independent judge diagnostic, kept separate

The saved [`independent-judge-diagnostic.json`](../../data/evaluations/precision-study-2026-10-24/independent-judge-diagnostic.json) contains four CP assessments using `deepseek/deepseek-v4.1-flash`. These are calibration observations, not replacements for GLM scores or a second full benchmark.

| Case / passage set | Uniform GLM CP | Diagnostic DeepSeek CP | Main disagreement |
| --- | ---: | ---: | --- |
| 6 — saved ranking | 86.67% | 20.00% | DeepSeek rejects file-readiness and customer-error contrasts as support for the shop-error reference; GLM accepts them as remotely useful. |
| 6 — tuned ranking | 100.00% | 50.00% | Both find the actual shop policy at rank 2; DeepSeek rejects the customer-error passage at rank 1. |
| 10 — saved ranking | 95.00% | 86.67% | DeepSeek accepts China/Ritrama/OWV but rejects transparent vinyl and Cromo for the outdoor-specific reference. |
| 10 — tuned ranking | 80.42% | 100.00% | DeepSeek now accepts all five passages, including Cromo's negative contrast; GLM rejects Cromo. |

The independent judge confirms the actual shop-policy rank improves 5 → 2, while differing substantially on broad relevance. For case 10, the two judges give opposite directions of score change. That is not enough evidence to certify semantic precision or claim a stable causal effect from either judge alone.

## Ten-case source/answer inspection

| Case | Uniform CP → tuned CP | Evidence and answer finding |
| --- | ---: | --- |
| 1 — locations | 50.00% → 100.00% | Physical-address passage moves rank 2 → 1. Both answers still name branches and postpone the requested address. Perfect relevancy measures do not establish answer completeness. A later general information-versus-order-handoff prompt fix is a separate phase. |
| 2 — payment | 100.00% → 100.00% | New answer states the remainder conditionally if DP is 60%, avoiding the old unconditional 40% balance assumption. Minimum DP 60% is source-supported; legacy 50–60% reference conflict still produces CR 0.00%. No reference was changed to eliminate this score. |
| 3 — waterproof labels | 100.00% → 80.42% | New answer provides actual vinyl kiss-cut prices Rp17,500/Rp15,000 rather than incorrectly saying that tariff is unavailable in the knowledge. Some less directly useful passages now affect CP despite improved answer information. |
| 4 — files/JPEG | 100.00% → 100.00% | JPEG quality/300 DPI/CMYK and document-send requirements are source-supported. The answer remains long, listing formats and delivery advice beyond the direct question. This is a concision concern, not evidence of a wrong tariff. |
| 5 — area price | 63.89% → 100.00% | Relevant spanduk tariff/formula is ahead of unrelated display-package material. Rp33,000 standard and Rp50,000 HR per 2×1 m print match source arithmetic. |
| 6 — shop errors | 86.67% → 100.00% | Explicit free-reprint policy rank 5 → 2; customer-file exception remains distinct. Do not attribute the earlier historical 20.00% → uniform 86.67% jump to the ranker. |
| 7 — three banners | 100.00% → 100.00% | Rp99,000 standard and conditional Rp150,000 HR totals are correct. Explicit material/quality assumptions remain necessary. |
| 8 — capacity | 100.00% → 100.00% | Official kiss-cut table rank 3 → 1. New answer separately states manual cutting 54 and kiss cut 35; it does not replace the approved 35 with the generic 40 estimate. |
| 9 — mixed products | 100.00% → 86.67% | Rp100,000 reference-variant total is correct, but the business-card passage is only rank 5 after unrelated Y/Roll-Up packages. Answer says BC/lamination prices are not in the shop list: they are absent from the returned card chunk, but present in the complete original price source. Absence from retrieval is not absence from the full knowledge base. |
| 10 — outdoor glass | 95.00% → 80.42% | Answer adds unsupported broad claims that transparent vinyl is less suitable outdoors and Ritrama is the most durable. Source supports Cromo's non-waterproof paper property but does not establish the same negative conclusion for transparent vinyl. Faithfulness flags these as borderline and still returns 100.00%. |

## What the perfect answer metrics conceal

| Complete phase | Faithfulness yes / borderline / no | Answer Relevancy yes / borderline / no |
| --- | ---: | ---: |
| Uniform baseline | 51 / 18 / 1 | 70 / 18 / 1 |
| Tuned, original prompt | 58 / 13 / 0 | 72 / 10 / 0 |
| Held-out knowledge before | 42 / 20 / 0 | 57 / 12 / 0 |
| Held-out knowledge after | 53 / 13 / 0 | 53 / 18 / 2 |
| Information-first development | 61 / 20 / 0 | 73 / 17 / 2 |
| Information-first held-out | 43 / 15 / 0 | 55 / 15 / 2 |
| Latest grounding development | 66 / 13 / 1 | 76 / 18 / 0 |
| Latest grounding held-out | 50 / 11 / 0 | 56 / 17 / 0 |
| Final guard development | 60 / 16 / 0 | 73 / 20 / 3 |
| Final guard development-validation12 | 49 / 20 / 0 | 60 / 19 / 0 |
| Untouched final eight | 40 / 7 / 0 | 41 / 14 / 0 |

The current library configuration accepts borderline verdicts, including unsupported noncontradictory claims and tangential supporting information. Therefore the tuned 100.00% values are mathematically correct under that recipe, while the source review still finds missing requested information and unsupported generalizations. Lowering or capping those means to satisfy a desired open interval would corrupt the result; neither a perfect number nor a number just below it substitutes for calibration.

## Held-out knowledge-before observations

All twelve newly frozen questions have complete scores in the old namespace using the current ranking code, and all four means are 100.00%. This is not a pure reproduction of the earlier pre-reranker system. The recorded before/after namespaces separate the knowledge change; their runtime passage metadata must be considered when attributing effects.

The core source-backed outcomes are correct in the twelve before answers: Pamulang landmark, exact general contacts, named Ciputat address/Maps, Rp256,000 backdrop, Rp270,000 X-Banner packages, Rp30,000 frame-only, shop-error free reprint versus excluded blurry original customer file, both cancellation conditions, Cromo writing/non-waterproof limits, Ritrama no-residue choice, and OWV two-sided appearance.

There are still answer/calibration concerns despite perfect means:

- The blurry-file liability answer provides a long preventive DPI/file-delivery tutorial. The judge accepts five of those relevance decisions as borderline; it does not penalize the added burden on the user.
- The wrapping answer asserts China's adhesive is inferior and that it is best for surfaces not needing clean removal. The source gives Ritrama's no-residue property but does not establish the opposite for China. The judge flags this as borderline and still scores Faithfulness 100.00%.
- The OWV answer adds that the shop stays bright. The source supports outward visibility, not a lighting guarantee; inspect that extra claim separately from the correct core optical description.
- Correct cancellation advice keeps both time and pre-production conditions and routes actual status to staff. The judge sometimes marks reasonable procedural guidance unsupported because the retrieved context does not document the bot/admin capability boundary. That differs from fabricating the actual order status.

Perfect CP is also not a claim that every top-five context is relevant. Across the before sample there are **20 yes and 40 no** context verdicts, with CP 100.00%. The average-precision formula can be 1 when useful evidence precedes all irrelevant passages; an irrelevant tail after the last useful passage does not lower it. Do not relabel this as ordinary Precision@5.

## Held-out regressions and information-first outcomes

Both old/new namespace runs use current BGE reranking. The twelve source-grounded reference outcomes remain present in their paired answers. Recorded CP nevertheless decreases from 100.00% to 97.22%, and AR from 100.00% to 96.67%; those decreases must remain visible. In held-out 03, the new-knowledge answer gives the correct requested address but appends file-submission email/Google Drive/25 MB instructions. AR 60.00% penalizes those two unrelated statements. This is a concrete concision regression rather than failed location retrieval. In held-out 04 and 05, the core Rp256,000/Rp270,000 arithmetic remains correct while unrelated display-package contexts occur before supporting formula passages, producing CP 91.67% and 75.00%.

The information-first held-out answer in 03 removes the Drive instructions but retains an unrelated email offer; its AR is 75.00%. Held-out 11 has the correct Ritrama/no-residue recommendation and states that China's residue behavior is unspecified, improving the earlier unsupported opposite inference, but adds an irrelevant outdoor-large-sticker discussion (AR 90.00%). Correct core outcomes coexist with avoidable padding.

Information-first development case 9 still says BC and lamination tariffs are not available in the entire shop list. Their absence is only from the returned card passage; the full source lists them elsewhere. Faithfulness 100.00% is consequently not a certificate that the complete business answer is correct. The latest grounding phase was introduced on this development-case evidence; its saved answer removes that false global absence claim, as checked below.

The frozen held-out questions have now been exposed repeatedly across prompt phases. They remain useful regression evidence, but they are no longer a pristine unseen test for subsequent optimization. A later optimization round requires a fresh independently reviewed held-out sample. None of the twelve references was rewritten to favor these answers.

## Latest grounding: dependency and factual verification

All ten development and twelve held-out latest-grounding answers were inspected. An offline comparison independently verified that every question, reference and ordered passage text exactly matches its recorded source case (`final` or `final-heldout`), and that retained CP/CR scores and calculation traces are unchanged. The installed Contextual Precision/Recall required parameters are input, expected output and retrieval context; they do not include `actual_output`. Retaining their results for identical dependencies avoids interpreting repeated-judge noise as retrieval change.

The latest twenty-two cases have **44 fresh answer-metric scores and 44 retained retrieval-metric scores**, totaling 88/88 available scores with no answer/metric errors. The export records `retained_from` for those retrieval metrics. Availability means the operation produced a recorded numeric result; it does not independently validate the judge's semantic decisions. The hold-out file remains unchanged at SHA-256 `6f60628bdc39976372a5ac12e0c0c532cb39a8660f0acd5c3654cfc6b383d386`.

The last development answer 9 is now a concise Rp100,000 Art Carton/X-Banner estimate with explicit components and an ordinary final-price confirmation caveat. It no longer claims BC/lamination prices are absent from the whole knowledge base. Answer 10 now gives source-supported Ritrama, China and OWV options and Cromo's actual non-waterproof limitation; it no longer rejects transparent vinyl or claims Ritrama is categorically the most durable. These are concrete source-alignment improvements, independent of the perfect answer-metric values.

Residual concerns remain visible:

- Latest development case 6 Faithfulness is 85.71%, producing a 98.57% mean. Its single `no` again conflates customer-file wrong size with shop production wrong size and says the production-error examples are absent. The actual rank-2 passage explicitly lists shop/production origin, wrong size, wrong material, machine defect and severe banding. This appears to be the same scoring-path calibration failure observed in the uniform baseline, not proof that the new answer is factually less grounded. The raw score is preserved.
- Latest held-out 03 now answers the named branch address/landmark/Maps without the unrelated email/file-submission instructions. That resolves the concrete padding regression seen in earlier phases.
- Latest held-out 11 correctly chooses Ritrama and says China's residue behavior is unspecified, but adds **“jadi cat mobil tetap aman.”** No-residue removal does not by itself establish an unconditional paint-safety assurance. The source does not make that broader guarantee, yet the judge accepts the combined claim as `yes`. It is a residual answer-quality/calibration limitation, not a basis to fabricate a lower metric.
- The blurry-file liability answer remains lengthy, with preventive DPI and delivery guidance accepted as supporting information. Some conversational padding and reasonable procedural statements still receive borderline decisions while passing under the established rubric.

### Latest development scores

| Case | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision |
| --- | ---: | ---: | ---: | ---: |
| 1 | 100.00% | 100.00% | 66.67% | 100.00% |
| 2 | 100.00% | 100.00% | 0.00% | 100.00% |
| 3 | 100.00% | 100.00% | 100.00% | 80.42% |
| 4 | 100.00% | 100.00% | 100.00% | 100.00% |
| 5 | 100.00% | 100.00% | 100.00% | 100.00% |
| 6 | 85.71% | 100.00% | 100.00% | 100.00% |
| 7 | 100.00% | 100.00% | 100.00% | 100.00% |
| 8 | 100.00% | 100.00% | 100.00% | 100.00% |
| 9 | 100.00% | 100.00% | 100.00% | 86.67% |
| 10 | 100.00% | 100.00% | 100.00% | 70.00% |

All twelve latest held-out F/AR/CR scores are 100.00%. Their CP scores by ID suffix are `01:100.00, 02:100.00, 03:100.00, 04:91.67, 05:75.00, 06:83.33, 07:100.00, 08:100.00, 09:100.00, 10:75.00, 11:100.00, 12:100.00` percent. The 93.75% mean therefore still includes real ranking weaknesses in several cases. It must not erase the before/after held-out decrease or be represented as a uniformly improved sample.

## Grounding-phase assessment, before the final property guard

The latest recorded development CP is **93.71%**, +4.15 percentage points versus the uniform baseline's 89.56%, and recall remains **86.67%**. Held-out CP is **93.75%**, above 87% but below the old-knowledge held-out result of 100.00%. These are bounded experimental observations with the judge-variance and sample limitations described above, not guarantees of production accuracy or a stable lower bound on true contextual precision.

The requested **greater-than-95% and less-than-100% Answer Relevancy aim remains unmet**: the latest recorded means are 100.00% for both development and held-out answers. Held-out Faithfulness is also 100.00%. Development Faithfulness is 98.57%, numerically within that interval, but its only negative decision appears to be a false contradiction and therefore cannot be celebrated as successful calibration. No cap, penalty, threshold change, fabricated mistake or reference rewrite was used to force those values below 100%.

This study improves observable evidence ordering and several concrete answers while exposing unresolved judge and answer-quality limitations. Independent human business review and a new unseen validation sample remain necessary before making broad reliability claims. The four official scores and all unfavorable historical/intermediate results remain intact.

## Final property-inference guard and current application

The final protected prompt hash is `ae0161f05d799c7d06aaf53ec32d2a95e3130487930924be50239d3663ea9914`. Its general rule prevents turning one documented material property into an unsupported safety/freedom-from-damage guarantee about a customer's object. It applies across materials and surfaces rather than recognizing a benchmark question.

All `verified-main` and `verified-heldout` saved answers were inspected. All twenty-two cases again have exact question/reference/ordered-passage matches to their reuse sources, with **44 fresh answer metrics and 44 explicitly retained retrieval metrics**, no answer/metric errors, and unchanged CP/CR scores/calculation traces. No numerical score was altered by this review.

The current development means are **Faithfulness 100.00%, Answer Relevancy 98.00%, Contextual Recall 86.67%, Contextual Precision 93.71%**. The original twelve development-validation cases have **100.00%, 100.00%, 100.00%, 93.75%** respectively. Their targets must be interpreted using the actual latest phase, rather than selecting a more favorable earlier mean.

The earlier observed paint-safety overclaim is resolved in saved validation answer 11. It now states the supported no-residue property and explicitly distinguishes that from a guarantee that paint will remain safe after installation/removal. It also says China's residue behavior is unspecified instead of assuming a negative property. Development answer 9 keeps its correct conditional Art Carton/X-Banner estimate without the false whole-list BC/lamination absence claim, and answer 1 immediately supplies both real branch addresses/Maps. Those are observable answer improvements.

There is a new calibration limitation behind the development AR mean of 98.00%. All three `no` verdicts occur in case 10 and are the extracted single words **“Promosi,” “Terlihat,” and “Dekorasi.”** In the actual answer, those words occur inside coherent sentences; they are not independent disconnected outputs. The installed statement-extraction instruction allows single words only if they are outside a coherent statement. The extractor therefore appears to create penalized fragments that do not represent the answer's actual statement structure. The raw case AR 80.00% and aggregate 98.00% remain unchanged, but reaching the requested numerical interval this way is not proof of successful calibration.

The **Faithfulness below-100% aim remains unmet in the current phase**: both development and original validation means are exactly 100.00%, with 16 and 20 borderline verdicts respectively. Development AR is numerically within the requested greater-than-95%/less-than-100% interval, subject to the fragment-extraction concern above; the original validation AR is still 100.00%. Earlier false-negative Faithfulness decisions were not introduced or retained just to bring the current mean below 100%.

Some limitations remain despite the fixes. Development answer 2 again states a 40% remaining balance after describing a **minimum** 60% DP, without explicitly conditioning the remainder on the amount actually paid. That is an assumption needing confirmation, not an independently verified universal balance rule. Long preventive file advice and extra order follow-ups remain accepted as borderline supporting information. Perfect Faithfulness/AR under this recipe should not be represented as flawless business communication.

The original twelve cases informed a later guard, so their final scores are regression evidence. Only the separate eight-case file frozen after this prompt can serve as the final previously unobserved check. Its questions/references were generated and frozen before its application outputs existed; it must be evaluated once without another tuning cycle on those results.

## Final previously unobserved eight-case check

The terminal saved result is [`untouched-final/results.json`](../../data/evaluations/precision-study-2026-10-24/untouched-final/results.json). Its manifest uses final prompt hash `ae0161f05d799c7d06aaf53ec32d2a95e3130487930924be50239d3663ea9914`, answering model `anthropic/claude-haiku-5.5`, intent model `openai/gpt-4.1`, judge `z-ai/glm-5.3-flash`, top-k 5, and new snapshot `kb-0a4b41713f9e423799b20387bda6597b`. The application was not tuned again after observing this sample.

All eight saved questions/references exactly match the frozen dataset; its SHA-256 remains `0741633ac4777163f5611e4843a786299f9ec8391e37c2ddced5c63f45751965`. All **32 metric scores are fresh**, with no `retained_from`, answer errors or metric errors. Each answer and its item-level judge evidence were inspected against the source excerpts. This review made no changes to the dataset, outputs or scores.

| Final ID suffix | Core answer/evidence finding | F | AR | CR | CP |
| --- | --- | ---: | ---: | ---: | ---: |
| 01 | Correct Ciputat file-submission email; extra subject/Drive/WhatsApp instructions are accepted as borderline supporting information. | 100.00% | 100.00% | 100.00% | 100.00% |
| 02 | Exact Pamulang physical address, MTsN landmark and source Maps URL; general admin numbers remain unassigned to a branch. | 100.00% | 100.00% | 100.00% | 100.00% |
| 03 | Correct two-package X-Banner340 estimate: 2 × Rp70,000 = Rp140,000, including frame. | 100.00% | 100.00% | 100.00% | 100.00% |
| 04 | Correct 3×1.5 m HR280 area calculation: 4.5 × Rp25,000 = Rp112,500. Other-material and Y-Banner contexts add ranking noise. | 100.00% | 100.00% | 100.00% | 91.67% |
| 05 | Correctly excludes customer-file typo and permits free reprint for shop-originated wrong material with physical proof. | 100.00% | 100.00% | 100.00% | 100.00% |
| 06 | Correct BCA-transfer/one-working-day/no-cash refund policy, without claiming a refund has actually been processed. | 100.00% | 100.00% | 100.00% | 100.00% |
| 07 | Correct 300 DPI, CMYK and Quality10–12/Maximum JPEG requirements. The only recall rejection is the reference's greeting, discussed below. | 100.00% | 100.00% | 75.00% | 100.00% |
| 08 | Correct source-listed Ritrama no-residue/material properties. It does not extrapolate to paint safety or a damage-free removal guarantee. | 100.00% | 100.00% | 100.00% | 100.00% |

The final JPEG CR result deserves explicit interpretation. The judge counts **four** reference statements: the greeting **“Halo!”**, 300 DPI, CMYK and Quality10–12/Maximum. It rejects only the greeting because it does not occur in the source. Rank 1 actually contains all three technical requirements, and the judge marks all three attributable. Thus raw case CR 75.00% and mean CR 96.875% reflect a harmless reference greeting being included in the metric denominator, not missing JPEG technical evidence. The reference and official scores remain unchanged; removing the greeting after seeing its effect would invalidate the frozen final comparison.

Other calibration limitations persist. In final case 02, the Faithfulness reason says the Maps URL is absent from context, although the exact source URL is supplied in the relevant branch information. It is accepted as borderline, so the metric remains perfect. In case 04, calling the company's estimate list a shop list is also marked borderline. These examples reinforce that semantic verdicts can overlook evidence or distinguish wording unhelpfully even when arithmetic is correct.

The final eight have 17 relevant and 23 irrelevant context verdicts across forty returned passages, while CP averages 98.96%; this is average precision by rank, not unweighted Precision@5. Their Faithfulness/AR remain 100.00% because all 7/14 borderline items are accepted. The requested below-100% target is therefore **unmet for both answer metrics on the final unseen sample**. No cap or manufactured mistake was used to change that outcome.

## Final interpretation

The current recorded development CP of **93.71%** and final eight-case CP of **98.96%** exceed the 87% optimization target. Development recall is preserved at **86.67%**, and final-sample recall is **96.88%** under the frozen recipe. These are useful local experimental outcomes, alongside concrete improvements in evidence order and answer specificity, not a population accuracy guarantee or a lower confidence bound on production contextual precision.

Preserve the historical 76.44% figure, the uniform baseline 89.56%, development-validation regressions, judge failures and the final raw result. Their different evidence/protocol/sample boundaries are essential to interpreting the apparent gains. Independent human review of the semantic labels, reference hygiene before a new freeze, and a larger new representative validation sample are the next research steps; the existing references and scores should not be adjusted to manufacture a preferred percentage.
