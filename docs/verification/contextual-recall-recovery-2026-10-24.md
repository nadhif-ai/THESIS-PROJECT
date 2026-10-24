# Contextual Recall recovery verification — 24 October 2026

Final verification run **49b97b79220e4d60ad9696c75e44bc37 completed** with ten fresh answers, forty valid scores and forty reported feedback records. **Contextual Recall is 100.00%, exceeding the requested 85% target; Contextual Precision is 89.83%.** Independent LangSmith review confirms all ten intent outputs are valid and every saved answer matches its actual Luna generation. The complete preceding OSS run is preserved, including its erased address answer.

## Recorded comparisons

| Run | Faithfulness | Answer Relevancy | Contextual Recall | Contextual Precision | Score coverage |
| --- | ---: | ---: | ---: | ---: | --- |
| Screenshot: `49a80377` | 100.00% | 97.78% | 76.67% | 91.10% | 40/40 |
| Fresh current-model baseline: `1bc29255` | 97.78% | 78.89% | 83.33% | 83.10% | 39/40; one Faithfulness unavailable |
| Complete isolated OSS run: `69e57033` | 92.50% | 90.00% | 100.00% | 87.26% | 40/40, zero scoring errors |
| Final GLM-intent verification: `49b97b79` | 88.00% | 96.67% | 100.00% | 89.83% | 40/40, zero scoring errors |

The screenshot used Haiku answering, GLM scoring, GPT-4.1 intent and the old 139-passage namespace. The fresh baseline used Luna/DeepSeek/GPT-OSS on the preceding 142-passage snapshot. The complete isolated OSS run used the new 141-passage snapshot, corrected answer handling, explicit empty single-turn history and DeepSeek reasoning `none`; all forty scores and feedback records reached terminal completion.

The final run keeps Luna answering, DeepSeek scoring, top-k five, the 141-passage snapshot, references and metric definitions. It changes intent to GLM 5.3 Flash after observed GPT-OSS structured-output failures, clarifies intent-resolution semantics, and asks answers to preserve source tariff qualifiers. These are combined interventions; average-score differences do not isolate one change.

## Diagnosis and changes

The old location result retrieved addresses without reference opening hours. Both facts existed in the source but were split; hours were dropped during reranking. The old waterproof-label result similarly omitted the square-metre Ritrama tariff after reranking, despite its presence among initial candidates. The preceding source-heading correction recovered that tariff. The legacy DP reference says 50–60%, while source policy requires a minimum of 60%; neither was changed to force agreement.

SOP 01 was reorganized into one 981-character customer-visit passage containing both complete addresses, maps, landmarks, customer schedules and order cutoffs. All business facts, contacts, staff shifts and the remainder of the SOP are conserved. Authenticated Replace/Sync activated revision 16, **`kb-e622863bb58d4137b4e8bf7cf62a186e`**, with **141 verified passages**; the preceding namespace remains available. Nemotron/OpenRouter, 2,048 dimensions, cosine, sections-v2 and chunk size/overlap 1000/100 remain unchanged. The [source conservation ledger](../../dataset/knowledge-revisions/2026-10-24-recall/provenance.json) and [splitter proof](../../dataset/knowledge-revisions/2026-10-24-recall/chunking-proof.json) retain the exact evidence.

Three retrieval-only depth probes retained the baseline five nodes at depth eight but still missed the needed hours/business-card rate and introduced unrelated nodes. Global top-k therefore remains five. No business price, benchmark example, expected answer, threshold or metric formula was injected into knowledge.

Model-supplied intent `failed` no longer enters the application-failure path on an ordinary nonvisual question; the provider schema reserves that state for real exceptions. Real parser/transport failures retain conservative attachment validation. Structured requests have cancellable whole-call limits of 20 seconds for intent and 15 seconds for attachment validation, with owned-client cleanup. A real HTTP-200 trickle test proves a provider cannot evade the limit by periodically sending bytes.

Single-turn evaluation calls explicitly pass empty history. A retry can retain its conversation audit without feeding its uncheckpointed answer into the next attempt. Conversational evaluations still pass their actual saved pairs. The shared customer RAG pipeline is unchanged by this evaluation-caller isolation.

The answer prompt preserves material, quality, finishing, side, unit and quantity qualifiers that determine a tariff, and separates per-product subtotals from a combined total. The intent prompt defines resolution as interpretation rather than price/stock/asset availability. These rules contain no business numbers or reference answers.

## Preserved unsuccessful attempts and provider evidence

Diagnostic job `14794b30c97d4f63a4a39bbe6687b05b` first exceeded its lease waiting for GPT-OSS. It requested 4,096 completion tokens but reported 32,782, returned malformed data after 316.654 seconds, and failed nine schema checks. Its expired-lease answer checkpoint was rejected. After a normal Resume, a prior uncheckpointed answer contaminated case 1's history. The job was explicitly stopped with **two cases/eight scores preserved**, including favorable case-1 scores; these are excluded from the isolated comparison, with the reason visible in history. No answers or scores were deleted or replaced.

