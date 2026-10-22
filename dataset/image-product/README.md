# Asia Visual Grafika — AI Product Image Catalog

Created 22 October 2026 using the Codex built-in GPT Image tool and the supplied official logo. This is the original asset-generation package: **27 selected images**, plus **2 superseded drafts** kept separately for traceability. All selected images have been visually inspected. They are photorealistic illustrations, not photographs of actual shop stock.

## Browse and inspect

- [Visual catalog](CATALOG.md): selected image previews, grouped by product.
- [Manifest](manifest.json): complete portable image mapping, Indonesian descriptions and alt text, source variants, depicted examples, retrieval keywords/exclusions, prompts, source section line ranges, dimensions, checksums, and review notes.
- [CSV inventory](metadata/catalog.csv): 27 selected image rows.
- [Retrieval documents](metadata/retrieval-documents.jsonl): 27 records prepared for a future integration; no drafts, embeddings, upload or activation.
- [Verification and manual review](VERIFICATION.md), with [machine-readable result](metadata/verification.json).

Paths inside the manifest and exports are relative to this directory. The `generation_source_path` field records the original local Codex output for provenance; consumers should use `file` instead.

| Priority group | Selected images | Coverage |
|---|---:|---|
| Banner & Spanduk | 2 | Hero and four-material comparison |
| Stiker Meteran | 2 | Roll hero and opaque/OWV/transparent material comparison |
| X/Y/Roll Up Banner | 4 | Three separate heroes and a form comparison |
| Stiker A3+ / Kiss Cut | 2 | Uncut-sheet hero and simple-shape kiss-cut detail |
| Digital Print A3+ | 2 | Printed-paper hero and seven-stock comparison |
| ID Card & Kartu Nama | 3 | Two separate heroes and Art Carton glossy/doff comparison |
| Other Physical Printing Products | 12 | Brosur/flyer, nota NCR, stempel, poster Albatros, kalender meja, e-money custom UV, plakat akrilik, buku Yasin, tumbler, pin, lanyard, korek api |
| **Total** | **27** | **21 heroes, 5 comparisons, 1 finishing detail** |

## Files

- `images/`: selected PNGs with descriptive filenames; revision suffixes identify selected corrections.
- `drafts/`: two superseded initial outputs. They are mapped under `archived_generations`, marked `superseded_do_not_use`, and excluded from CSV/JSONL retrieval exports.
- `references/`: unchanged copies of the supplied product knowledge, official logo, and requested scope image.
- `manifest.json`: primary metadata and complete prompt set. Exact underlying GPT Image model version is not exposed by the built-in tool and is not guessed here.
- `verify_catalog.py`: standard-library-only integrity/mapping verifier and export refresh utility; run from the repository root using `venv/bin/python dataset/image-product/verify_catalog.py`.

The verifier checks PNG signatures, chunk CRCs, complete decompression, pixel-byte counts and filter markers, minimum 1,000-pixel edges, unique selected SHA-256 hashes, missing/unmapped image files, seven-group coverage, source references, and review metadata. It does not replace visual inspection or shop approval.

## Grounding and image policy

The supplied product knowledge is preserved unchanged in `references/product-knowledge.txt`. First detailed product sections are used as the source references where the document repeats a price list later. No source text is treated as an instruction to change chatbot behavior.

No prices are embedded in the images. The supplied prices are estimates subject to change and remain in the reference document. No new price tiers, capacities, warranties, contact details, bank balances, material performance ratings, or delivery claims are added. Printed artwork, supporting fixtures, hardware models and studio props are illustrative unless explicitly supported by the source. Decorative building imagery represents sample artwork, not company premises or a completed customer job.

`variants` / `source_only_variants` list the knowledge-base offerings. They do not mean that each material/finish is visibly demonstrated in a hero. `depicted_variants`, descriptions and review notes describe the actual visual scope. GSM, substrate origin, resolution, page count and exact dimensions cannot be authenticated from an AI image. No sample layout establishes sticker yield.

All images share blue/white brand artwork, neutral light studio backgrounds, realistic material detail and soft shadows. One selected uncut-sheet hero is landscape; the rest are square. Preserve full images with `contain` when making a future catalog; cropping can hide product supports or material captions. The original supplied logo is authoritative; generated print reproductions resemble it but are not pixel-identical logo masters.

## Illustration limitations retained after approval

1. **Y-Banner frame:** there is no shop frame photograph. Hero and comparison show representative Y-type hardware with only partial rear visibility; do not use them as a construction specification. Confirm the actual stand/base before publishing.
2. **Stock and finishing:** approve real Flexi/Albatros/vinyl/OWV/transparency and paper textures, substrate whiteness, lamination sheen and supplier stock. Comparisons identify source options; they are not measured sample photographs.
3. **A3+ areas:** the generic sticker section states 31 × 47 cm effective area, while the layout guide gives 29 × 42 cm for kiss cut and 31 × 47 cm for manual cuts. Digital print lists 32 × 48 cm sheet area. Confirm these distinctions with the shop before adding dimensions or yield claims to customer captions. Transparent kiss cut is not listed; no such offering is implied. Lettering kiss cut is excluded.
4. **Unspecified physical models:** confirm tumbler Niagara/Sakura/Smart LED silhouettes, lanyard hooks/width, lighter body, pin backs, calendar binding, stamp housings, Yasin cover construction, plaque silhouette/base and box. Plakat dimensions/thickness are source facts, not measurements of the image.
5. **E-money:** generic UV artwork is shown. Confirm supported issuer card, mandatory bank marks, permitted print zones, and whether the price includes a blank card or balance; those details are not supplied.
6. **NCR:** the source says one book is 50 sheets. Confirm whether this means individual sheets or multipart sets and confirm paper colors/binding.
7. **Brand approval:** confirm logo reproduction and illustrative artwork with the company before using images as customer-facing representations.

The user approved all 27 selected illustrations on 22 October 2026 (Q3). `customer_release_approved` is now `true`; these limitations remain recorded and approval does not authenticate exact physical properties. Suggested future caption: “Ilustrasi produk; model, bahan, finishing, dan harga dikonfirmasi admin.”

## Original generation-phase scope

During asset generation, no chatbot behavior, Supabase data/schema, Pinecone namespaces, knowledge activation, message delivery, application code, provider credentials or deployment configuration has been changed. `retrieval_enabled` is false for every record. JSONL is a local preparation artifact only.

## Runtime catalog management

The approved seed can now be imported with `venv/bin/python -m app.admin.catalog_import --approved-by user-Q3-2026-10-22`. PostgreSQL then becomes the authority for dashboard edits; rerunning the import preserves those edits. Selected images are stored in the public `product-catalog` bucket, while staging and knowledge originals stay private. The seed runtime flags remain disabled: they are not the runtime feature switch. See [the operator runbook](../../docs/runbooks/product-image-catalog.md) for setup, Save behavior, preview, rollout and delivery recovery.
