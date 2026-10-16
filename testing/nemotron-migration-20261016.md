# Nemotron migration verification — 16 October 2026

## Configuration

- Embedding: `nvidia/nemotron-3-embed-1b:free`, OpenRouter, 2048 dimensions, L2 normalized.
- Pinecone: `chatbot-nadhif`, cosine; eight verified namespaces and 1,054 vectors.
- Eight original knowledge versions retained; seven indexed replacements and one draft. All 48 copied files were verified against their sources.
- Seven primary legacy10 runs: 70 cases, 350 final scores.
- Answering model: `anthropic/claude-haiku-5.5`; judge: `deepseek/deepseek-v4.1-flash`; top-k: 5.
- Dataset and prompt fingerprints match across all seven runs. No new E5 control run was performed.

## Results

| Nemotron version | Chunking | Chunks | Faithfulness | Relevancy | Precision | Recall | Business correctness | Median answer seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [nemotron-3e9de116004f](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/546bb1d6-8405-49fe-a213-bc3c5121bd98) | 1500/200 | 95 | 0.975 | 0.925 | 0.726 | 1.000 | 0.744 | 9.27 |
| [nemotron-08921960cce9 (published replacement)](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/68beb480-2049-4b28-aeed-6a298c7a0073) | 1500/200 | 95 | 0.907 | 0.840 | 0.726 | 1.000 | 0.684 | 9.60 |
| [nemotron-e23c009a5eb6](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/793ab590-5da9-4774-986b-9ce6b1490954) | 1000/100 | 139 | 0.864 | 0.860 | 0.687 | 0.833 | 0.551 | 8.85 |
| [nemotron-e01f5005f284](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/bbde9cbb-ddc9-4907-95eb-678a29bad7a7) | 800/80 | 173 | 1.000 | 0.867 | 0.903 | 0.750 | 0.596 | 9.02 |
| [nemotron-272dcb7918a2](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/766e7b6e-e946-4994-8d62-cdd41a0b8056) | 1000/0 | 136 | 1.000 | 0.924 | 0.701 | 0.750 | 0.695 | 10.12 |
| [nemotron-e22b7c691549](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/26fbd9fc-aae8-4ee6-8cc1-aaf95c4a8df0) | 1000/100 | 138 | 0.988 | 0.870 | 0.781 | 0.817 | 0.705 | 9.48 |
| [nemotron-9310488babe1](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/603d61fa-b3c9-486f-9504-51a0d0fe8bb2) | 1000/100 | 139 | 0.967 | 0.943 | 0.775 | 0.767 | 0.583 | 10.14 |

Scores are descriptive results from a small historical dataset. They are not evidence that the embedding change improved quality over E5: no paired E5 experiment was run. Different chunk configurations also carry their historical source/preprocessing differences.

## Quality limitations

The published replacement has mean business correctness below the 0.7 scoring threshold. Review its per-case outputs rather than treating a completed job as a quality pass. Examples include the legacy DP reference allowing 50–60% while the retrieved policy says a minimum of 60%, and legacy price references assuming a quality/material that the customer did not specify. Clarification can be appropriate even when the reference expects a total. One price response also ended mid-sentence; the existing answering-model budget remains a separate limitation.

For the A3+ 5×5 cm question, the official Kiss Cut reference is 35 pcs. The legacy generic question can also elicit a manual-cutting alternative; keep the distinction explicit when interpreting that result.

## Observed provider failures and recovery

- One judge returned repetitive non-JSON text and exhausted the unchanged output budget. A single retry of that Faithfulness measurement succeeded; original error and retry trace were retained.
- One answering-provider response was empty after consuming its output budget. That case was retried once with the same model, prompt, top-k, and namespace, then its five metrics were measured again. The original response and failed measurements were retained.
- A concurrent coordination checkpoint overwrite started one duplicate evaluation attempt. It was stopped, retained as interrupted, and excluded from the seven primary runs. The private ledger records its ID; one completed case was preserved. The runner now reloads reservations between versions, covered by a regression check.
- Consequently, API usage and total attempts exceed 70 generated answers / 350 metric attempts. The table reports the final 70 primary cases and 350 valid scores; it does not conceal the extra attempts.

## Functional checks

Before activation, direct calls through the migrated published-version RAG pipeline successfully answered:

- Greeting and store address.
- Explicit 5×5 cm Kiss Cut: **35 pcs per A3+**.
- Flexi China 280 GSM standard, 2×1 m × 3 sheets: **Rp99,000**.
- Two boxes of Art Carton single-sided business cards without lamination plus one Flexi 280 X-Banner package including frame: **Rp100,000**.

## Automated checks

- 109 backend regression checks passed, including PostgreSQL transport/lifecycle, archive boundaries, embedding validation, migration resume, empty-answer rejection, and WhatsApp queue/reconciliation.
- 12 frontend recovery checks passed.
- Frontend production build passed; lint has eight existing warnings and no errors.
- FastAPI import passed with local inference packages unavailable.

## Activation and final integration

- Activated published replacement: `nemotron-08921960cce9`; `.env` now selects Nemotron / 2048 / `chatbot-nadhif`.
- Backend restarted successfully; `/health` returned 200, the WhatsApp worker is running, and runtime mode is `live`.
- WAHA session was observed `WORKING`. The full recorded maintenance interval was reconciled: no missing inbound messages were found.
- Administration data contains 16 versions: eight read-only originals, one new published version, six new ready versions, and one new draft.
- Real dashboard Playground request succeeded after restart: 5×5 cm Kiss Cut → 35 pcs, five retrieved sources, 13.639 seconds, with a LangSmith trace. This confirms the browser → FastAPI → Nemotron → Pinecone → answering-model path.
- Fresh WhatsApp verification completed: inbound address question received 16 October 2026 17:17:40 WIB, one reply marked sent at 16 October 2026 17:18:03 WIB, ACK 2 observed, no inbox error. The reply names both Ciputat and Pamulang branches. LangSmith metadata confirms channel WhatsApp, published version `nemotron-08921960cce9`, Nemotron / 2048 dimensions / `chatbot-nadhif`. RAG processing took 15.13 seconds.
- The dashboard Providers section displays the new model, index, and dimensions. Evaluation history and saved result inspection also loaded successfully.
- Existing browser authentication survived the restart. A separate password-login probe was not completed because `ADMIN_PASSWORD` is unset in `.env`; it does not replace the existing account password stored in PostgreSQL.

![Published Nemotron Playground verification](nemotron-playground-20261016.png)

Operational procedure: [Nemotron migration runbook](../docs/runbooks/nemotron-embedding-migration.md).
