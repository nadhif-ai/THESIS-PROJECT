# Evaluation arithmetic

New single-question dashboard runs use recipe `chunking-fact-coverage-v1`:

| Measure | Calculation | Decision source |
| --- | --- | --- |
| Precision@k | Relevant returned passages / requested k | Offline annotations |
| Fact Coverage@k | Distinct covered reference facts / all reference facts | Offline annotations |
| Faithfulness | Accepted claim verdicts / all claim verdicts | DeepEval LLM judge |
| Answer Relevancy | Accepted statement verdicts / all statement verdicts | DeepEval LLM judge |

Internal staff correctness assessment and WhatsApp SUS are separate research instruments. No staff-rating input is added to the dashboard. New conversational runs retain turn faithfulness, turn relevancy and conversation completeness; they do not run Business correctness. Historical results and running checkpoints retain their original recipes and metric order.

## Reading the results

Expand **Evaluation methods and formulas** in Evaluation history. After opening a run, expand **How the run averages are calculated**, then a case and its metric. New records save ratio operands, counted items and verdicts. Exports include the same evidence. Old scores without these traces cannot be reverse-engineered into claim counts; the interface says so explicitly.

The run average is `sum(available case scores) / number of available case scores`. Missing and failed scores are excluded, never converted to zero. The interface shows each denominator. Percentages represent means multiplied by 100, not case pass rates. Retrieval measures are score-only; no unvalidated pass threshold is added.

DeepEval 4.2.8 accepts `yes` and `borderline` for the current Faithfulness and Answer Relevancy configuration. Borderline is not proof of support or business correctness. With no extracted items, the library returns 1 for these two metrics; the interface discloses that convention instead of inventing a `0/0` calculation. The configured 0.7 judge threshold remains an engineering setting, not an academically established acceptance criterion. A trace is saved only if it reproduces the actual score. Historical Contextual Precision traces use weighted cumulative precision, not unweighted Precision@k.

## Offline retrieval annotations

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

Changing that file invalidates the existing QA reference review. Re-review the research references before submitting the audited dataset. This records dataset readiness, not the separate staff answer assessment. The original CSV benchmark has no new annotations and will show unavailable retrieval scores until an annotated QA dataset is used.

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

Sources: [DeepEval Faithfulness](https://deepeval.com/docs/metrics-faithfulness), [Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision), and [RAGAS, EACL 2024](https://aclanthology.org/2024.eacl-demo.16/). Fact Coverage@k is this study's explicitly defined operational measure, not standard passage recall attributed to RAGAS or DeepEval.