The complete isolated OSS run `69e570332b4d4f3f83db7c06ae292dcd` has exactly ten answer roots and forty metric roots, no duplicates or unfinished roots, and no history contamination. GPT-OSS returned valid intent JSON in 8/10 cases; cases 1 and 7 returned empty visible content with `finish_reason=stop`. Case 1's guard also returned empty output and erased a correct address answer. Case 7's guard succeeded and retained the correct Rp99,000 standard/Rp150,000 HR quote. No whole-call timeout occurred in that complete run. A separate bounded native-wire GPT-OSS probe timed out, so the failure is not established as merely a LangChain parsing defect.

GLM was selected for structured-output compatibility, not for giving more favorable evaluation judgments. Its initial operational probes exposed loose resolution semantics; the generic interpretation definitions corrected the observed address/banner/roll-up examples in one subsequent pass, with validated JSON in approximately 1.8–3.0 seconds. These small development probes are not a reliability estimate or an end-to-end image-delivery test. All probe outcomes, including earlier false ambiguity and the native-wire timeout, are preserved.

## Metric interpretation and remaining limits

The original DeepEval rubrics, threshold 0.7, temperature zero, score arithmetic and accepted verdict policy remain intact. DeepSeek reasoning changed from `low` to its supported `none` because the baseline exhausted 4,096 and 8,192 tokens in reasoning without returning visible JSON for one metric. That change is disclosed and affects comparability even though the rubrics are unchanged.

In the complete OSS run, cases 2 and 9 had the same question, reference and ordered retrieved texts as the fresh baseline, while their Recall changed from zero and 2/3 to one. Those gains are judge-setting/verdict variation, not repaired retrieval. Case 1's newly returned address/hour passage is a real coverage improvement. Contextual Recall does not use the generated answer; clearer subtotal wording cannot itself explain a Recall increase.

Final raw Faithfulness is 88.00%, lower than the preceding results. Three rejected claims remain visible: case 3's vinyl/China material alias, case 5's Rp33,000 standard banner total, and case 7's Rp150,000 HR banner total. Source inspection supports the material link and both area calculations; case 5's own rejection reason explicitly acknowledges the calculation is correct. The earlier omitted HR qualifier is now present in the actual case-3 answer. No rejected verdict was converted to accepted and no score was corrected manually. Case 4 Answer Relevancy is 2/3 because the judge rejects the additional WhatsApp document-sending tip; its overall reason also inaccurately claims the answer did not address JPEG despite accepting its JPEG statement. These observations require judge calibration, not invented price changes.

There are **36/40 metric results meeting the existing 0.7 threshold**, with cases 5 and 7 Faithfulness, case 4 Answer Relevancy and case 6 Contextual Precision below it. Case 6's Precision is 50.00%, so irrelevant return-policy context remains a concrete retrieval limitation despite the aggregate target being met. Zero scoring errors means valid recorded scores, not that every threshold passed or that semantic judgments are infallible. Borderline Faithfulness/Answer Relevancy verdicts still count under the existing recipe and remain visible in case evidence.

Case 2's ordered contexts remain identical to the fresh baseline although Recall changes from zero to one. Case 9 already changed from 2/3 to one between the baseline and complete OSS run with identical ordered contexts; the final run keeps Recall at one but changes context order and replaces one unrelated passage. Case 3 Precision also changes from 80.42% in the complete OSS run to 100% in the final run with identical question, reference, ordered contexts and judge settings. The identical-input changes are judge variation. As a sensitivity calculation, holding baseline Recall at zero for case 2 and 2/3 for case 9 while retaining the other eight final values gives **86.67%**. This is arithmetic, not a separate measured run or an adjustment to the official 100.00% score; it illustrates that the target does not depend on those two favorable judgment changes.

Only ten legacy development questions are measured. Per-case standard errors are 6.63 percentage points for Faithfulness, 3.33 for Answer Relevancy, 0.00 for Recall and 5.39 for Precision. Recall's zero reflects identical scores in this small sample, not certainty. The mean is not a probability of customer correctness, and standard error does not capture reference bias, judge error or population coverage. The DP reference still needs separate business review before any replacement benchmark can be considered independent evidence.

## Verification and evidence

