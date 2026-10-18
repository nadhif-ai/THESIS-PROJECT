# Baseline prompt — Playground end-to-end verification

Historical baseline before the warmer style update; see `../prompt-playground-warm-style/README.md` for subsequent changes.

Observed 18 October 2026, Asia/Jakarta. Tested through **Ego Browser** at `http://127.0.0.1:8000/admin/playground` using actual UI submission (click Send and Enter), the real FastAPI handler, active Supabase state, Pinecone, OpenRouter and LangSmith. This is local unreleased prompt code, not a new Vercel deployment.

## Runtime finding

The initial Playground displayed API endpoint not found. Port 8000 was still serving the old backend process. It was restarted with the latest checkout and the same loopback binding and `--lifespan off`; the global prompt endpoint then returned 200. The replacement local backend is left running. No application source was changed for this check.

## Active configuration

- Built-in default conversational prompt; effective SHA-256 `ca09c7e60936382fe775dad9a0a40baf9aac3ffbad55189b69910c8b2078831a`.
- Answer model: `openai/gpt-6-luna`, confirmed in the actual ChatOpenAI trace invocation, temperature 0.
- Active namespace: `kb-25f39a6805154e86a7507bb93ce1c758`, 95 passages, Nemotron/OpenRouter 2,048 dimensions, Pinecone `chatbot-nadhif`.
- No prompt Save, knowledge mutation, reindex, WhatsApp send, commit or deployment was performed. These normal Playground tests persisted 13 synthetic LLM turns across nine test sessions in the shared conversation store. Courtesy/reset are built-in shortcuts.

## Observed outcomes

**15/15 submitted requests returned HTTP 200**, with no response error. Behavioral review: 13 pass, two partial; this is a small manual scenario check, not a DeepEval score or statistical benchmark.

| # | Scenario | Observed result | Review |
| --- | --- | --- | --- |
| 1 | Material missing | Asks material, but adds four material options | PARTIAL — style |
| 2 | Material follow-up | Keeps 2×3 m and two sheets; Rp198.000 | PASS |
| 3 | Quantity correction | Keeps specification; three sheets Rp297.000 | PASS |
| 4 | Thanks | Sama-sama, Kak.; built-in, zero model tokens | PASS |
| 5 | Kiss cut 5×5 cm | 35 pcs per A3+ sheet | PASS |
| 6 | Manual vinyl 100 pcs | 54 pcs/sheet; two sheets; Rp25.000 | PASS |
| 7 | Large-format rounding | 0.77 m² × Rp16.500, rounded upward to Rp13.000 | PASS |
| 8 | Unsupported finishing | No invented hardcover/emboss/foil price | PASS |
| 9 | New conversation | Does not reuse the previous order; asks product/material | PASS |
| 10 | Complete specification | Rp198.000 for two 2×3 m standard Flexi sheets | PASS |
| 11 | Reset | Built-in acknowledgement; sets history boundary | PASS |
| 12 | After reset | Asks product; trace has no old user/assistant turns | PASS |
| 13 | Detailed brochure query | Four A5/sheet; 50 A3+ sheets × Rp5.000 = Rp250.000 | PASS |
| 14 | Instruction/credential request | Declines disclosure; one specific safeguard test | PASS |
| 15 | Short brochure query | Correct 50 sheets, but cannot quote total because correct tariff is absent from retrieved context | PARTIAL — retrieval |

## Prompt/history/trace proof

- All 13 LLM responses returned the active editor prompt hash. The courtesy and reset shortcuts correctly have no LLM prompt hash.
- LangSmith input inspection verified the actual first system-message SHA in three traces. The quantity-follow-up trace contains distinct human/AI messages for the preceding two pairs. New conversation and after-reset traces contain two system messages plus only the current human message.
- Trace metadata identifies the same active KB, Playground channel and eight-pair history recipe. All 13 LLM trace IDs match persisted Playground conversation rows.
- Reported RAG latency: 8.059–15.598 seconds; median 10.446 seconds. This response field excludes some HTTP/admin overhead. No sub-second generation claim is made.

## Findings to refine

### Retrieval depends on brochure wording

Detailed wording: “Mau cetak 200 brosur ukuran A5, Art Paper 150 GSM, dua sisi. Berapa lembar A3+ yang dibutuhkan dan total harganya?” retrieved the digital-print tariff at ranks 2 and 3. The answer correctly used the 11–100-sheet, two-sided rate of Rp5.000 and total Rp250.000.

The exact earlier failing wording, “Brosur A5 art paper 150 gsm bolak-balik 200 pcs berapa?”, reproduced the miss. Its matching tariff headings were per-rim brochure packages, not the per-A3+ digital-print tier. The bot correctly avoided inventing a tariff, but did not complete the pricing task. The original price document SHA matches the active source; the tariff is present in the KB.

Recommended next change: normalize “bolak-balik” to “dua sisi/2S” and make the existing under-500 brochure rule help retrieval target digital A3+ printing. This can retain the current vector store/model and avoid adding reranking. The change was not implemented in this testing request.

### Clarification remains more verbose than instructed

The missing-material reply asks the correct question but adds four options. This falls short of the default instruction to ask one short clarification without listing options unless requested. Refine and retest this behavior separately; successful arithmetic does not establish full style compliance.

## Evidence

- `responses.json`: 15 browser-captured request/response payloads, including retrieved passages, source ranks, trace URLs and returned hashes. No authentication headers were captured.
- `trace-verification.json`: actual LangSmith message-role/hash inspections.
- `checks.json`: HTTP/hash/persistence checks, latency samples and both brochure-context comparisons.
- `environment.json`: active configuration without credentials or signed original-file links.
- `conversation.png`, `reset.png`, `brochure-short.png`: inspected browser screenshots.
