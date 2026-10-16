# Chroma retrieval baseline — 12 October 2026

The original 10-case retrieval benchmark produced Hit Rate@3 **90%** and source-file Precision@3 **0.6000** against the existing 95-chunk Chroma corpus. It used local multilingual E5 embeddings and made no answering-model or WhatsApp calls.

| Artifact | Contents |
| --- | --- |
| `manifest.json` | Source and artifact checksums, sanitized settings, dependency versions, embedding cache revision, Git revision, and index configuration |
| `index_snapshot.json` | Original chunk IDs, text, metadata, and 384-dimensional vectors |
| `source_snapshot.tar.gz` | Original application, benchmark, dataset, and business knowledge files; excludes environment credentials and customer chat history |
| `answers.json` | Original 10 generated answers, retrieval context, usage, and LangSmith trace IDs captured before migration |
| `results.json` | Per-case retrieval results and aggregate scores |
| `retrieval.csv` | Original benchmark CSV output |
| `summary.txt` | Original benchmark summary |

The capture ran the existing evaluation functions with their output destinations redirected into this directory. The index build marker matched the current knowledge hash. Evaluation k=3 and application runtime k=5 are separate recorded settings. The answering-model setting is recorded for the subsequent answer capture, but did not affect these retrieval scores.

Filename matching is the original relevance proxy: a retrieved chunk counts as relevant when its source filename contains the expected source string. This is not manually labeled chunk relevance or generated-answer correctness. Case 5 missed the expected price source. No changes were made to improve the benchmark before saving it.

For reproduction after migration, use the archived source and dataset in an isolated environment with the recorded dependency versions, restore a separate Chroma collection from the saved documents, metadata, and vectors, and run the archived benchmark against that collection. Preserve this directory as the reference capture; write later comparisons into a new run directory.
