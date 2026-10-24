# Knowledge content change audit, 24 October 2026

## Finding and scope

**Knowledge source content was edited.** Through the original 139-passage snapshot, the preceding 142-passage precision snapshot, and the pre-restoration 141-passage recall snapshot at revision 16, administered files **01, 04 and 06 changed**. Files **02, 03 and 05 did not change through revision 16**. The recall-cohesion intervention changed **01 only**.

**Current follow-up: revision 18 is activated with 142 passages.** After the user confirmed the three removed technical facts, source06 restored them and source02's stale cross-reference was repaired. Across the whole sequence, **four files changed: 01, 02, 04, 06**. Sources **03 and 05 remain unchanged**. The [activated restoration follow-up](#activated-restoration-follow-up-revision18) below distinguishes this current state from the dated revision 16 audit and its frozen evaluation snapshot.

The latest SOP01 reorganization conserves its existing business facts. That verified claim must not be extended to the entire earlier 04/06 cleanup: those replacements removed conflicting Kiss Cut estimates **and additional technical descriptions absent from the active corpus at inspection**. Describing the complete work as only a layout change, as removing only duplicates, or as preserving every item of content would be inaccurate.

This report compares retained exact original texts, frozen replacement artifacts, their provenance ledgers, and read-only administration-store results. The live catalog was checked on **24 October 2026 at 10:41:29 Asia/Jakarta**. Each active extracted source text hashes to its registered SHA-256. No database, Storage, administered knowledge-source or runtime changes were made for this audit; no provider or evaluation calls were made.

**Subsequent user validation, 24 October 2026:** the user confirmed that the 29×42 cm effective machine area, 1–2 cm registration/sensor allowance, and half-cut/backing-intact definition are all valid. The [restoration set](../../dataset/knowledge-revisions/2026-10-24-restoration/README.md) was prepared from exact revision16 source02/06 hashes and subsequently activated through existing private upload/finish and durable Sync services at **11:01:49 Asia/Jakarta**, after the active evaluation's scoring freeze. This is user-supplied business confirmation rather than an independent machinery test. The dated audit findings retain their original revision16 scope; the subsequent revision18 activation is recorded separately and does not rewrite completed evaluation evidence.

## Active state and snapshot boundaries

| Stage | Snapshot and namespace | Source revision | Preprocessing | Factual passages |
| --- | --- | ---: | --- | ---: |
| Original screenshot state | `kb-ecaf24265cfa46cab72f1d24f2c29ce0` | 10 | `sections-v1` | 139 |
| Preceding precision baseline | `kb-0a4b41713f9e423799b20387bda6597b` | 15 | `sections-v2` | 142 |
| Recall state at 10:41 inspection; frozen evaluation snapshot | `kb-e622863bb58d4137b4e8bf7cf62a186e` | 16 | `sections-v2` | 141 |
| Current activated restoration | `kb-84668f0b823a402cbe360c2c711bd766` | 18 | `sections-v2` | 142 |

At the **10:41:29** read-only inspection, `revision=16`, `applied_revision=16`, `pending=false`, and `sync_job=null`. All **six sources were enabled**; no source was deleted. Original and intermediate snapshots were stored with status `ready`; revision 16 was then `published`. This is the preserved pre-restoration observation. The later completed restoration has `revision=18`, `applied_revision=18`, `pending=false` and 142 verified passages; revision 16's namespace remains retained. Historical passage records were not rewritten in place.

Chunk size **1,000**, overlap **100**, fixed Nemotron/OpenRouter embeddings, **2,048 dimensions**, and cosine remain unchanged. The v2 preprocessing removes separator-only lines such as `# -----` before Markdown header parsing; it retains real titles, prices and units. Explicit v1 behavior remains available for historical reconstruction. Parser prefix and section-boundary changes affect passage counts, so the 139→142→141→142 sequence is not a count of business facts added or removed.

| Source filename | Original139 | Precision142 | Recall141, rev16 | Restored142, rev18 |
| --- | ---: | ---: | ---: | ---: |
| `01_sop_dan_kebijakan_toko.txt` | 11 | 15 | 14 | 14 |
| `02_spesifikasi_bahan_dan_finishing.txt` | 29 | 29 | 29 | 29 |
| `03_panduan_berkas_siap_cetak.txt` | 16 | 16 | 16 | 16 |
| `04_daftar_estimasi_harga.txt` | 75 | 75 | 75 | 75 |
| `05_daftar_pertanyaan_populer.txt` | 0 | 0 | 0 | 0 |
| `06_estimasi_pcs_per_lembar_a3.txt` | 8 | 7 | 7 | 8 |

