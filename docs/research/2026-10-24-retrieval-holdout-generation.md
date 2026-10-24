# Source-grounded retrieval hold-out — 24 October 2026

Twelve new single-turn QA goldens were generated using the actual DeepEval 4.2.8 `generate` CLI and frozen before evaluating the tuned pipeline. The sample is a targeted stress check for the distinctions being changed, not a representative production benchmark or a statistically powerful generalization study.

Dataset: [`testing/evals/.retrieval-holdout.json`](../../testing/evals/.retrieval-holdout.json). SHA-256: `6f60628bdc39976372a5ac12e0c0c532cb39a8660f0acd5c3654cfc6b383d386`. Frozen at **24 October 2026, 01:19:38 Asia/Jakarta** (`2026-10-23T18:19:38.554252+00:00`).

The goldens use standard `input`, `expected_output`, and `context` fields, with stable IDs and `additional_metadata`. `actual_output` is null in every row. Metadata records the source file, original source hash, excerpt line range/hash, exact supporting quotes, generation batch, normalization, and agent validation notes. [Machine-readable provenance](2026-10-24-retrieval-holdout-generation.json) preserves the raw generation output, rejected cases, source excerpts, source inventory, generation configuration and selection ledger.

## Generation and independence

The only factual inputs were exact excerpts exported from the pre-change source documents in `/tmp/rag-knowledge-before`. The original knowledge snapshot is `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, source revision 10, corpus SHA-256 `a2f9e7365454bcb8ac069fe599276bec21eca7d5179f553a68c8bcdb7a27ca49`.

The `contexts` method was chosen so generation used those exact source excerpts without new embeddings or the retrieval pipeline being optimized. No tuned-pipeline answers or retrieval outputs were inspected to construct the questions or references. No expected answers were copied from chatbot outputs. Existing development benchmark questions were excluded from exact duplication; their intent families are intentionally shared because the check tests paraphrases and contrasting conditions within those families. This does not establish independence at the intent-family or business-domain level.

Four family batches each contained three source contexts and requested at most one single-turn golden per context. A temporary `Synthesizer` subclass injected the application's configured `OpenRouterJudge` into the real Typer CLI. It used `z-ai/glm-5.3-flash`, temperature 0, low reasoning effort, and the existing backend credentials. No credentials were placed in shell arguments or reports, and no persisted provider settings were changed.

The command shape was:

```sh
deepeval generate --method contexts --variation single-turn \
  --contexts-file FAMILY-contexts.json --sync-mode --max-concurrent 1 \
  --max-goldens-per-context 1 --output-dir OUTPUT --file-name FAMILY-goldens \
  --scenario SCENARIO --task TASK --input-format INPUT_FORMAT \
  --expected-output-format EXPECTED_OUTPUT_FORMAT
