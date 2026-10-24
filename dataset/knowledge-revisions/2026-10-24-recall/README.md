# Customer-visit source cohesion, 24 October 2026

Status: **activated at source revision 16**. Authenticated Replace and Sync knowledge published snapshot `kb-e622863bb58d4137b4e8bf7cf62a186e` with **141 verified passages**. Only SOP source 01 changed. This replacement and the earlier revision directory are preserved as frozen activation records.

The replacement was based on the SOP activated in snapshot `kb-0a4b41713f9e423799b20387bda6597b`, source revision 15. Its before hash was verified against the preceding source ledger and revalidated through the authenticated knowledge API before Replace:

- Before SHA-256: `a71abb58643be1e5522cbcb6ba09c5e0c056914069f7ec4a677b63dad84ebd30`.
- After SHA-256: `4644272c85369c6de895eee7f38121126b6cd054a6f955806ed0d1e63205a1ed`.
- Existing source ID: `ae2852bc51ff4b588bee4ec0de5a1618`.

This is a source-organization change for customers deciding where and when to visit. It moves both complete branch addresses, maps, landmarks, and the existing customer schedules into one coherent visitor section. It does not add a question/answer example or change a business number to suit a benchmark.

The visitor section retains weekday opening/closing and the 01.30 order cutoff; the restriction to completion/pickup after that cutoff; Sunday hours and its distinct 20.30 order cutoff; national-holiday hours; and the Friday holiday exception after Friday prayers. The weekday schedule is not presented as a universal daily schedule.

Emails remain associated with their branches in a separate file-submission section. The entire contact block is preserved verbatim, including the later live Admin 1 number **0896-9241-1115**. The three staff shifts and staffed-break coverage are kept verbatim in a separate staff section, with their original Monday–Saturday qualification preserved. Everything from section 3 (ordering and collection) to the end of the file is byte-identical to the previous SOP; payment, production, cancellation, refund, and warranty facts therefore remain unchanged.

The [fact-conservation ledger](provenance.json) records seventeen checks, including exact address/map/landmark values, branch/email associations, unchanged contact and staff text, customer-schedule correspondence, and the preserved remainder hash. URLs and email addresses have identical multisets before and after, and the protected branch/contact values each occur once. Business facts were moved or reformatted rather than duplicated into multiple source sections.

## Offline splitter proof

The real `app.admin.chunking.split_document` function, with `sections-v2`, chunk size 1,000 and overlap 100, produced:

| Check | Result |
| --- | ---: |
| SOP passages before | 15 |
| SOP passages after | 14 |
| Visitor passages | 1 |
| Visitor passage characters, including heading prefix | 981 |
| Longest resulting SOP passage | 985 |

The single visitor passage contains both complete addresses, both exact map URLs, both landmarks and every customer schedule/cutoff. It excludes file-submission emails, phone contacts and staff shifts. Its exact text, metadata and hash are retained in [chunking-proof.json](chunking-proof.json). The dry run used no API, database, embedding, model or vector-store operation.

These checks establish source conservation and passage cohesion. Neither the splitter proof nor completed activation establishes improved retrieval, Contextual Recall, Contextual Precision or answer quality. Those outcomes require a fresh recorded comparison using the frozen before/after snapshots.

## Completed activation

Before Replace, the authenticated knowledge API confirmed the previous active namespace `kb-0a4b41713f9e423799b20387bda6597b`, revision 15, no pending changes, and the exact before source hash recorded above. The replacement was staged through the existing authenticated **Replace** flow; staged revision 16 matched the replacement hash.

**Sync knowledge** job `e622863bb58d4137b4e8bf7cf62a186e` built and verified the replacement, then atomically activated namespace `kb-e622863bb58d4137b4e8bf7cf62a186e` at revision 16 with 141 passages. The previous namespace remains available. Nemotron 2,048-dimensional cosine embeddings, 1,000/100 sections-v2 chunking and global top-k were retained.

The [provenance ledger](provenance.json) records the completed activation and source hashes. Preserve these artifacts and the earlier source ledger unchanged; any further source correction belongs in a new revision with its own provenance.
