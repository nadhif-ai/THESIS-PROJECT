# Faithfulness follow-up, 24 October 2026

## Question and baseline

The user requested an exact explanation of the changes that raised evaluation scores, disclosure of Knowledge source edits, and Faithfulness above 95% while retaining useful answers. Baseline complete run `49b97b79220e4d60ad9696c75e44bc37` records F 88.00%, AR 96.67%, CR 100.00%, CP 89.83%, ten fresh cases, forty valid scores and forty feedback records. Its raw results remain unchanged.

The [knowledge content audit](../research/2026-10-24-knowledge-change-audit.md) answers the source-edit question separately. Earlier source 04/06 cleanup removed conflicting capacity estimates and additional technical descriptions; the source 01 reorganization alone has a proven full fact-conservation ledger. The initial follow-up run made **no further knowledge change through its scoring freeze**. The user subsequently confirmed all three removed cutting-process facts, and their restoration occurred after that cutoff. The later restoration and final comparison are recorded separately below.

## Diagnosis

Independent source/trace inspection identifies three baseline Faithfulness NO verdicts:

- Case 3, F 0.8: source facts connect Vinyl Meteran China 200 GSM with its China 200 GSM High Resolution tariff. Intermediate truth extraction drops part of the identity, and the answer also omits the 200 GSM qualification. The verdict treats these as different products.
- Case 5, F 0.5: the rejection reason explicitly computes 2 m² × Rp16,500/m² = Rp33,000 and says the rejected claim matches the source. The answer nevertheless uses an unscoped cheapest-option phrase and omits the unit rate.
- Case 7, F 0.5: extracted truths already include the HR rate Rp25,000/m² and the area/quantity formula. The verdict incorrectly says the context only supplies a standard rate. The answer combines both quality totals without a separate unit-rate calculation for each.

