# Evaluation arithmetic

New single-question dashboard runs use recipe `rag-four-metrics-v1` in this order:

| Measure | Calculation | Decision source |
| --- | --- | --- |
| Faithfulness | Accepted claim verdicts / all claim verdicts | DeepEval LLM judge |
| Answer Relevancy | Accepted statement verdicts / all statement verdicts | DeepEval LLM judge |
| Contextual Recall | Attributable reference statements / all reference statements | DeepEval LLM judge |
| Contextual Precision | Sum of cumulative precision at relevant ranks / relevant returned contexts | DeepEval LLM judge |

Business correctness/G-Eval, Hit Rate, source-filename Precision@3, annotated Precision@k and Fact Coverage@k are not part of new single-question runs. Internal staff assessment and WhatsApp SUS are separate research instruments. New conversational runs retain turn faithfulness, turn relevancy and conversation completeness. Historical results and running checkpoints retain their original recipes and metric order. The dashboard research view shows the four QA metrics where recorded; exports preserve the complete original record, including historical extra metrics. Missing contextual scores are never inferred from annotated scores.

## What the judge decides

Faithfulness compares extracted answer claims with retrieved context. Answer Relevancy compares answer statements with the question. Contextual Recall checks reference-answer statements against the complete returned context. Contextual Precision judges each returned context against the question and reference answer, then weights the relevance decisions by rank. All four use `eval_mode="llm"`; removing G-Eval does not remove LLM judgement.

For recall, `CR_i = A_i / N_i`: `A_i` is the number of attributable reference statements and `N_i` is the number judged. For contextual precision, `CP = Σ(P@j × r_j) / Σr_j`, with `P@j = Σ(l≤j)r_l / j` and `r_j` equal to 1 for a relevant context, otherwise 0. A relevant context near the beginning contributes more. This is not unweighted Precision@k. The judge makes semantic decisions; code performs the arithmetic.

## Reading the results

Expand **Evaluation methods and formulas** in Evaluation history. After opening a run, expand **How the run averages are calculated**, then a case and its metric. New records save ratio operands, counted items and verdicts. Exports include the same evidence. Old scores without these traces cannot be reverse-engineered into claim counts; the interface says so explicitly.

The run average is `sum(available case scores) / number of available case scores`. Missing and failed scores are excluded, never converted to zero. The interface shows each denominator. Percentages represent means multiplied by 100, not case pass rates. The UI reports the configured judge threshold checks separately from these means.

The configured Faithfulness and Answer Relevancy metrics accept `yes` and `borderline`; Contextual Recall and Contextual Precision count only `yes`. Borderline is not proof of support or business correctness. With no extracted items, the library returns 1 for the two answer metrics and 0 for the two contextual metrics; the interface discloses that convention instead of inventing a `0/0` calculation. The configured 0.7 judge threshold remains an engineering setting, not an academically established acceptance criterion. A trace is saved only if it reproduces the actual score. Contextual Precision traces include each rank, cumulative precision and weighted contribution. Old scores without verdict traces are not reverse-engineered from percentages or free-text reasons.

## Historical offline retrieval annotations

The retired `chunking-fact-coverage-v1` recipe below remains supported only for resuming existing checkpoints and interpreting saved exports. New runs do not require these annotations. For new chunking comparisons, hold corpus, questions, references, embedding, prompt, answer model, judge and top-k fixed; compare all four metrics together.

Keep questions and reference fact IDs/text fixed across chunking configurations. Fix embedding, top-k, prompt and answer model. Label passage relevance and fact coverage separately for each passage snapshot. Do not infer labels from filenames or treat missing labels as negatives.

Add `retrieval_annotations` to the corresponding row in `testing/evals/qa-reference-candidates.json`. This is a schema example, **not a reviewed case or a usable golden**:

```json
{
  "retrieval_annotations": {
    "question_sha256": "SHA256_OF_EXACT_QUESTION",
    "snapshot_sha256": "SHA256_FROM_RETRIEVAL_MANIFEST",
    "facts": [
      {"id": "stable-fact-id", "text": "Replace with an independently verified reference fact"}
    ],
    "passages": {
      "SHA256_OF_PASSAGE_SOURCE_AND_TEXT": {
        "relevant": true,
        "fact_ids": ["stable-fact-id"]
      },
      "SHA256_OF_AN_IRRELEVANT_PASSAGE": {
        "relevant": false,
        "fact_ids": []
      }
    }
  }
}
```

Changing that file invalidates the existing QA reference review. Re-review the research references before submitting the audited dataset. This records dataset readiness, not the separate staff answer assessment. The original CSV benchmark has no annotations, so historical annotated runs can have unavailable retrieval scores. That limitation does not apply to new contextual-metric runs.

Calculate identifiers with shared helpers (read-only database access):

```python
from app.admin import store
from testing.evals.calculations import passage_key, question_key, retrieval_manifest

snapshot = store.version()
print(retrieval_manifest(snapshot["records"])["snapshot_sha256"])
print(question_key("Exact question from the QA row"))
for passage in snapshot["records"]:
    print(passage_key(passage), passage["metadata"].get("source"), passage["document"])
```

Annotate all passages for a complete offline benchmark, including explicit irrelevant labels. At minimum every returned passage needs a label, or both scores remain unavailable. Keys bind exact passage text and source. Snapshot hashes bind the full passage set, so annotations cannot silently be reused after changing chunking or knowledge. Question hashes prevent reuse after a question changes. Rows, annotations and snapshot metadata are frozen in each run.

Precision divides by requested k even when fewer passages are returned. Coverage counts each fact once across top-k passages, even when overlapping passages repeat it. Map a passage to facts it sufficiently contains; partial fragments do not establish an entire fact. Empty fact sets, malformed labels, duplicate retrievals or stale hashes produce unavailable scores. Valid annotated cases with no retrieved passages score zero. Unanswerable cases require a separate protocol, not an invented fact denominator.

## Verification

Offline checks cover arithmetic, duplicate facts, missing/stale labels, judge borderline/empty policies, and checkpoint continuation. No model calls are needed:

```sh
venv/bin/python -m pytest testing/test_evaluation_calculations.py testing/test_durable_evaluations.py testing/test_dashboard_progress.py -q
cd frontend
npm run build
```

Sources: [DeepEval Faithfulness](https://deepeval.com/docs/metrics-faithfulness), [Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy), [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision), and [RAGAS, EACL 2024](https://aclanthology.org/2024.eacl-demo.16/). The retired Fact Coverage@k measure was an operational definition in the historical annotation protocol, not standard passage recall attributed to RAGAS or DeepEval.
