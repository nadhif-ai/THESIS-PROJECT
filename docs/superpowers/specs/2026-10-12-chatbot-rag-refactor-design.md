# Chatbot RAG refactor design

Status: implemented locally. The user approved the interview recommendations, selected LangSmith, and explicitly instructed continuing with grill-with-docs without the brainstorming workflow. The implementation and validation details below record that scope.

## Purpose and agreed scope

Improve the Asia Visual Grafika chatbot for one business, retain real WhatsApp operation, and produce reproducible thesis comparisons. The work order is: capture the existing evaluation baseline; migrate ingestion and retrieval to Pinecone; build a React + Vite + shadcn admin dashboard, playground, and DeepEval integration. FastAPI remains the backend and exposes the same RAG service to WhatsApp, playground, and evaluation callers.

The admin contains Dashboard, Knowledge, RAG & Playground, Conversations, Providers & Settings, and Evaluations. The application runs locally on macOS during this work. Deployment configuration can be designed after the refactor; no new hosting account or deployment is required for this phase.

## Verified current state and captured baseline

The Python 3.12.13 environment contains Chroma 1.5.1, LangChain Core 1.5.3, LangChain OpenAI 1.1.7, and LangSmith 0.14.7. Pinecone and DeepEval packages are not installed yet. Credentials are present for Pinecone, LangSmith, and OpenRouter, and have not been written into artifacts.

The existing Pinecone index `chatbot-avg` is ready, dimension 384, cosine metric. The LangSmith project `chatbot-avg` is accessible through `https://api.smith.langchain.com`.

The current `.env` selects `intfloat/multilingual-e5-small`, `anthropic/claude-haiku-5.5`, and runtime retrieval k=5. E5 embeddings run locally on CPU, normalize vectors, and use `passage: ` and `query: ` prefixes. The answering model and proposed Gemini evaluation judge are listed in OpenRouter's model catalog; their generation and structured-output behavior still need a bounded live check.

The existing benchmark contains 10 cases with question, category, expected source, and reference answer. It queries Chroma at k=3 without the application's intent filter. It measures whether returned source filenames contain the expected filename; it does not use reference answers or call the generator. Captured scores: Hit Rate@3 90%, Precision@3 0.6000. Case 5, an abbreviated banner price question, misses the expected source. These scores describe the legacy retrieval benchmark and are not generated-answer accuracy.

The capture is stored in `testing/baselines/2026-10-12-chroma/`: manifest, per-case results, CSV, summary, the 95 indexed chunks with their original vectors and metadata, and an archive of the relevant application and knowledge source files. The manifest records file hashes, dependency versions, Git revision, index metadata, and settings. This snapshot provides a frozen reference even if knowledge changes later.

Before replacing the application retriever, capture answers and context for the original 10 cases using the current application pipeline and isolated evaluation sessions. Evaluation messages must not enter customer conversation logs. Preserve the LLM, prompt, runtime k=5, filters, and conversation behavior for the matched backend comparison. The legacy retrieval experiment remains k=3. The two experiment types must be labeled separately.

## Architecture and boundaries

FastAPI coordinates a RAG service, a knowledge administration service, and an evaluation service. The vector store boundary handles ingestion, metadata filtering, retrieval, and namespace selection. It returns source documents and explicitly named scores to the RAG service. LangSmith records execution traces and experiment feedback. DeepEval computes quality scores.

For the local phase, use a small SQLite database under the ignored application data directory for document records, knowledge versions, published-version selection, application settings, job state, conversations, and evaluation summaries. Store uploaded originals in that directory and vectors in Pinecone. This removes JSON-file rewrites from conversation persistence and supports an eventual storage migration without introducing a managed relational database account now.

Use one API process and one job runner for the initial local application. Persist job requests before returning a job ID. Indexing and evaluation execute outside HTTP request handlers with bounded concurrency. A restart marks an interrupted evaluation as interrupted and permits an explicit rerun; indexing jobs may resume using deterministic vector IDs. Do not claim exactly-once processing or arbitrary horizontal scaling in this phase.

The frontend uses FastAPI APIs through a Vite development proxy. For a local production-style run, build the frontend and serve its assets and SPA fallback under `/admin`, retaining `/docs` and WhatsApp endpoints. API requests authenticate on the server. Add a session-based admin login with password hashing, expiry, secure production cookie settings, and request-origin/CSRF protection for cookie-authenticated mutations. Existing admin endpoints must receive the same protection. Provider credentials remain backend-only and are masked in responses.

## Pinecone migration

Keep local E5 embeddings and existing chunking for the migration comparison. Validate the selected index's dimension and metric before any upsert. Copy the frozen Chroma vectors and metadata into a new migration namespace; do not replace or delete existing Pinecone data merely because the index name matches. Record the namespace and chunk manifest with the experiment.