- Complete offline backend suite after the final prompt changes: **326 passed, 11 expected skips**, two existing deprecation warnings, 58.46 seconds. The offline suite skipped ten paid single-question cases and one review-gated conversation test. Fresh authenticated admin runs exercised all ten legacy questions and their four metrics; the paid pytest assertions and conversational evaluation were not executed.
- Frontend lint and TypeScript/Vite production build: passed; ten existing lint warnings, zero lint errors.
- Fourteen durable evaluation tests cover checkpoint/retry isolation and preservation of conversational pairs. Thirty structured-provider/intent/attachment tests cover schema safety, usage, copied trace context and cancellable transport behavior.
- `git diff --check`: passed. Tests use disposable loopback PostgreSQL on port 54585, never the hosted administration database.
- All legacy question/reference pairs and the original CSV remain frozen: CSV SHA-256 `5a2e7007d79921c613c1366cafc0e21755e6f3a594ef7e54c8ec3ffc355a36e8`; row-dataset SHA-256 `be04e9dc4d73e1c8a123e96a16452cf35999d7c6b33837297055e3b9fd37555b`.
- The OSS scoring postflight verifies exact source/configuration/prompt/runtime hashes through completion of all forty scores, before later local prompt edits. Its reporting then completed without changing those saved results.
- Final GLM preflight/postflight match exactly for business sources, configuration, active namespace and fourteen runtime source hashes. They freeze answer prompt `f7b590b832f4e6a2d940bf45287ce579c4f9f06420d5203a1ce3e3a65079c9ce`, intent prompt `1fc8a6965b2d8bdef91d477706de1fbb7b71de34e2b7c2351b2342dbb1e0861f`, top-k five and the recorded judge settings. All forty saved scores reproduce from their recorded numerator/denominator calculations.
- Independent LangSmith review verifies exactly ten complete answer roots and forty complete metric roots, without duplicates, unfinished roots or errors. Every actual model request matches Luna answering/GLM intent; all twenty prompts have one current human message and no prior AI history. Each answering system prompt and intent instruction prefix matches its frozen snapshot. No fallback erased an answer, no attachment guard ran, and no rerank fallback occurred.
- The final browser session initially expired with HTTP 401 during reporting. It correctly returned to sign-in and was handed to the user; no session was created or extended by the agent. Terminal results were captured read-only through the same store readers used by the authenticated export API. After the user signed in and confirmed completion, the same browser space was resumed for the fresh UI verification below. The earlier [loading/empty/error and broader UI verification](evaluations-ui-2026-10-23.md) remains documented separately; the only UI change in this recovery is interrupted-checkpoint copy.

The [research record](../research/2026-10-24-contextual-recall-recovery.md) links the Exa/Context7-checked primary sources. Full exports, preflights, probes and independent LangSmith audits are retained locally under `data/evaluations/recall-recovery-2026-10-24/`. The durable [comparison bundle](../../testing/comparisons/2026-10-24-recall-recovery.json) contains all four raw runs, per-case calculations, protocol freezes, unsuccessful attempts and independent audits (2,503,120 bytes; SHA-256 `b46b38a6f8deeb657260cdd2261da7d9a87cb631d495db8248fb12734831a245`). The [completed LangSmith experiment](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/beb4a913-508a-48b3-9017-dc17478d8893) contains the final live traces.

## Delivery boundary

Source revision 16 is activated in the administration knowledge store. Intent GLM is saved through Providers. Code/UI changes are in the local working tree and the local backend was restarted; no commit, merge or deployment is claimed. No customer WhatsApp message was sent, and no production WhatsApp receipt or image-delivery claim is made.

## Authenticated UI follow-up after sign-in

The final result panel was inspected in Ego Lite after the user confirmed successful sign-in. It displays the correct full run ID, Completed status, ten recorded cases, frozen snapshot/model metadata and all four recorded means with 10/10 coverage and zero errors. The browser's normal Export JSON action downloads a result whose decoded JSON exactly matches the terminal capture above; no evaluation or provider call was triggered.

Keyboard activation opens Inspect result in its dedicated URL, resets scroll to zero and focuses the run heading. Case 5, its Faithfulness reason and its five ordered retrieved passages open through keyboard-operated disclosures. Need attention identifies exactly cases 4, 5, 6 and 7. Back to evaluation history restores both filters (`status=completed`, `task=evaluate`), the same Inspect result focus and the exact prior scroll position of 573.5 CSS pixels.

Fresh screenshots were visually reviewed at desktop 1788×1007 and mobile 390×844 in both light and dark themes. Run/snapshot identifiers wrap, metric explanations remain readable and case answer/reference/evidence stack without horizontal overflow. Measured document widths equal viewport widths at 390 and 320 pixels; 320 pixels received an overflow measurement rather than a separate visual review. The original light theme and desktop viewport were restored. Loading, empty and error states were not repeated in this follow-up.

Screenshots, authenticated export and `verification.json` are retained under `data/evaluations/recall-recovery-2026-10-24/ui-check/`. The earlier comparison bundle and its recorded hash remain unchanged; this follow-up supersedes its historical pending GUI status only.