Source05 remains navigation-only material, intentionally excluded from factual embedding. Its zero passages do not mean it was deleted.

## Exact file-by-file changes

### 01_sop_dan_kebijakan_toko.txt

**Original139 to precision142:**

- Renamed `1. PROFIL DAN LOKASI CABANG TOKO` to `1. PROFIL TOKO DAN CABANG`.
- Added physical-address/map/landmark headings for Ciputat Timur and Pamulang. The existing addresses, maps, landmarks and emails were retained.
- Added a contact/social heading and the explanatory sentence: `Kontak berikut adalah sarana menghubungi toko; alamat fisik dan tautan peta tercantum pada masing-masing cabang.`
- Added separate headings for cancellation before production, refund, shop/production-fault reprinting, and customer design/file-error exclusions. Existing policy text was retained; these headings did not create new refund or warranty entitlements.

**Precision142 to recall141, revision16:**

- Moved both full branch addresses, both map links, both landmarks, and all customer hours/order cutoffs into `KUNJUNGAN GERAI: ALAMAT, PETA DAN JAM LAYANAN`.
- Reformatted branch identification and schedule wording while preserving values and conditions.
- Moved the two submission emails into a separate section that retains their branch associations.
- Retained the complete contact block verbatim, including the newer live Admin1 number **0896-9241-1115**.
- Separated staff shifts into `2. SHIFT KERJA DAN PELAYANAN STAF`. The three-shift sentence and staffed-break coverage remain verbatim, with their original Monday–Saturday scope retained.
- Preserved **all source text from section 3 to the end byte-for-byte** relative to precision142, including ordering/collection, production estimates, payment, cancellation/refund and warranty.

The preserved customer hours are Monday–Saturday **08.30–02.30**, close order **01.30**, with completion/pickup only after 01.30; Sunday **09.00–21.00**, close order **20.30**; national holidays other than Friday **12.00–21.00**; and Friday national holidays **13.00 after Friday prayers–21.00**. No tariff, address, phone, deadline or policy number was changed in this latest SOP replacement.

The resulting visitor passage is **981 characters**, including its heading prefix. The SOP now has 14 passages, with a maximum length of 985 characters. The [17-check fact-conservation ledger](../../dataset/knowledge-revisions/2026-10-24-recall/provenance.json) and [exact splitter proof](../../dataset/knowledge-revisions/2026-10-24-recall/chunking-proof.json) are scoped to this latest SOP01 change.

SOP01 remained unchanged in the subsequent revision18 restoration.

Before/after evidence: [original139 private export](/tmp/rag-knowledge-before/01_sop_dan_kebijakan_toko.txt), [precision142 replacement](../../dataset/knowledge-revisions/2026-10-24/01_sop_dan_kebijakan_toko.txt), [recall141 replacement retained in revision18](../../dataset/knowledge-revisions/2026-10-24-recall/01_sop_dan_kebijakan_toko.txt).

### 02_spesifikasi_bahan_dan_finishing.txt

**Unchanged through the first three snapshots, ending at revision16**, including its blob ID, extracted text and hash. The later revision18 restoration replaced exactly one cross-reference line; all remaining source02 text is byte-identical. Existing material/product definitions were not rewritten.

At the revision 16 inspection, original line 141 was stale and still said:

> Rincian lengkap dan tabel estimasi jumlah stiker per lembar A3+ (metode Kiss Cut Mesin dan Potong Manual Karter) dapat dilihat pada dokumen resmi: `06_estimasi_pcs_per_lembar_a3.txt`.

At revision16, source06 contained manual estimates only and directed Kiss Cut counts to source03. The earlier replacement had not corrected the source02 sentence. Revision18 now uses:

> Tabel acuan resmi jumlah pcs stiker Kiss Cut per lembar A3+ terdapat pada `03_panduan_berkas_siap_cetak.txt`. Informasi proses Kiss Cut dan tabel estimasi jumlah pcs Potong Manual Karter terdapat pada `06_estimasi_pcs_per_lembar_a3.txt`.

