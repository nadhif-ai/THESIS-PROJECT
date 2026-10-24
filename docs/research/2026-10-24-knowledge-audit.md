# Knowledge and chunking audit, 24 October 2026

## Observed state and scope

This audit read the configured administration store, the active snapshot, retained source text, repository documents, and ingestion/retrieval code. It made no database or Storage changes and no paid model calls. Source edits and activation are separate operator work; this report does not claim that the recommendations are active.

The active snapshot at inspection was `kb-ecaf24265cfa46cab72f1d24f2c29ce0`, published on 22 October 2026 at 22:57:49 UTC. Its namespace is the same identifier. Source revision and applied revision were both **10**, `pending=false`, and no sync job was running. The snapshot contains **139** factual passages. The six source files include a navigation-only menu, which is not embedded.

- Corpus SHA-256: `a2f9e7365454bcb8ac069fe599276bec21eca7d5179f553a68c8bcdb7a27ca49`.
- Chunking: `sections-v1`, 1,000 characters, overlap 100.
- Embeddings: OpenRouter `nvidia/nemotron-3-embed-1b:free`, 2,048 dimensions, L2 normalization, `nvidia-query-passage-v1` input contract.
- Pinecone index: `chatbot-nadhif`; cosine compatibility is checked by the application.

Exact UTF-8 source exports, inventory, the original snapshot, and the isolated chunking diagnostic were saved privately under `/tmp/rag-knowledge-before/` (directory mode 0700, files 0600). Every exported text hash matches its registered source blob hash. These temporary exports are not repository artifacts. The snapshot and source revision were checked again after export and had not changed.

## Source inventory

| Source | Source ID | Blob ID | SHA-256 | Indexed passages |
| --- | --- | --- | --- | ---: |
| `01_sop_dan_kebijakan_toko.txt` | `ae2852bc51ff4b588bee4ec0de5a1618` | `5bc37d8ea2454457b78a0cdb9d51a0fe` | `31bc29dd769d698d0e9988f8d12dd26757a5303348fd441fba8295022f965fdc` | 11 |
| `02_spesifikasi_bahan_dan_finishing.txt` | `37cfa02e3aac466b9a806aa2bd465fd3` | `08c1192e03e34507a46dbbee648be248` | `448fc0a469256712acda22d22aea4a674210b828a3e0761260ed5ee38d4a7352` | 29 |
| `03_panduan_berkas_siap_cetak.txt` | `6e21c4942b07464a9285ad8d7d1f8cec` | `b457cbf47b594baf9d444694eab014a8` | `10b06892b01ddbae064bef3c52d0127fe7fe797ccbd2c28c04c14c6dd81bb19d` | 16 |
| `04_daftar_estimasi_harga.txt` | `36f51e8a65d64ff8b782187c47b68720` | `ff4d8c8f9e374501a2e53233f7005d9c` | `048fc683a95b9c5884d01348770f2a815a51d5bd998766dbff6249bc2f67b048` | 75 |
| `05_daftar_pertanyaan_populer.txt` | `dd49dc2700a64546a995be35e6474b60` | `df1f3c1e3ab64a87b2d01a65ebb3779e` | `e87bc03eed420c15b4e84303d2e5bb2cc821c23fd77d1dc26a6e4fab4f2fb8ca` | 0 |
| `06_estimasi_pcs_per_lembar_a3.txt` | `aea30213c78a4e5d819d2ae2dd199069` | `661be36113044f5d99284977547c0fe8` | `d072075361d140e615738d90ac73640a9e2a767014f7edcffdf3998e5ddd2181` | 8 |

## Findings and evidence-backed changes

### Physical locations and contact information share one retrieval heading

SOP lines 4–25 combine a company description, two physical addresses/maps/landmarks, file-submission emails, WhatsApp numbers, office telephone, and social accounts under `1. PROFIL DAN LOKASI CABANG TOKO`. The active splitter produces:

- Chunk 0, `8f3a03e8ac002732361822836e734a49fb2bb6a1d7b373585511bb40aee17dd3`: both physical addresses plus the beginning of the contact heading.
- Chunk 1, `d15c478a580fc0f74a16aa549d04e7e66d49e47a93a4888b326d137caba92e48`: file-submission email and contact channels, still labeled as the location section.

The locations already exist in the source: Ciputat Timur at **Jl. Ir. H. Juanda No. 17** and Pamulang at **Jl. Pajajaran No. 38**, with distinct maps, landmarks, and emails. No new address is needed. Use separate semantic headings for each physical branch and for contact/file submission. A location query can then rank an address passage rather than a contact passage that inherits a location label. Keep the two branch addresses and their branch associations intact. A generic location question should not silently assert that only one branch exists.

**Source drift to preserve:** active SOP line 20 has `0896-9241-1115`; repository line 20 has `0896-3241-1115`. The live source was edited on 22 October; the repository material predates that edit. This audit does not independently certify either phone number. Derive the replacement from the retained live source and preserve its phone value, rather than uploading the repository file wholesale.

### Shop production errors and customer-file errors are split apart