Compare the copied 95-vector corpus with the legacy benchmark, then compare complete answers using the same input cases and application settings. Search ordering may differ for equal or nearly equal scores; report per-case differences and score changes. A migration succeeds when corpus fidelity, filters, source attribution, and the intended scoring semantics are preserved and any quality differences are understood. It need not increase baseline scores.

Chroma returns cosine distance with smaller values indicating closer matches. Pinecone returns cosine similarity with larger values indicating closer matches. Expose `similarity` and `distance` explicitly, and supply the legacy prompt with cosine distance (`1 - similarity`) when needed to preserve its input. Never reuse the old `similarity_score` label without clarifying what it stores. Pinecone must preserve existing intent filters and the no-results fallback behavior.

New knowledge uses deterministic document and chunk identifiers, source names, content hashes, knowledge version, and existing business metadata. Preserve text, page information when available, intent type, and media references. An embedding-model change creates a separate compatible index and a new evaluation comparison; it cannot update the 384-dimensional index with incompatible vectors.

## Knowledge lifecycle

Each knowledge version has a document manifest and its own Pinecone namespace. Initial migration creates the first published version after validation. Upload, edit, or delete creates a new draft manifest. Reuse vectors for unchanged chunks, embed changed chunks, and populate the draft namespace with the complete version's vectors. This limits re-embedding while keeping published retrieval isolated from candidate changes.

Job states are queued, running, ready, failed, and interrupted. Knowledge versions track draft, indexing, ready, published, and archived states. Readiness verifies expected IDs and query availability with bounded retries to accommodate remote indexing delay. Publish only a ready version, switch the active pointer transactionally, and retain the previous version for rollback. Old namespaces can be removed by an explicit cleanup operation after confirming they are not published or referenced by retained experiments.

Support existing text files first, then Markdown and text-based PDFs using the existing loader capabilities. PDF extraction failures are visible; scanned PDFs requiring OCR receive an unsupported-file explanation. Upload limits and filenames are validated before saving. Arbitrary paths supplied by the browser must never become filesystem destinations.

## Playground and dashboard

Dashboard shows recent activity, response time, errors, knowledge readiness, and the selected published version. Knowledge shows documents, their status, draft changes, chunk previews, indexing actions, and publish/rollback actions. Conversations shows real WhatsApp history, separated from playground and evaluation sessions. Settings shows the answering model, separately configured evaluation judge, retrieval k, embedding identity, and masked provider connection status.

The playground selects published or ready draft knowledge, retains an isolated conversation session, and calls the same RAG service used by WhatsApp. It shows the answer, retrieved chunks, source identifiers, clearly labeled scores, latency, token usage when available, and a LangSmith trace link. Reset affects only that playground session. Candidate settings are explicit per playground session and do not silently change customer settings.

Evaluations shows dataset identity and version, knowledge version, run status, metric definitions, judge and answering model, per-case scores and reasons, failures, local exports, and LangSmith experiment links. Missing results remain missing; failed metric calls must not become zero quality scores. Comparison views distinguish legacy retrieval, single-question quality, and conversational quality.

Use shadcn Sidebar, Card, Table, form controls, Tabs, Dialog, Alert, and appropriate chat primitives from verified registry documentation. Include loading, empty, failure, keyboard, and responsive states. Shared API types should follow the FastAPI response contracts.

## Evaluation datasets and metrics

Retain the original 10-case CSV unchanged. Create a committed rerunnable DeepEval suite with metric instances in `testing/evals/metrics.py`. Use `deepeval test run` for the suite. Use `deepeval generate` against the business knowledge to produce approximately 40 candidate multi-turn scenarios, then mark them as awaiting review. Generated reference outcomes are candidate labels until reviewed for business correctness. Use a deterministic development/evaluation split; held-out cases are not used to select prompts or retrieval settings.

Single-question diagnostics use Faithfulness, Answer Relevancy, and a business-correctness GEval that compares the actual answer with the supplied reference. Multi-turn cases use Turn Faithfulness, Turn Relevancy, Conversation Completeness, and ConversationalGEval for business correctness, with retrieval context attached to assistant turns. Use conversational metric types for conversational cases and single-turn types for single-turn cases. Record initial exploratory thresholds of 0.7 in metric configuration; these are diagnostic thresholds and do not establish real-world suitability without review.

The judge uses OpenRouter with a separate configurable model identifier. Start with `google/gemini-2.5-flash` after checking availability and structured output support; the answering model remains the frozen current setting for the migration comparison. Do not copy a current answering-model change into historical runs. Limit automatic work to one improvement round after the baseline and migration comparison, consistent with the user's approved recommendation.

No numeric spending limit was supplied in the interview. Keep case counts, judge concurrency, retries, maximum output tokens, and the number of rounds explicit and conservative. Expose estimated usage and an optional budget setting. Do not present an estimate or client-side token calculation as a guaranteed provider billing cap. An expanded judged run is an explicit job action; generating candidate scenarios does not authorize repeated unattended optimization loops.

## LangSmith integration

