# Retrieval ranking audit — 24 October 2026

This audit separates a reproducible query-construction defect from an unmeasured reranking hypothesis. The query-construction correction below is implemented and covered by offline regression tests. A hosted reranker is a proposed experiment; this document does not claim that it has achieved the precision target.

## Frozen evidence

The inspected result is `35f66aaf15a744dd835aabd63329e471`, saved locally in `/tmp/evaluation-tuned-final.json`, a failed-metric-only scoring retry of `4b2b1b4ec01a47839615742ad4633218`. It uses the `legacy` dataset, top-k 5, the `semantic-bm25-rrf-v1` retrieval recipe, Haiku 5.5 answers and GLM 5.3 Flash scoring. Its knowledge namespace is `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, corpus SHA-256 `a2f9e7365454bcb8ac069fe599276bec21eca7d5179f553a68c8bcdb7a27ca49`.

All four metrics have ten scores. Means are Faithfulness 100.00%, Answer Relevancy 100.00%, Contextual Recall 86.67%, and Contextual Precision 76.44%. These are ten-case benchmark means, not production accuracy or calibrated confidence.

| Case | Query task | Contextual Precision | Evidence in the returned five chunks |
| --- | --- | ---: | --- |
| 1 | Physical store location | 50.00% | Actual addresses are rank 2; contact numbers rank 1. |
| 2 | Payment/DP | 100.00% | Payment rules and ordering requirements rank 1–2. |
| 3 | Waterproof sticker labels | 100.00% | The judge accepts all five material/price chunks. |
| 4 | Accepted file formats | 100.00% | Four relevant chunks precede the irrelevant one. |
| 5 | Flexi 280 banner, 2 × 1 m | 63.89% | X-Banner package is rank 1; per-m² price and calculation are ranks 2–4. |
| 6 | Shop-caused print defects | 20.00% | Reprint warranty is rank 5; customer-file exclusion is rank 2. |
| 7 | Three Flexi 280 banners | 100.00% | Formula, per-m² price, and calculation example occupy ranks 1–3. |
| 8 | 5 × 5 cm stickers per A3+ | 80.56% | Generic sticker pricing interrupts the relevant quantity/formula chunks. |
| 9 | Business cards plus X-Banner | 100.00% | The judge accepts all five package/price chunks. |
| 10 | Outdoor window sticker material | 50.00% | A general applications chunk precedes the material recommendation. |

The primary saved trace for case 1 is [the answer run in LangSmith](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/93a921a2-9a85-490d-ae7e-aa92b11bee3c/trace/01a169d1-1e32-76f0-b72f-df036ffc0733/run/01a169d1-1e32-76f0-b72f-df036ffc0733?start_time=2026-10-23T17%3A31%3A14.866713%2B00%3A00).

## Verified query dilution

`app/backend/chain.py` sends `retrieval_question(question, history)` into `similarity_search_with_score`. Before this correction, `app/backend/history.py` treated any occurrence of `cabang`, `alamat`, `lokasi`, or `terdekat` as an ordering handoff. It appended:

```text
Informasi untuk langkah berikutnya: lokasi cabang, alamat, tautan Maps, kontak admin dan alur pemesanan.
```

Consequently, a first-turn request for a physical address also searched for contacts and ordering procedures. A request for a branch email address received the same expansion. Independently, any follow-up after an assistant message mentioning `cabang` received the expansion, even when the customer asked a new contact-information question.

This defect was reproduced without external calls. Five address/contact first-turn variants and three information questions after a branch offer failed against the old implementation. Existing actual-handoff tests passed.

The correction removes location/contact nouns as unconditional handoff triggers. Explicit booking, approval, continuation and ordering requests retain the handoff expansion. After a branch offer, numeric/acceptance replies, explicit branch selection, or a branch label actually offered in the assistant's message retain it. Previous customer messages continue to provide bounded product/quantity context. The implementation contains no benchmark questions, product names, branch names, or expected answers.

The regression tests verify the public query-construction boundary. With both query corrections in this audit, `testing/test_retrieval_history.py` and the existing offline print-inquiry tests have **22 passing cases**. One database-backed print-inquiry audit test was excluded from this focused run because disposable PostgreSQL on loopback port 54585 was not running. The tests establish task preservation and retained handoff behavior; live retrieval and metric changes still require the full controlled comparison.

## Product/intent metadata and lost conversation context

A read-only inspection of the active database snapshot confirmed 139 chunks from five sources: 11 SOP/policy, 29 materials/finishing, 16 artwork-file guidance, 75 pricing, and eight A3+ quantity-guide chunks. All 139 carry `source`, `format`, `answer_source`, `source_id`, `document_id`, `section_1`, `section_2`, and `chunk_index`; nine carry `section_3`. None carries `product_id`, `product_ids`, `product_type`, or `intent_type`.

This matches `app/admin/global_knowledge.py::documents`: production text sources receive provenance and heading metadata, not image-catalog product tags. `app/admin/catalog.py::PRODUCTS` and the image assets' positive/negative keywords form a separate vocabulary. They do not filter the factual knowledge retrieval. The catalog's `banner-spanduk` aliases include `flexi`, while standing-banner package passages also contain Flexi materials; that word alone is not a safe discriminator. The factual sources already distinguish per-m² banner printing from fixed X-Banner packages and shop-production responsibility from customer-file exclusions. Specific section headings and body evidence should retain these distinctions.

`product_intent.extract` permits factual discussions to establish a product with `action='none'`. Its prompt explicitly requires generic sticker families to remain ambiguous when subtype/focus is unknown. The schema validates recognized IDs and response shape, not the semantic correctness of the product assignment. A wrong resolved ID could still bias the query; held-out model traces are required before claiming that product classification is accurate.

The chain contained a second reproducible query-construction defect: after building a history-aware search question, it replaced that entire question with the current message plus product labels whenever the intent returned resolved product IDs. A material follow-up after an order with known dimensions and quantity therefore lost those specifications:

```text
Previous customer: Stiker 5 x 5 cm sebanyak 100 pcs
Current customer: Vinyl saja
Old retrieval query: Vinyl saja\nProduk yang dimaksud: stiker a3
```

The public `RAGChain.run` regression reproduced the loss with a valid nonvisual resolved intent. The one-line correction appends product labels to the already-constructed query. Dimensions, quantity, previous customer context, and actual handoff expansion remain available. This does not change the semantic classifier, inject a product-specific rule, or convert image metadata into factual answer context.

## Remaining ranking limitations

1. **RRF cannot resolve semantic distinctions it never scores.** In case 1, the contacts chunk has semantic rank 1 and lexical rank 2; addresses have semantic rank 2 and lexical rank 1. Equal-weight RRF with constant 60 yields exactly the same fused score, so the stable tie-break keeps contacts first. A query–passage model can consider whether the body actually supplies a location.
2. **Shared breadcrumbs mask body differences.** Both address and contact chunks repeat `PROFIL DAN LOKASI CABANG TOKO`. Lexical scoring counts these title terms even for a contact-only body. Source subsections should describe their actual contents; this is a source/chunk audit issue, not a reason to fabricate relevance labels.
3. **Lexical matching treats exclusions as matches.** X-Banner text explicitly says it is not a per-metre banner, yet it contains overlapping `banner`, `Flexi`, and `280` terms. Keyword overlap does not interpret the difference between per-m² printing and a fixed frame package.
4. **Responsibility matters for warranty questions.** Case 6's genuine shop-production warranty was semantic rank 11 and lexical rank 2, then fused to rank 5. The customer-file exception was semantic rank 9 and lexical rank 1, then fused to rank 2. They share policy words but answer contrasting causes. A ranker should score the actual question against both bodies without removing the exclusion from the corpus.
5. **Candidate membership and ordering are different interventions.** Reordering the same five chunks preserves their content coverage. Reranking the wider twenty-candidate pool may improve recall but can also remove useful material. Measure both precision and recall; keep the candidate pool and retained top-k explicit in provenance.

## Reranker implementation seam

The narrow shared seam is the end of `app/backend/vectorstore.py::similarity_search_with_score`, after document construction and fusion. WhatsApp, Playground and evaluations already use this method. The existing Pinecone client is version 7.3.0; introspection confirms its `inference.rerank(model, query, documents, rank_fields, return_documents, top_n, parameters)` interface is available without adding a dependency.

[Pinecone's official guide](https://docs.pinecone.io/guides/search/rerank-results) describes the two-stage workflow: retrieve a wider pool, then score each candidate against the query and return a smaller set. It identifies `bge-reranker-v2-m3` as a multilingual model for short queries and medium-length passages, supporting at most 100 documents and 1,024 tokens per query/document pair. Current chunks are roughly 1,000 characters, but long conversational queries still need a bound. The guide's larger Cohere model is an alternative to evaluate, not a reason to silently change the chosen reranker mid-run.

The [standalone endpoint](https://docs.pinecone.io/reference/api/2026-04/inference/rerank) accepts original document IDs and returns indices plus relevance scores. Use returned indices to select the original immutable documents; retain original cosine distances and store reranker scores separately. Do not relabel a reranker score as cosine similarity or introduce a confidence threshold from an unrelated model.

The installed SDK's `rerank` convenience method has no timeout argument and invokes its generated API directly. A bounded request through the already-installed `requests` client is a possible adapter when a request deadline is required. Neither API readiness nor billing access was probed by this read-only audit.

Recommended failure handling is a bounded rerank attempt with an explicit observed fallback to the fused ranking. Validate unique indices, range, finite scores, and expected result count. Record model, candidate count, top-k, recipe, rerank/fallback status and latency so a successful answer cannot conceal that the reranker failed.

## Verification required for the experiment

- Freeze dataset/reference hashes, answer model, prompt, judge model/rubric/settings, and top-k for before/after runs. Record a separate knowledge snapshot whenever corrected source documents are activated through Sync knowledge.
- Compare per-case retrieved IDs/text and relevance reasons, not only aggregate scores. A changed relevant/nonrelevant judge verdict is distinct from a changed order.
- Test held-out phrasing and contrasting intents: physical address versus email/contact; per-m² banner versus X-Banner package/frame; operator error versus customer-file error versus unknown cause; outdoor window durability versus one-way visibility; quantity-per-sheet versus sticker price.
- Keep thresholds fixed and preserve difficult cases. Audit the judge's treatment of borderline faithfulness and apparently permissive relevance verdicts separately from retrieval optimization.
- Mock malformed indices, duplicates, partial responses, nonfinite scores, transport errors and permanent HTTP errors in offline adapter tests. Verify no document/distance mutation, no lost namespace/filter, empty input behavior, and deterministic fallback.
- Measure answer grounding and completeness, contextual recall, scoring coverage/errors and added retrieval latency. The ≥87% precision target remains an empirical optimization target.
