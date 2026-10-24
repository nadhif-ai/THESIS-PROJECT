# Final unseen eight-case sample — 24 October 2026

Eight source-grounded single-turn goldens were generated **after** the final application prompt was frozen at SHA-256 `ae0161f05d799c7d06aaf53ec32d2a95e3130487930924be50239d3663ea9914`. They are intended for one final evaluation with that fixed application, followed by reporting rather than further tuning on their results.

Dataset: [`testing/evals/.retrieval-final-holdout.json`](../../testing/evals/.retrieval-final-holdout.json). Frozen at **24 October 2026, 01:48:05 Asia/Jakarta** (`2026-10-23T18:48:05.533064+00:00`). Dataset SHA-256: `0741633ac4777163f5611e4843a786299f9ec8391e37c2ddced5c63f45751965`.

The original twelve questions in `.retrieval-holdout.json` are now **development-validation**, because their observed answer evidence informed a later general grounding/property-inference guard. Their historical filenames and scores are preserved, but they are not the final unseen sample. This new eight-question file restores a final post-freeze check without rewriting earlier references or hiding unfavorable results.

## Source-only generation

Generation used the actual DeepEval 4.2.8 Typer `generate` command, `--method contexts --variation single-turn --max-goldens-per-context 1 --sync-mode --max-concurrent 1`. Four bounded family batches contained two exact source contexts each. The existing generation-only adapter injected the configured application OpenRouter judge, `z-ai/glm-5.3-flash`, with temperature 0 and low reasoning effort, without changing persisted provider settings or placing keys in shell arguments.

The context method avoided new embedding calls and did not consult application retrieval. Inputs were exact pre-change source excerpts from `/tmp/rag-knowledge-before`; their business facts still apply in the new snapshot. The source snapshot was `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, and the fixed application evaluation snapshot is `kb-0a4b41713f9e423799b20387bda6597b`.

Neither optimized application answers nor scoring outcomes entered the generation prompts. Coverage constraints selected new quantities and contrasting needs from the stated research scope; the model authored the questions and expected answers. All eight initial outputs passed agent source validation. There were **no rejected generations, replacement batches, reference-answer edits, or JSON-answer unwrapping** for this sample.

The [machine-readable provenance](2026-10-24-retrieval-final-holdout-generation.json) contains exact source excerpts, file/excerpt hashes and line ranges, the full generation/styling configuration, generation-adapter settings/system instruction and code hash, and all eight raw goldens. Each dataset row also records exact supporting quotes and agent validation notes.

## Frozen coverage

| ID suffix | New question coverage | Source-grounded required result |
| --- | --- | --- |
| 01 | Send a design to named Ciputat branch | File-submission email `asiavisualgrafika@gmail.com`; distinguish it from physical location or general WhatsApp. |
| 02 | Visit named Pamulang branch | Exact Jl. Pajajaran No. 38 address, MTsN landmark and source Maps link. |
| 03 | Two X-Banner Flexi China 340 GSM packages | 60×160 cm, frame included; 2 × Rp70,000 = Rp140,000. |
| 04 | One 3×1.5 m Flexi China 280 GSM HR spanduk | 4.5 m² × Rp25,000/m² = Rp112,500; already a multiple of Rp500. |
| 05 | Customer typo versus shop wrong material | Customer-file typo excluded; shop-originated wrong material gets free reprint with physical proof. |
| 06 | Excess-transfer refund timing and method | Transfer through BCA within one working day; no cash refund. |
| 07 | JPEG resolution, color and save quality | At least 300 DPI, CMYK, Quality 10–12/Maximum. The generated question's `CMR` is a user typo, not an alternative accepted profile. |
| 08 | Ritrama no-residue property and listed benefits | Source's removable-adhesive/material facts; no assumption of paint safety, freedom from damage, or a new warranty. |

The price calculations were independently checked against the stated quantities and units. Source validation checked that every supporting quote exists in its original hashed source, and loading through `EvaluationDataset.add_goldens_from_json_file` produced eight goldens. IDs/questions are unique and have no exact duplicate among the ten legacy questions or the original twelve development-validation questions. Every `actual_output` was null at freeze.

## Research boundary

Validation was performed by an agent against the recorded source text, **not by a human business operator**. The source facts, generation and evaluation judge can share biases. The eight scenarios were selected to stress the intended distinctions and contain new questions/quantities; they are not a random representative customer sample or unseen intent families. Eight questions provide a small final smoke check rather than a statistical guarantee of accuracy or an ≥87% production precision bound.

Keep this file unchanged for the final evaluation, record the final prompt/model/knowledge configuration, and report all per-case outcomes, missing scores and errors. Do not tune further on its outputs or change references to favor answers. A later optimization would require a new validation sample. Earlier results remain development evidence even if a later phase scores better.