Load tracing environment variables from `.env` into the process before creating LangChain clients. Pydantic reading `.env` alone does not populate the environment the tracing SDK reads. Use the configured tracing flag, endpoint, key, and project. Support an optional workspace ID for organization-scoped credentials when required.

Wrap the shared RAG entry point and retriever with LangSmith tracing. Existing LangChain model calls create child traces. Add channel, knowledge version, prompt/configuration fingerprint, provider/model, and evaluation identifiers as metadata; represent customer session identifiers without exposing phone numbers in trace tags. Include retrieved content and available usage information for diagnostic visibility.

Use LangSmith experiments and a custom evaluator adapter to map DeepEval scores, reasons, thresholds, metric versions, and errors to LangSmith feedback. Associate references and outcomes with dataset examples. Make dataset synchronization idempotent by dataset version and case identifier. Keep application traffic in the configured project and use distinct experiment names for evaluations linked by metadata.

The dashboard obtains trace and evaluation summaries through authenticated backend endpoints; browser requests never receive the LangSmith API key. Keep local result exports for reproducibility. A failed LangSmith upload is reported as a reporting failure and may be retried without invoking the chatbot or judge again. Tracing failures must not prevent customer replies.

The user explicitly selected LangSmith tracing, so DeepEval's own tracing and Confident AI reporting are not part of this implementation. Construct test cases from the real pipeline's recorded outputs and contexts and connect their scores to LangSmith runs. This adaptation follows the user's chosen tracing system.

## Acceptance and validation

1. A rerunnable baseline artifact retains the original dataset, indexed corpus, embeddings, settings, and legacy metric definitions. Generated-answer capture is added before changing the default retriever.
2. Pinecone migration validates dimension and metric, preserves corpus content and filters, isolates its namespace, and produces an explained per-case comparison with the frozen Chroma reference.
3. An upload can be indexed and inspected in a draft playground while published WhatsApp knowledge stays available. Failed indexing cannot publish partial knowledge.
4. Playground, evaluation, and WhatsApp use the same RAG service while keeping conversation records and sessions independent.
5. A DeepEval run records per-case metrics and reasons, exports inspectable artifacts, and links its scores and traces in LangSmith. Reporting retries do not repeat paid evaluation calls.
6. All admin mutations and history endpoints enforce server-side authentication. No provider key appears in browser responses, logs, committed files, or evaluation metadata.
7. Local macOS setup instructions cover Python, frontend development, production-style local serving, indexing, baseline comparison, and `deepeval test run`.

Use meaningful automated checks for namespace selection, draft/publication transitions, dimension mismatch, score conversion, filter behavior, authorization, and feedback mapping. Use a bounded live Pinecone migration check and one judged evaluation run, then inspect the dashboard and playground in a browser. Every evaluation report states the actual dataset size, settings, and limitations.

## Sources and decisions

- [ADR 0001: Pinecone](../../adr/0001-pinecone-vector-store.md)
- [ADR 0002: LangSmith and DeepEval](../../adr/0002-langsmith-tracing-and-evaluation-results.md)
- [ADR 0003: Knowledge publication](../../adr/0003-publish-reviewed-knowledge-versions.md)
- [LangSmith Python SDK tracing configuration](https://docs.langchain.com/langsmith/smith-python-sdk)
- [LangSmith custom evaluation metrics](https://docs.langchain.com/langsmith/metric-type)
- [LangSmith experiment metadata](https://docs.langchain.com/langsmith/filter-experiments-ui)
- [DeepEval OpenRouter integration](https://github.com/confident-ai/deepeval/blob/main/docs/content/integrations/models/openrouter.mdx)

## Implementation evidence — 12 October 2026

The 95 baseline vectors were migrated without re-embedding. Pinecone retained the legacy headline retrieval results (90% Hit Rate@3 and 60% source-file Precision@3). Ten original answers and contexts were captured before switching retrievers. The live Pinecone 10-case DeepEval experiment produced average Faithfulness 0.975, Answer Relevancy approximately 0.907, and Business Correctness 0.57, with feedback uploaded to LangSmith. These are judge scores; the pricing/specification failures remain visible for review.

The shadcn dashboard builds and runs under /admin. A ready draft was indexed and queried in the playground while the published knowledge pointer stayed unchanged. Thirteen offline boundary tests passed; a one-case DeepEval CLI smoke test passed and attached feedback to LangSmith. Forty candidate conversation scenarios were generated using deepeval generate from indexed knowledge contexts and remain awaiting human review. Thirty-two are development scenarios and eight are reserved for final evaluation.

DeepEval 4.2.8 and Chroma 1.5.1 require incompatible PostHog versions, so Chroma was moved to the isolated historical-baseline environment. A small synchronous OpenRouter judge adapter closes its HTTP client explicitly to avoid the SDK's closed-event-loop cleanup warnings. Deployment and live customer WhatsApp delivery are not validated in this local refactor.