Evidence: [original export unchanged through revision16](/tmp/rag-knowledge-before/02_spesifikasi_bahan_dan_finishing.txt), [revision18 replacement](../../dataset/knowledge-revisions/2026-10-24-restoration/02_spesifikasi_bahan_dan_finishing.txt), and [restoration conservation proof](../../dataset/knowledge-revisions/2026-10-24-restoration/provenance.json). The older [repository source02](../../dataset/knowledge_base/02_spesifikasi_bahan_dan_finishing.txt) still matches the original export and retains the former cross-reference; it is no longer a mirror of active source02.

### 03_panduan_berkas_siap_cetak.txt

**The administered original was unchanged across all four snapshots**, including blob ID and hash. Its existing section 9 official Kiss Cut table remains the source used by the replacements, including **5×5 cm = 35 pcs/A3+** and **3×3 cm = 108 pcs/A3+**. The table was not newly invented or altered during this work.

The older repository copy differs from this administered original. In particular, the repository has a prior historical reorganization of the 5×5 answer; that local form was not uploaded in the observed replacement sequence. Do not describe local source03 changes as a current administered replacement.

Evidence: [unchanged administered export](/tmp/rag-knowledge-before/03_panduan_berkas_siap_cetak.txt), especially section 9; [initial live-source audit](2026-10-24-knowledge-audit.md#live-sticker-knowledge-reintroduced-an-already-reviewed-contradiction).

### 04_daftar_estimasi_harga.txt

**Changed in the preceding precision work; unchanged in the recall-cohesion and subsequent restoration work.**

- Changed `Berlaku untuk kedua cabang`, currency/price-change metadata, contact-for-current-price text, and the separator in the preamble from Markdown level-one headings into ordinary text. Their wording was retained, leaving the real document title as a title.
- Added a general statement that banner/spanduk prices in the first section are **per square metre**, whereas X-Banner is a **print-plus-frame package**. Existing product prices and units remain: for example, Flexi China 280 GSM standard spanduk is Rp16,500/m², its HR option is Rp25,000/m², and the Flexi China 280 GSM X-Banner 60×160 cm package is Rp50,000.
- Replaced the Kiss Cut `29 cm ×42 cm` area instruction in the A3 calculation guide with a direction to the official source03 capacity table.
- Restricted the straight-grid formula and corresponding calculation steps to **manual cutting**. For Kiss Cut, the revised steps explicitly use source03 and warn against treating both methods as having equal capacity.
- Removed the former example for **500 pcs, 3×3 cm Cromo Kiss Cut**, calculated as 126 pcs/sheet, four sheets, Rp50,000. Source03 already says 108 pcs/sheet, so the old example's capacity and resulting sheet-count estimate conflicted with the retained official table. The Rp12,500 sheet tariff itself was not changed; deletion of a derived illustration is not a tariff change.
- Retained the other examples and tariff text. Existing duplicate Y-Banner and Roll Up price sections were not consolidated by these replacements.

The earlier capacity correction is distinct from the latest SOP01 cohesion change. The record of prior business confirmation concerns official capacities, particularly the 5×5 Kiss Cut answer; it does not independently certify every removed description of the cutting process.

Before/after evidence: [original139 private export](/tmp/rag-knowledge-before/04_daftar_estimasi_harga.txt), [active replacement](../../dataset/knowledge-revisions/2026-10-24/04_daftar_estimasi_harga.txt), and [precision provenance](../../dataset/knowledge-revisions/2026-10-24/provenance.json).

### 05_daftar_pertanyaan_populer.txt

**Unchanged across all four snapshots**, including blob ID, extracted text and hash. It remains the navigation-only menu. No FAQ source was deleted or replaced.

Evidence: [unchanged original export](/tmp/rag-knowledge-before/05_daftar_pertanyaan_populer.txt); [matching local copy](../../dataset/knowledge_base/05_daftar_pertanyaan_populer.txt).

### 06_estimasi_pcs_per_lembar_a3.txt

**Changed in the preceding precision work; unchanged in the recall-cohesion work through revision16.**

- Retitled and scoped the guide to **manual cutting**; changed headings and example questions accordingly.
- Added a direction to the source03 official table for Kiss Cut, stating that manual quantities do not apply to Kiss Cut.
- Removed the entire Kiss Cut grid-capacity column from the square and rectangular tables. For example, the old source06 said 5×5 Kiss Cut = 40 whereas source03 says 35; source06 said 3×3 Kiss Cut = 126 whereas source03 says 108.
- Preserved **all 42 manual size/capacity pairs exactly**: 24 square and 18 rectangular entries. This was checked by extracting and comparing the size→manual-count mappings. Manual 5×5 remains 54, along with the 31×47 manual area and grid formula.
- Removed the Kiss Cut introductory subsection, including the additional descriptions listed below. Kept the manual straight-through cutting description, square/rectangular suitability, custom-cut fee Rp25,000 and above, and instruction to consult the admin for exact design-specific quantities/prices.
- Removed source06's repeated Kiss Cut restriction to circles/simple shapes and exclusion of lettering. Those restrictions remain in source04's cutting-policy section; their removal from06 did not remove them from the corpus.

**Revision 16 to activated revision 18:** updated the title/subtitle to reflect process information plus manual estimates, and restored the three user-confirmed process facts in a standalone Kiss Cut section: 29×42 cm effective area, 1–2 cm registration/sensor allowance, and half-cut with backing intact. That section continues to direct capacity questions to source03 and does not restore the conflicting grid counts or broad custom-shape promise. All 42 manual size/count pairs, tariff lines, and the entire existing manual section through EOF remain byte-identical to revision 16. Source06 now has 8 passages, including one 407-character process passage.

Before/after evidence: [original139 private export](/tmp/rag-knowledge-before/06_estimasi_pcs_per_lembar_a3.txt), [precision replacement retained through revision16](../../dataset/knowledge-revisions/2026-10-24/06_estimasi_pcs_per_lembar_a3.txt), [current revision18 replacement](../../dataset/knowledge-revisions/2026-10-24-restoration/06_estimasi_pcs_per_lembar_a3.txt), [precision provenance](../../dataset/knowledge-revisions/2026-10-24/provenance.json), and [restoration provenance](../../dataset/knowledge-revisions/2026-10-24-restoration/provenance.json).

## Substantive technical omissions and subsequent validation

The original source06 introduction, lines 13–15, contained:

> 1. Metode Kiss Cut (Mesin Cutting Otomatis Plotter):
>    - Area Efektif: 29 cm × 42 cm (disisakan ruang 1–2 cm untuk tanda registrasi sensor mesin).
>    - Pemotongan setengah putus (kertas backing tetap utuh). Cocok untuk stiker bentuk bulat, oval, atau custom shape.

The `29×42` effective area also appeared in original source04's calculation guide and deleted example. At the **10:41 revision 16 inspection**, searching all six hash-verified active texts found **no remaining occurrence** of the 29×42 machine-area statement, registration allowance, `backing`, or `setengah putus` description. Source02's ordinary A3 dimensions **29.7×42 cm** are a different claim. After user confirmation, revision 18 restored all three process facts in source06; the historical absence finding does not describe the current active corpus.

| Removed content | Evidence of contradiction | Audit conclusion |
| --- | --- | --- |
| Grid-derived Kiss Cut capacities such as 5×5=40 and 3×3=126 | Directly differs from the retained source03 official capacity table, 35 and 108 respectively. Prior business confirmation supports using the official 5×5 count. | A demonstrated capacity contradiction was removed. |
| Effective machine area 29×42 cm | Source03 gives usable counts, not a direct statement rejecting this physical area. Spacing, margins, shapes or production layout could affect counts. | Removed earlier; **not independently disproved** by the table. User confirmed validity on 24 October 2026; restored in source06 at revision 18. |
| Sensor/registration allowance 1–2 cm | No contradiction was established in the initial audit. | Removed earlier; user confirmed validity on 24 October 2026; restored in source06 at revision 18. |
| Half-cut with backing intact | No contradiction was established in the initial audit. | Removed earlier; user confirmed validity on 24 October 2026; restored in source06 at revision 18. |
| General suitability for circle/oval/custom shape | Source04 retains the more specific circles/simple-shapes restriction and lettering exclusion. | Original broad wording was removed; shop-specific supported capabilities still require the existing scope. |

The official count correction does not logically prove that the physical area, sensor allowance, or cutting definition was false. Their removal remains disclosed as content loss from the earlier cleanup, not retrospectively justified as validated misinformation. The user's later confirmation supplied the business validation for restoring those three facts. The subsequent operator restoration completed after the active evaluation's scoring freeze. Conflicting grid capacities and the broad custom-shape promise remain excluded.

## Source identity and exact hashes

The stable source IDs identify the same six Knowledge-page entries before and after replacement:

| File prefix | Source ID | Blob ID at the revision16 audit |
| --- | --- | --- |
| 01 | `ae2852bc51ff4b588bee4ec0de5a1618` | `487baa47a2f94133a6951fb4e6399436` |
| 02 | `37cfa02e3aac466b9a806aa2bd465fd3` | `08c1192e03e34507a46dbbee648be248` |
| 03 | `6e21c4942b07464a9285ad8d7d1f8cec` | `b457cbf47b594baf9d444694eab014a8` |
| 04 | `36f51e8a65d64ff8b782187c47b68720` | `d15fa09cf6ce474b8f8b19bef2c78e67` |
| 05 | `dd49dc2700a64546a995be35e6474b60` | `df1f3c1e3ab64a87b2d01a65ebb3779e` |
| 06 | `aea30213c78a4e5d819d2ae2dd199069` | `97f0f1552c2646afb420d1f0dc2f953c` |

```text
01 original139 31bc29dd769d698d0e9988f8d12dd26757a5303348fd441fba8295022f965fdc
01 precision142 a71abb58643be1e5522cbcb6ba09c5e0c056914069f7ec4a677b63dad84ebd30
01 recall141    4644272c85369c6de895eee7f38121126b6cd054a6f955806ed0d1e63205a1ed
01 restored142  4644272c85369c6de895eee7f38121126b6cd054a6f955806ed0d1e63205a1ed

02 throughrev16 448fc0a469256712acda22d22aea4a674210b828a3e0761260ed5ee38d4a7352
02 restored142  2298e1e3098d0dfb26a1db744117fea5de154cdc23b372951fe608822d577920
03 all stages   10b06892b01ddbae064bef3c52d0127fe7fe797ccbd2c28c04c14c6dd81bb19d

04 original139  048fc683a95b9c5884d01348770f2a815a51d5bd998766dbff6249bc2f67b048
04 precision142 e47b67626e0e5a98fe6582bb55684d04799006e602088862e79d6f148f0edffe
04 recall141    e47b67626e0e5a98fe6582bb55684d04799006e602088862e79d6f148f0edffe
04 restored142  e47b67626e0e5a98fe6582bb55684d04799006e602088862e79d6f148f0edffe

05 all stages   e87bc03eed420c15b4e84303d2e5bb2cc821c23fd77d1dc26a6e4fab4f2fb8ca

06 original139  d072075361d140e615738d90ac73640a9e2a767014f7edcffdf3998e5ddd2181
06 precision142 1f9e13352fdf7909b68e5f84a54adb0f266aec63ee398f61f0c7b433a52971ed
06 recall141    1f9e13352fdf7909b68e5f84a54adb0f266aec63ee398f61f0c7b433a52971ed
06 restored142  41842e8490846877ed94bf221015ee342da99e16b1aba325f12e7e8358db6e62
```

The private original exports and [inventory](/tmp/rag-knowledge-before/inventory.json) are temporary local evidence, not committed source artifacts, and may not exist on another checkout. The [initial audit](2026-10-24-knowledge-audit.md) records their original source/blob/hash inventory. Frozen before/after replacement hashes and activation IDs are retained durably in the [precision ledger](../../dataset/knowledge-revisions/2026-10-24/provenance.json), [recall ledger](../../dataset/knowledge-revisions/2026-10-24-recall/provenance.json), and [restoration ledger](../../dataset/knowledge-revisions/2026-10-24-restoration/provenance.json).

## Local files, Knowledge page and activation boundary

`dataset/knowledge_base/` is **not an automatic mirror of the administered source originals**. At the dated revision 16 inspection, local files 02 and 05 hash-matched the administered originals; local 01, 03, 04 and 06 differed. After the revision 18 source02 repair, **only local05 matches its active administered file**. Local02 still contains the superseded cross-reference. Local01 contains the older Admin1 number 0896-3241-1115, while the original139 live export and the retained SOP replacements preserve 0896-9241-1115. Re-uploading the old repository folder wholesale could undo newer administered facts.

The exact current changed sources are **recall-directory01**, **restoration-directory02**, **precision-directory04**, and **restoration-directory06**, linked above. Administered03/05 continue using their unchanged private originals. The frozen revision directories document what was uploaded; merely editing a local TXT file does not update customer retrieval.

The existing authenticated Knowledge **Replace** or **Save text** flow uploads a private replacement original and stages its source reference. **Sync knowledge** builds and verifies a separate snapshot namespace, then atomically activates it. The earlier precision/recall activations used that workflow. The later restoration used its existing operator private-upload/finish services and the normal durable Sync service, as recorded in the activation evidence; this report does not claim that restoration was clicked through a browser session. Source edits and Sync are distinct operations; a failed Sync must retain the old active selection. The completed restoration has no pending source revision.

These source changes did not themselves redesign the Knowledge page. The page still represents the same six source entries, with changed source content and passage organization where documented. Runtime ingestion changes concern the versioned separator-heading preprocessing and preservation of explicit historical recipes.

## Correction to preservation language

Use the following scope when explaining the work:

- **Accurate:** “The latest SOP01 replacement moved and reformatted existing visitor information while preserving its business facts, contacts, staff scope and remaining policies.”
- **Accurate:** “Earlier 04/06 replacements resolved conflicting Kiss Cut capacity instructions and preserved tariffs and all 42 manual capacity pairs, but also removed technical process descriptions and left a stale source02 cross-reference.”
- **Accurate:** “After the user confirmed the three process facts, revision 18 restored them in 06 and corrected 02's one cross-reference line. Across the whole work, 01/02/04/06 changed; 03/05 remained unchanged.”
- **Inaccurate:** “Only display/spacing changed,” “all six source contents stayed unchanged,” “only duplicate text was removed,” or “every original business/technical fact was preserved across all revisions.”

The latest SOP conservation ledger does not certify conservation for the earlier04/06 changes. Neither measured retrieval scores nor a successful evaluation run establishes the truth or falsity of the removed technical details. Their validation comes from the subsequent user confirmation. The restoration set is now **activated at revision18**. Its [ledger](../../dataset/knowledge-revisions/2026-10-24-restoration/provenance.json) records exact hashes, offline proofs and completed activation. Historical evaluation evidence and the revision16 namespace remain retained; source restoration does not retroactively change their results.

## Activated restoration follow-up (revision18)

Operator restoration began on **24 October 2026 at 10:59:48 Asia/Jakarta**, after the active `c221` evaluation's **10:55:03 scoring cutoff**, and completed at **11:01:49**. Existing private upload/finish services replaced only 02/06; durable Sync job **`84668f0b823a402cbe360c2c711bd766`** completed 142/142 passages with no error and atomically activated **`kb-84668f0b823a402cbe360c2c711bd766`**. Post-activation revision and applied revision are both 18, with `pending=false`.

| Replaced source | New active blob | Current content |
| --- | --- | --- |
| 02 | `d2af3ec04f514e5f97533c1913f34f0f` | Exactly one cross-reference sentence changed; all remaining bytes preserved. |
| 06 | `fc2e4550bd394b1390cdf5e3854a629e` | Three confirmed process facts restored, title scope updated, official03 capacity routing retained; manual section/tariffs unchanged. |

The [activation record](../../data/evaluations/faithfulness-follow-up-2026-10-24/knowledge-restoration-activation.json) contains all six active source hashes. The [durable Sync record](../../data/evaluations/faithfulness-follow-up-2026-10-24/knowledge-restoration-sync-job.json) confirms terminal completion and 142 verified passages. Those records match the [frozen restoration texts and ledger](../../dataset/knowledge-revisions/2026-10-24-restoration/README.md). No source03/05 replacement, tariff change, schema change, ACL change or runtime change was part of this restoration.

Scores frozen before activation belong to the retained 141-passage revision 16 snapshot. The current 142-passage restored snapshot has different 02/06 hashes; those historical scores are not post-restoration measurements, and this report claims no measured metric gain from restoration.