The installed DeepEval 4.2.8 rubric reserves NO for direct contradiction and uses BORDERLINE for unsupported, noncontradictory claims. The original rubrics, accepted verdict policy, thresholds and saved NO scores remain intact. An 88% macro mean is not proof of 12% factual hallucination, and the requested 95% is not a calibrated probability of correctness. The [official Faithfulness definition](https://deepeval.com/docs/metrics-faithfulness) and [official implementation](https://github.com/confident-ai/deepeval/blob/main/deepeval/metrics/faithfulness/faithfulness.py) were checked with Exa/Context7 alongside the installed code and actual LangSmith calls.

## Initial follow-up: single changed variable

For the initial follow-up, only shared answer instructions in `app/backend/prompt_template.py` changed:

- Use the tariff-row variant name and price-determining qualifications, rather than replacing them with a broader material alias.
- Avoid unscoped cheapest/most-economical claims without a supported comparison.
- Explain customer-readable area/quantity × unit rate = total separately for each option, including any price rounding.

During that initial freeze, no business number, benchmark example, expected answer, judge instruction, model, retrieval rule, dataset or threshold was introduced or changed. The configurable conversation instructions remained identical to the baseline. These rules improve customer auditability; they do not guarantee the judge will obey its rubric.

## Initial frozen execution protocol

Fresh run **`c221a7fcedb84ee28ba87d3366ca3603`** was submitted once at **24 October 2026, 10:42:06 Asia/Jakarta** using the existing durable evaluation submission service, the same service called by the authenticated administration endpoint. This operator invocation did not create or extend an admin session. Normal leases, checkpoints and reporting applied; the job appears in administration history. It regenerated ten answers and all forty scores, without scoring-only retries or best-run selection.

- Answering: `openai/gpt-6-luna`; intent: `z-ai/glm-5.3-flash`; scoring: `deepseek/deepseek-v4.1-flash`.
- Judge: reasoning `none`, temperature 0, budgets 4096/8192 tokens, original threshold 0.7 and metric definitions.
- Knowledge: unchanged published revision 16, namespace `kb-e622863bb58d4137b4e8bf7cf62a186e`, 141 passages, no pending source change.
- Retrieval/embedding: unchanged top-k 5, Nemotron 2048/cosine, sections-v2, chunk size 1000/overlap 100.
- New answer prompt SHA256: `96c9c3e96e122e30e1922f90304d9ceb5fddff62322a673142a04c681a520437`.
- All fourteen tracked source hashes match the preceding freeze except `app/backend/prompt_template.py`; all configuration/source/intent settings and ten references match exactly.

The complete offline suite passed **326 tests, 11 expected paid/review-gated skips, 2 existing deprecation warnings in 57.25 seconds**. An initial targeted run encountered a missing disposable PostgreSQL service (8 passed, 1 setup error); after starting loopback PostgreSQL 17, the complete suite passed. The disposable test container was stopped afterward. No test used the hosted administration database. No frontend source changed in this follow-up, so the previous UI verification is unchanged.

## First complete follow-up: preserved outcome

Job `c221a7fcedb84ee28ba87d3366ca3603` completed with **F 95.00%, AR 98.75%, CR 76.67%, CP 88.71%**, ten cases, forty valid scores, forty feedback records and zero execution/scoring errors. Thirty-five of forty scores pass the original 0.7 threshold. Strict F > 95% and CR > 85% are **not met** by this run.

All ten question/reference/ordered-context arrays are byte-identical to the baseline run. Recall drops in cases 2, 5, 7 and 9 therefore do not indicate a changed retrieval set: the DP reference conflicts with the minimum 60% policy; other verdicts reject correct derived totals or confuse the customer's dimensions with an illustrative source example. Precision changes in cases 3 and 4 are also judge variation on identical inputs. These official raw scores remain unchanged.

Faithfulness contains 27 YES, 9 BORDERLINE and 2 NO verdicts. Both tariff claims in case 7 now pass, while the judge shifts its rejection to the correct 2 × 1 × 3 = 6 m² statement. Case 3 retains its source-backed alias rejection despite the repaired 200 GSM qualification. Claim segmentation and verdict variation contribute to the mean movement; it is not seven percentage points of independently established factual improvement.

Case 6 exposes a genuine wording risk despite F 1: the answer categorically excludes refunds when the returned policy only promises free reprint. The judge extracts and marks this BORDERLINE; the original accepted-BORDERLINE policy still counts it. A high Faithfulness ratio alone cannot certify safe business wording.

The complete scoring postflight at **24 October 2026, 10:55:03 Asia/Jakarta** verifies the original source/configuration/prompt/runtime freeze for all forty scores. Later operations below occurred only after that cutoff; remaining static feedback reporting completed without changing results. The separate independent audit preserves every score, actual model/prompt/history check and remaining disagreement.

## Source restoration and calibrated judge diagnostic

The user confirmed all three removed process facts: 29 × 42 cm effective machine area, 1–2 cm sensor/registration allowance, and half-cut/backing-intact definition. They were restored in source 06; source 02's stale cross-reference was corrected. All 42 manual size/count pairs, tariffs, other source text and official source 03 Kiss Cut capacities remain unchanged. Normal private replacement and verified atomic Sync activated **revision 18, 142 passages, `kb-84668f0b823a402cbe360c2c711bd766` at 11:01:49 Asia/Jakarta**. Old namespaces remain available. See the [restoration ledger](../../dataset/knowledge-revisions/2026-10-24-restoration/provenance.json).

Before additional benchmark scoring, nine controls and expected label classes were frozen. Seven use exact extracted truths and controlled claims for material aliases, correct/incorrect area pricing, warranty and an unsupported refund exclusion; two use fixed contexts for correct derived pricing and a contradictory unit tariff. These are source/arithmetic-checked development diagnostics, not independent human labels or a held-out dataset.

The same DeepSeek model, temperature, installed rubrics, messages and schemas were tested with existing reasoning `none`/4096-token budget and candidate reasoning `low`/16384-token budget. **Existing: 6/9 expected label classes; candidate: 9/9.** All three direct-contradiction negative controls remain NO in both configurations. Low repairs the alias, customer-area and unsupported-borderline distinctions in these controls. Both variants pass the two Recall controls, so this does not establish a Recall-specific improvement. Reasoning effort and budget change together; no isolated causal claim is made.

The first four Recall attempts failed locally before any provider call because the diagnostic omitted installed template interpolation fields. A separate correction uses the exact installed prompt builder and original frozen inputs; no Faithfulness control was repeated. All original failures and 18 valid unique control/configuration calls remain recorded. Independent LangSmith inspection verifies the actual requests and corrected harness boundary.

The selected judge now uses reasoning `low` with 16384 tokens and a fixed 32768-token truncation retry. Existing rubrics, accepted verdict policy, model identities, thresholds, temperature and formulas remain unchanged. Budget exhaustion still produces an unavailable score. Twelve adapter tests verify forwarding, fixed retry budgets and failure behavior. The original 4096/8192 reasoning `low` baseline had exhausted its budget before visible JSON, which is why simply reenabling reasoning without more headroom was unsuitable.

A separate generic application rule now prohibits inferring a policy exclusion from a source that merely offers one option. This addresses case 6's real unsupported refund inference; improving rubric adherence alone would still count that BORDERLINE as accepted.

## Final frozen execution and uniform baseline

Fresh complete job **`dfffee3891ae415e91343abae6729ffb`** was submitted once at **24 October 2026, 11:05:24 Asia/Jakarta** after restoration, calibration review, backend restart and a final offline suite: **326 passed, 11 expected skips, 2 existing warnings, 55.31 seconds**. The disposable loopback PostgreSQL 17 container was stopped after testing. The new answer prompt is `ff64c89b909786d0d7a76d2926b33cfcdbf02721cd7eb025bb991525d347337a`.

It regenerates all ten answers and forty metrics with unchanged Luna/DeepSeek/GLM model identities, top-k 5, Nemotron 2048/cosine, 1000/100 sections-v2 and legacy questions/references. The intended changes are the user-confirmed restored knowledge, generic answer policy guard and calibrated judge configuration. Their combined effect is not an isolated generator or retrieval experiment. All fifteen runtime/test hashes, knowledge references, prompts and settings are frozen in `final-preflight.json`.

For comparison, **all forty baseline metrics** were freshly scored under this same calibrated judge in a separate LangSmith project, completing at **24 October 2026, 11:17:43 Asia/Jakarta**. Its original answers, references, full ordered context records and original metrics match run `49b97b79220e4d60ad9696c75e44bc37` exactly; no answers were regenerated, no retrieval occurred and no historical administration record was overwritten. This uniform baseline measures scoring-setting effects and judge variation on unchanged application outputs; it is not a failed-only retry or best-run selection.

| Recorded outcome | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision |
| --- | ---: | ---: | ---: | ---: |
| Original run49, original judge settings | 88.00% | 96.67% | 100.00% | 89.83% |
| Same run49 answers/evidence, calibrated judge | 98.00% | 98.89% | 86.67% | 85.71% |

All forty uniformly rescored metrics are available with zero errors, and their ratios, ranked contributions and macro means reproduce from recorded verdicts. This shows why the historical Faithfulness increase cannot all be attributed to application improvements. The correct material alias and banner calculations now pass without changing those old answers. However, the judge remains semantically brittle: case 6 receives F 0.8 because it treats an umbrella heading naming refund as contradicting an answer about the specific reprint remedy; case 9's correct derived combined total still receives only 2/3 Recall. Matching nine diagnostic controls does not validate every business judgment. The [uniform baseline traces](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/70923a31-3168-4e82-9a62-9a33df78b8bc) preserve all calls.

## Final recorded scores and interpretation

All ten fresh answers and forty metric scores are recorded with zero scoring errors:

| Outcome | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision |
| --- | ---: | ---: | ---: | ---: |
| Original run49, previous judge settings | 88.00% | 96.67% | 100.00% | 89.83% |
| First complete c221 follow-up, previous judge settings | 95.00% | 98.75% | 76.67% | 88.71% |
| Original run49 answers, uniformly calibrated judge | 98.00% | 98.89% | 86.67% | 85.71% |
| Fresh final dff run, calibrated judge | **95.28%** | **97.50%** | **90.00%** | **88.72%** |

The unrounded recorded final Faithfulness mean is 0.9527777777777778, strictly above 0.95 without rounding or clipping; Recall > 0.85 and Precision > 0.87 are also met on these ten development questions. This is not evidence that all metrics improved under a uniform judge: final Faithfulness and Answer Relevancy are lower than the uniformly rescored old answers. The historical 88% to 95.28% change combines application changes, judge configuration and judgment variation.

Final Faithfulness has 45 YES, 6 BORDERLINE and 3 NO item verdicts. Its unchanged default policy accepts YES and BORDERLINE. The case-level sample standard error is 3.15 percentage points across ten development cases; no normal 95% interval or calibrated customer-correctness probability is claimed. The margin above the requested 95% threshold is small, and repeated judge variation remains observable.

Compared with the uniform baseline, all 3.33 percentage points of Recall movement come from case 9: the exact same question, reference and all five ordered context texts receive 2/3 versus 1 under identical judge settings. Recall does not use the generated answer; this is residual judge variation, not an answer-format or retrieval gain. The DP case remains zero because the unchanged reference says 50–60% and the authoritative source requires minimum 60%.

Precision movement is concentrated in case 8 (0.7 to 1) plus a small case-3 change (0.8041667 to 0.8055556). Case 8's official 35-piece Kiss Cut table was already rank 1 in the old run and remains rank 1. Restoration changes secondary context, including the direct manual table now at rank 4. This supports the answer's explicit 35-piece Kiss Cut/54-piece manual distinction, but does not establish recovery of a missing official table or an isolated ranking improvement. Both cases have changed context and new relevance verdicts.

Independent actual-answer inspection finds the following material details:

- Case 3 retains the correct Vinyl Meteran China 200 GSM High Resolution Rp45,000/m² scope. Its food-contact caution is BORDERLINE for Faithfulness and rejected as irrelevant by Answer Relevancy, which falls to 0.75. F 1 is not proof of direct support for every sentence.
- Cases 5 and 7 separately name standard/High Resolution tariffs and show the correct customer-readable area × rate calculations. Case 7's total area is 6 m², with Rp99,000 standard and Rp150,000 High Resolution; all four metric scores are 1.
- Case 6 replaces the categorical refund exclusion with the source-backed free-reprint remedy, physical-proof requirement and customer-file-error distinction. The remaining statement, “Informasi soal retur uang belum tersedia,” lacks explicit scope to the information available for this store-error case. Meanwhile the judge infers refund information from an umbrella heading, rather than a refund-term body. This is a mixed answer-scope/judge-evidence issue; the raw F 0.75 remains. It is not a new incorrect reprint policy or purely a judge defect.
- Case 8 explicitly distinguishes 35 Kiss Cut pieces from 54 manual-cut pieces per A3+ for 5×5 cm. Both are supported by returned evidence; all four scores are 1.
- Case 9 explicitly assumes Art Carton one-side cards and the standard 60×160 cm X-Banner package including frame. Subtotals are Rp50,000 + Rp50,000 = Rp100,000, followed by confirmation of the material assumption. No stock, booking or payment completion is asserted.
- Case 10's actual answer names Vinyl Meteran China (200 GSM) and Ritrama (250 GSM). Its claim extractor rewrites these as product “sizes”; the verdict stage then rejects them because GSM is weight rather than dimensions. Actual Luna text never calls GSM a dimension, and extracted source truths correctly describe the weights. Both NO verdicts and F 7/9 remain unchanged; no factual material-number error was found.

Actual LangSmith inspection confirms ten Luna answers and ten GLM intents, all twenty prompts with one Human message and zero AI history, exact frozen answer/intent systems, ten complete intent JSON outputs, stop finishes, no guards or trace errors, and every saved answer identical to its Luna generation. All fifty generation/metric roots are complete. Eight sampled case-6/case-10 judge requests confirm DeepSeek, reasoning `low`, 16384-token budget and stop finishes.

The job reached terminal **completed at 24 October 2026, 11:33:44 Asia/Jakarta**, with ten answers, forty valid scores, **40/40 reported feedback records**, zero execution/scoring/reporting errors and **38/40** original-threshold passes. The result's `completed_at` field is the earlier scoring-completion time, **11:27:57**, rather than the end of reporting. The [completed LangSmith experiment](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/8636d888-27ca-486a-83a6-e7b7269569c5) retains the real generated answers and metrics.

Final postflight verifies that all fifteen tracked runtime/test hashes, configuration, source references, active revision 18/142 passages, prompt and judge settings exactly match the final preflight, with no pending Knowledge revision. The ten original questions/references remain unchanged. All 160 recorded scores across the four outcomes above reproduce from verdict counts or ranked contributions, including their thresholds, accepted policies and macro means. Independent auditing also verifies exact preservation of the historical administration result.

The durable [comparison bundle](../../testing/comparisons/2026-10-24-faithfulness-follow-up.json) includes complete raw results for every outcome, per-case changes, both independent audits, preflight/postflight freezes, all diagnostic controls and original harness failures, source restoration/activation evidence, and evidence SHA-256 hashes. The credential-pattern scan passed. Detailed local worker logs remain in `data/evaluations/faithfulness-follow-up-2026-10-24/`; they are not needed to reconstruct the bundled score arithmetic.

No commit, merge, deployment, customer WhatsApp send or production-delivery verification is claimed. Knowledge restoration is active in the administration store; these runtime code changes have only been verified locally. No frontend source changed during this follow-up; prior UI verification does not constitute a fresh visual inspection of this final run.