SOP lines 87–95 combine cancellation, refunds, and reprints. Active chunk 9 (`cd24d7fab4a812d9dede0daac4d25f11bb780b74e483cbf96882063d742aa94b`) contains cancellation, refunds, and the positive shop-fault reprint policy. Chunk 10 (`de1e23c0cdde08a3f56ee3e4fa6cd21eef40b973eae7e41aa6bdc2391dd9d8e6`) contains only the customer-fault exclusion, under the same mixed heading.

The source says shop/operator mistakes such as the wrong size/material, a printing-machine defect, or severe streaking qualify for free reprinting with physical evidence returned to the shop. It separately excludes free replacement for customer design/typing mistakes, the customer's wrong file dimensions, or an originally blurry file. These are already supported facts, not a new warranty.

Give cancellation and refund their own headings, and place both sides of the reprint distinction in one coherent `Garansi dan cetak ulang` subsection. Preview with the unchanged 1,000/100 budget to ensure the shop-fault condition, customer-fault exclusion, and physical-proof requirement remain together. Do not shorten the policy to “all wrong prints are free” or “all design mistakes are excluded” without identifying who caused the error. Preserve the original cancellation/refund facts in their own sections.

### Banner printing per square metre and X-Banner packages are different products

Price source lines 7–21 define banner/spanduk printing by area: length × width × price per m² × copies, with rounding to Rp 500. Flexi China 280 GSM standard is **Rp 16.500/m²**; high resolution is **Rp 25.000/m²**. Lines 41–52 define the **60 × 160 cm X-Banner package including the frame**, with Flexi China 280 GSM at **Rp 50.000/package**. The specifications source lines 96–105 independently describes the X-shaped frame and package contents.

Active price chunk 0 (`8590803c75def8ccd54833fd9091309f76e7e7a127a9d349a10d3496105104ed`) contains the banner area formula and standard rates. Chunk 3 (`cc07ccebec44aabf870a2780aced358cc8d10921ec113eb5335a35d826d565f0`) contains the X-Banner package. The latter also contains “BUKAN spanduk meteran”; simple token matching can reward the shared words without understanding the negation. Both facts are present: this is primarily a ranking/disambiguation problem, not missing pricing knowledge.

Use clear section names and preserve the pricing unit, product form, quality tier, dimensions, and inclusion of the frame. Explain the general distinction once in the source, rather than inserting the exact benchmark question or hard-coding a 2 × 1 m exception. A reranker should assess which passage answers the query and should recognize explicit package-versus-meter distinctions. Avoid a hard product filter until ambiguous customer wording is validated: a generic “banner” inquiry can legitimately require clarification.

The price document also duplicates the Y-Banner and Roll Up price sections at lines 518–542 after the fuller sections near the start. Rates match in this inspected text. These partial duplicates can occupy candidate positions. Consolidation is reasonable only after checking every unit, size, tier, frame-only option, and unique detail; deleting whole blocks without that comparison risks losing facts.

### A separator comment overwrites useful header metadata

The original preprocessing removed standalone `---` lines, but not `# -----`. `MarkdownHeaderTextSplitter` therefore interpreted comment separators in source preambles as real level-one headings. **83 of 139** active passages have `section_1="-----------------------------------------------------------------------"` and repeat that separator in their embedded text. Price source line 5 and sticker-estimate source line 3 reproduce the defect. A synthetic price source reproduced the same loss of title before the fix.

The corrected recipe is explicitly **`sections-v2`**. It removes bare or heading-prefixed separator-only lines before Markdown parsing and retains real headings, prices, dimensions, and units. `sections-v1` is retained for explicit historical reconstruction. The global ingestion function forwards the recorded preprocessing identifier; configuring new chunking through the authenticated API stages `sections-v2`. New legacy-style drafts use the new recipe, while re-indexing an existing explicit v1 draft retains v1.

Isolated diagnostic on the exact original source text, with no business-content edits:

| Source | Frozen v1 passages | Corrected v2 passages |
| --- | ---: | ---: |
| SOP | 11 | 11 |
| Materials/finishing | 29 | 29 |
| Print-ready file guide | 16 | 16 |
| Prices | 75 | 74 |
| Sticker estimates | 8 | 8 |
| Total factual passages | **139** | **138** |
| Passages whose level-one heading is only a separator | **83** | **0** |

Explicit v1 reconstruction reproduces **all 139 frozen passage texts exactly**, compared as multisets. Corrected v2 passages have a maximum of 999 characters. Changed prefix length can change boundaries even with identical character/overlap settings; this is a real snapshot change and must be recorded in comparisons. No retrieval-score improvement follows from this structural diagnostic alone.

**Remaining source-level issue:** several consecutive `#` lines in the price preamble are valid Markdown headings. After separator removal, the last meaningful line, “Untuk konfirmasi harga terkini, silakan hubungi admin toko.”, still becomes the level-one heading. Normalize the preamble to one true document title with other metadata as ordinary text. The generic parser must preserve real Markdown headings; it should not guess which informative heading is merely a comment.