```

The application model was injected rather than relying on an unrelated global CLI provider default. Full styling values are in the provenance JSON. They request concise Indonesian WhatsApp questions, one primary intent, answers grounded only in source facts, and clear distinctions between addresses/contacts, area-based pricing/packages, shop/customer errors and sticker uses. Generation kept DeepEval's standard one evolution and input-quality filtering defaults.

## Pre-freeze validation and bounded repair

Agent source validation rejected three of the first twelve generated cases **before** any pipeline evaluation:

1. A generic physical-address question had a reference for only one branch despite the source corpus having two branches. It was replaced by a named-Ciputat-branch question.
2. A combined X-Banner/spanduk question omitted X-Banner material, but its reference assumed 340 GSM and incorrectly claimed spanduk pricing was unavailable. It was replaced by a fully specified three-package X-Banner question.
3. A Cromo question's generated expected output was a Faithfulness verdict rather than a customer answer. It was replaced by a new Cromo question and answer.

The inherited judge adapter's metric-specific system instruction contributed to output-format contamination: several generated answer strings contained evaluator JSON. One bounded three-context CLI generation batch used a generation-specific system instruction with the same configured OpenRouter client/settings. The instruction requests source-grounded customer answers rather than scores or verdicts; its full text is recorded in the provenance JSON. It does not change evaluation metric definitions or later scoring instructions.

For six otherwise valid retained goldens, the generated JSON's `answer` or `response` string was extracted verbatim and evaluator metadata discarded. Those reference-answer words were not rewritten. The three rejected initial goldens and all replacement outputs remain in provenance. Selection did not depend on an optimized-pipeline score.

LangSmith MCP verified the [final Cromo reference-generation completion](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a169fb-ba8d-7e21-971a-8552fc279cae/run/01a169fb-ba8d-7e21-971a-8552fc279cae?start_time=2026-10-23T18:17:47.405544Z): model `z-ai/glm-5.3-flash`, `finish_reason=stop`, 94 completion tokens. The content matches the frozen reference. A successful generation trace is not proof of business correctness or human approval.

## Frozen coverage and source checks

| ID suffix | Need tested | Required source-grounded outcome | Original source lines |
| --- | --- | --- | --- |
| 01 | Pamulang landmark | In front of MTsN Kota Tangerang Selatan | SOP 13–17 |
| 02 | General WhatsApp contacts | Admin 1 `0896-9241-1115`; Admin 2 `0897-3232-322`; no invented branch assignment | SOP 19–25 |
| 03 | Named Ciputat physical address | Jl. Ir. H. Juanda No. 17, Cempaka Putih, Ciputat Timur; opposite SPBU Ciputat | SOP 8–12 |
| 04 | 4×2 m Flexi China 340 GSM HR backdrop | Rp32,000/m²; 8 m² × Rp32,000 = Rp256,000 | Prices 7–21 |
| 05 | Three X-Banner Flexi Korea 440 GSM packages | 60×160 cm, frame included; 3 × Rp90,000 = Rp270,000 | Prices 41–52 |
| 06 | X-Banner frame only | Rp30,000 per piece, without printed visual | Prices 52 |
| 07 | Shop size/material production error | Free reprint with physical evidence of the faulty product | SOP 93–94 |
| 08 | Blurry original customer file | No compensation/free reprint for the original file's insufficient resolution | SOP 95 |
| 09 | Cancellation before processing | Less than two hours after payment agreement **and** before operator processing; no claim that actual status has been checked | SOP 88–92 |
| 10 | Writing on Cromo jar labels | Ballpoint pen supported; not waterproof; no food-contact certification claim | Materials 74–77 |
| 11 | Car wrapping with no adhesive residue | Ritrama's removable adhesive and curved-body suitability; no unsupported opposite claim about China vinyl | Materials 78–85 |
| 12 | OWV outside versus inside view | Full graphic outside, outward view through perforations from inside; no night-privacy guarantee | Materials 90–92 |

Source filenames and hashes:

- SOP: `01_sop_dan_kebijakan_toko.txt`, `31bc29dd769d698d0e9988f8d12dd26757a5303348fd441fba8295022f965fdc`.
- Prices: `04_daftar_estimasi_harga.txt`, `048fc683a95b9c5884d01348770f2a815a51d5bd998766dbff6249bc2f67b048`.
- Materials: `02_spesifikasi_bahan_dan_finishing.txt`, `448fc0a469256712acda22d22aea4a674210b828a3e0761260ed5ee38d4a7352`.

Validation loaded all twelve records through `EvaluationDataset.add_goldens_from_json_file`, checked unique questions/IDs and no exact duplicate of the ten legacy questions, verified source hashes and supporting quotes, checked both price calculations independently, and confirmed null actual outputs. These checks were offline and produced no evaluation scores.

## Interpretation and use

The references were **validated against sources by an agent, not reviewed by a human business operator**. Validation establishes consistency with the recorded source text, not independent real-world truth. The generation model is also the configured evaluation judge, which adds another reason to retain independent human calibration and report the sample's limited coverage.

Freeze these questions/references for the paired baseline/tuned comparison. Record the answer prompt, models, judge protocol, top-k, retrieval recipe, and both knowledge-snapshot IDs. Keep scoring errors and coverage explicit. Do not tune further ranking rules against hold-out answers or labels after seeing its results; a later tuning round needs a fresh validation set. Preserve these references if a result is poor. Source corrections require independent business evidence and a new dataset version, not a rewrite to favor output.

The requested optimization target remains a target. A perfect score on twelve source-driven synthetic questions is neither a correctness probability nor evidence that all production questions are covered. Report the raw outcome, including 100.00% if that is what the frozen judge actually returns.
