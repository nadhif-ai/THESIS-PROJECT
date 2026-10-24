# User-confirmed Kiss Cut process restoration, 24 October 2026

Status: **activated at source revision 18 on 24 October 2026 at 11:01:49 Asia/Jakarta**. The published namespace is **`kb-84668f0b823a402cbe360c2c711bd766`**, with **142 verified passages**, `revision=18`, `applied_revision=18`, and `pending=false`. The two replacements derive from the exact pre-restoration revision 16 source hashes. The preceding 141-passage namespace `kb-e622863bb58d4137b4e8bf7cf62a186e` remains retained for historical evaluations.

The user confirmed in chat on **24 October 2026** that all three previously removed process facts are valid:

- Kiss Cut machine effective area: **29 cm × 42 cm**.
- Allowance for registration/sensor marks: **1–2 cm**.
- Kiss Cut makes a **half-cut with the backing intact**.

These process facts are now restored in source06. The former conflicting grid-derived Kiss Cut capacities, the deleted 500-piece pricing illustration, and the broad custom-shape capability claim remain excluded. Official Kiss Cut piece counts continue to come from the unchanged table in source03.

## Activated files

| File | Exact change | Passages before→after |
| --- | --- | ---: |
| [02_spesifikasi_bahan_dan_finishing.txt](02_spesifikasi_bahan_dan_finishing.txt) | Replace the stale final cross-reference with separate routing: official Kiss Cut quantities →03; Kiss Cut process and manual estimates →06. Every other byte remains unchanged. | 29→29 |
| [06_estimasi_pcs_per_lembar_a3.txt](06_estimasi_pcs_per_lembar_a3.txt) | Update the title/subtitle to reflect process information plus manual estimates; add one standalone Kiss Cut process section containing the three confirmed facts and a direction to the official03 table. The complete existing manual section through EOF remains byte-identical. | 7→8 |

No other source changed in this replacement set. In particular, SOP01, the official source03 Kiss Cut table and source04 tariffs are untouched. Both replaced files retained their existing Knowledge source IDs. Across the complete original139→precision142→recall141→restored142 sequence, **four files changed: 01, 02, 04, 06**; 03 and 05 remain unchanged.

## Exact source hashes

```text
02 before 448fc0a469256712acda22d22aea4a674210b828a3e0761260ed5ee38d4a7352
02 after  2298e1e3098d0dfb26a1db744117fea5de154cdc23b372951fe608822d577920

06 before 1f9e13352fdf7909b68e5f84a54adb0f266aec63ee398f61f0c7b433a52971ed
06 after  41842e8490846877ed94bf221015ee342da99e16b1aba325f12e7e8358db6e62
```

The source02 base is the private original export and is byte-identical to the older repository source02; that repository file no longer mirrors the active source02 after this cross-reference repair. The source06 base is the frozen [preceding replacement](../2026-10-24/06_estimasi_pcs_per_lembar_a3.txt), whose hash was verified against the pre-restoration administration source in the [change audit](../../../docs/research/2026-10-24-knowledge-change-audit.md). The earlier [precision provenance](../2026-10-24/provenance.json) and [recall provenance](../2026-10-24-recall/provenance.json) remain frozen.

## Offline proof

The actual `app.admin.chunking.split_document` ran locally with **sections-v2, chunk size 1000, overlap 100**, without API/database/provider calls. The [provenance ledger](provenance.json) contains exact before/after hashes, conservation checks, passage counts and the full restored process passage.

- Source02 changes exactly one cross-reference line; the remaining text has identical SHA-256 `505c2ade4ea3869639c0dde1ee09864de6302e8c518b8c95dac91ab37b610c98`.
- Source06's existing manual section through EOF has identical SHA-256 `e17c0e0f81ecae1390156abe6dd6383702db0a219aff0583bc9330ebcbf55c7d`.
- All **42 manual size/capacity pairs**, their order, and all source06 tariff lines are unchanged: 24 square pairs and 18 rectangular pairs.
- The three process facts and official-capacity reference remain together in **one 407-character passage**. Its SHA-256 is `e006910f19063c7119ea9dbfa84c3782560d0e5403570beb61ff5ebabd6078f4`.
- Every replacement passage stays within 1000 characters: source02 maximum 999; source06 maximum 997.
- The offline estimate was **142 complete-corpus passages**. Completed Sync subsequently verified that exact count. Passage conservation and successful activation do not themselves measure retrieval or answer quality.

## Completed activation and evaluation boundary

Local preparation performed no administration writes. The later operator activation started at **10:59:48 Asia/Jakarta**, after the active `c221` evaluation's **10:55:03 scoring cutoff**, and used the existing private upload/finish services followed by the normal durable Sync. It did not require a new browser session, ACL change, schema change, or runtime change. The [activation record](../../../data/evaluations/faithfulness-follow-up-2026-10-24/knowledge-restoration-activation.json) retains both replacement blob IDs, all six source hashes, the cutoff and the old/new namespaces.

Sync job **`84668f0b823a402cbe360c2c711bd766`** completed with 142/142 passages and no error, then atomically activated revision 18. The [durable job record](../../../data/evaluations/faithfulness-follow-up-2026-10-24/knowledge-restoration-sync-job.json) and [provenance ledger](provenance.json) retain the completed snapshot/revision/count. The ledger's original pre-activation requirements and offline proof remain preparation evidence; the completed activation fields and saved job record establish the later active state.

The restored 142-passage snapshot has different 02/06 source hashes from the frozen 141-passage evaluation snapshot. Scores completed before this activation remain attributed to their original 141-passage snapshot and are not post-restoration measurements. No metric improvement is claimed from this content restoration. Source03/05, the existing source04 tariffs, SOP01, and historical evaluation evidence remain unchanged by this activation.