### Live sticker knowledge reintroduced an already reviewed contradiction

The live file guide line 122 says 5 × 5 cm Kiss Cut yields **35 pcs/A3+**, while live estimate source line 42 says **40** for machine Kiss Cut and **54** for manual cutting. The estimate source also uses a grid formula; price source lines 965–1001 apply that formula to Kiss Cut, including a 3 × 3 cm example giving 126, whereas the file guide's official table says 108.

This difference is not resolved by selecting whichever number raises the metric. The prior reviewed correction is documented in [the 12 October research record](2026-10-12-small-corpus-rag-chunking.md#koreksi-bisnis-setelah-konfirmasi-pengguna), lines 82–90: the user confirmed **35 pcs for 5 × 5 cm Kiss Cut**, preserved manual estimates, removed the conflicting duplicate Kiss Cut grid/table, and retained historical artifacts. Repository files 03/04/06 contain that correction, but the inspected active global source files do not.

Reapply that already documented correction through staged replacements of 03/04/06, preserving unrelated live edits. Keep the official Kiss Cut table distinct from theoretical/manual capacity. For a question that omits the cutting method, explain the dependency or ask for it; do not advertise all methods as sharing one capacity. Record this as a factual corpus correction, separate from reranking, and retain the old snapshot for provenance.

### Product-image metadata is not pricing authority

Global factual passage metadata currently includes source/blob identifiers, headings, ordinal, format, and `answer_source`. It does not carry canonical product IDs, pricing units, branch IDs, or error-causing party. The structured product-intent classifier supplies product labels to the retrieval query; it does not create verified factual metadata for passages. Image catalog metadata describes approved illustrations and supported product vocabulary, and explicitly excludes prices from captions.

A semantic reranker can use the question and source text without inventing new business facts. If structured metadata is later added, derive it from reviewed source sections, version it with the snapshot, and validate uncertain classifications. Do not use illustrative catalog attributes as evidence of exact stock, prices, or warranty eligibility.

## Existing staged replacement and activation workflow

1. Start with the exact exported live source texts and record their source IDs/hashes. Modify only supported facts/structure. Review a diff that preserves the live phone value, addresses, maps, prices, conditions, and unique product details.
2. Use the existing source replacement flow with the original `source_id`: request an upload ticket, upload a new private original, then complete the upload. The frontend's **Save text** action uses this same replacement flow. `kb_store.finish_upload` updates the staged source reference and increments the revision; it does not alter the active pointer.
3. Stage 1,000/100 with `preprocessing=sections-v2` through the existing configuration path. Preview extracted source text and all resulting passages before starting the sync. Confirm addresses versus contacts, both warranty conditions, tariff units, and official Kiss Cut values are present in coherent passages.
4. Invoke **Sync knowledge** once. `start_sync()` freezes enabled sources, hashes, chunking, revision, embedding identity, and index in the durable job. Source mutations are locked for the duration of the sync.
5. The durable worker prepares a separate `kb-<job_id>` snapshot/namespace, embeds with fixed Nemotron 2,048 dimensions, upserts stable vector IDs, verifies the complete vector-ID set, and performs a retrieval probe. It must not mutate the old namespace in place.
6. Activation requires the live job lease, matching `sync_job`, and the original revision. It atomically publishes the new snapshot and updates the active pointer and applied revision. Failed syncs leave the previous active snapshot selected. Evaluations submitted at this boundary pin one unambiguous snapshot using the same state lock.
7. Record old/new snapshot IDs, corpus hashes, source hashes, passage counts, and preprocessing identifiers. Verify the completed sync job and new active pointer, then run fixed-condition answer/scoring comparisons and held-out contrasting intents. Do not label a snapshot/corpus correction as a pure ranking ablation.

Implementation references: `app/admin/global_knowledge.py` (`documents`, `sync_step`), `app/admin/kb_store.py` (`finish_upload`, `start_sync`, `create_evaluation`, `activate`), `app/admin/knowledge_routes.py`, and `frontend/src/components/knowledge-page.tsx` (`uploadFile`, Save text, Sync knowledge). The accepted global knowledge contract is [single-knowledge-base.md](../single-knowledge-base.md).

## Verification of the isolated code change

- Regression test first failed because the separator replaced the real source title, then passed with `sections-v2`.
- Historical-version test first failed when old configuration silently used the corrected algorithm, then passed after propagating the recorded recipe.
- Explicit v1 reconstruction matched every original passage; no active record was rewritten.
- Focused offline checks: `LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_knowledge_chunking.py testing/test_global_knowledge.py testing/test_admin_workflow.py -q` passed **44 tests**. The API test verifies authentication and CSRF, stages the new recipe without an active snapshot change, and rejects invalid overlap without changing the staged configuration. Database fixtures created disposable `chatbot_test_*` databases only on loopback port 54585; no tests used the configured administration store.

Activation, paid-provider evaluations, held-out answer quality, and resulting Contextual Precision remain separate evidence requirements. The structural fix alone does not prove the ≥87% optimization target.
