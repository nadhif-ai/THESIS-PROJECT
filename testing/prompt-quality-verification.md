# Conversational prompt implementation and verification

Observed 18 October 2026. Implemented in the shared checkout; this change has not
been deployed. The approved single-KB refactor is already present and remains the
owner of source synchronization, active knowledge selection and durable jobs.
Coordination with the “Set up and run chatbot RAG” chat confirmed that its release
excludes these prompt edits.

## Behavior and persistence

- `app/backend/prompt_template.py` separates editable conversational instructions
  from code-owned grounding, safety, pricing/calculation and WhatsApp formatting
  rules. Examples teach style without embedding changing tariffs. Temperature
  remains 0.0. The default asks one focused clarification, answers thanks briefly,
  makes lists/emojis optional, and removes repetitive reset reminders.
- `/admin/knowledge` has an authenticated Global system prompt editor. Save uses
  `PUT /admin/api/knowledge/prompt`; GET returns the saved/default instructions and
  effective prompt hash. Existing admin session, same-origin, CSRF and maintenance
  checks apply. Empty, whitespace-only, non-string, oversized and control-character
  values are rejected. Braces are literal text, not template variables.
- Save persists a string under `global_conversational_prompt` in the existing
  private Supabase PostgreSQL `chatbot.settings` table. No new table, credentials,
  migration, public policy, Pinecone write or knowledge revision is needed.
- Restore Default loads the built-in text into the draft. Save applies it. The
  editor reports unsaved changes, supports discarding them, warns before tab exit,
  retains the draft after save failure and returns keyboard focus to the textarea.
  In-app navigation shows the unsaved notice but does not block navigation or
  preserve an abandoned draft.
- The cached RAG chain reads committed instructions on each new LLM request;
  changes do not require another deployment or knowledge synchronization after the
  feature itself is released. Existing requests retain their captured prompt.
  Greeting, help/menu, reset and exact brief acknowledgements use built-in replies,
  as disclosed beside the editor. Help/menu is where reset guidance appears.
- History reads up to eight nonempty, completed pairs in the same session/channel,
  observes reset boundaries, and sends distinct human/assistant messages. Whole
  recent pairs fit within an 8,000-token conservative UTF-8 byte bound, including
  64 units per pair for framing. This is an upper-bound estimate, not a particular
  provider's tokenizer count. Older/oversized turns are omitted rather than
  truncating every assistant reply at 300 characters. For short requests, retrieval
  also receives up to three recent customer questions within 1,200 UTF-8 bytes.
- Returned answers and WAHA use the same text normalization. Legacy HTML emphasis
  and Markdown double asterisks become WhatsApp single-asterisk emphasis. Lists,
  line breaks, emojis and literal URLs remain usable.

## Evaluation consistency

New durable evaluation submissions capture the complete effective system text,
editable instructions, recipe and SHA-256 in the checkpoint. Preparation copies
that snapshot/hash into the result. Every question and simulated assistant turn
receives this snapshot explicitly, across saved prompt changes, worker recreation
and retries. Simulator-provided conversation turns supply history, avoiding
duplicate database turns after an interrupted simulation.

The older runner also captures once at execution start. The DeepEval pytest suite
captures once in its module fixture and records snapshot/hash in case metadata
and LangSmith trace metadata. Existing metrics, thresholds, reviewed datasets and
legacy results are unchanged. Historical results are not backfilled with invented
prompt contents. Unfinished legacy jobs without a saved prompt snapshot retain
the existing mismatch guard and can require a fresh run after a code deployment.

## Regression evidence

| Check | Observed result |
| --- | --- |
| `venv/bin/python -m pytest testing --ignore=testing/evals -q` | 183 passed; two dependency deprecation warnings |
| Focused prompt/durable tests after strengthening restart coverage | 24 passed |
| `node --test testing/test_admin_navigation.mjs testing/test_dashboard_query_retry.mjs` | 19 passed |
| `npm run build` in `frontend` | TypeScript and production build passed |
| `npm run lint` in `frontend` | Exit 0; existing warnings in shared UI/hooks and Knowledge page, none in the new editor |
| Mechanical design detector on the changed UI | No findings |
| Paid DeepEval CLI, one existing legacy location case | Exit 0; five metrics passed at existing threshold 0.7 |

The new tests use disposable local PostgreSQL and fake providers. They cover
authentication, CSRF/origin rejection, validation without overwriting a saved
prompt, persistence across pool recreation, restore, literal braces, immutable
rules, complete history, channel isolation, reset, live settings reload on a
cached chain, snapshot pinning across actual durable checkpoints and saved
results, legacy record readability, social shortcuts and idempotent formatting.

Browser verification used the real built frontend and admin API against a
disposable local database. It exercised Save, reload/persistence, Restore Default,
Discard changes, blank validation, blocked-network save failure and recovery,
keyboard submission and focus restoration. At 320 px, document scroll width was
320 px; reduced-motion emulation was active. Captures are in `prompt-editor/`.
The final light-theme contrast check measured 13.66:1 for the textarea text and
6.14:1 for supporting text. Desktop light/dark captures were visually inspected.

## Live response smoke test

`prompt-live-smoke.json` contains eight synthetic requests against the actual
active Pinecone snapshot and configured answer model, without inserting test
conversations into Supabase, saving a production prompt or sending WhatsApp.
The test used `openai/gpt-6-luna`, temperature 0, and snapshot
`kb-25f39a6805154e86a7507bb93ce1c758` with 95 passages.

| Scenario | Observed answer/check |
| --- | --- |
| Spanduk 2×3 m, two sheets, missing material | “Bahannya mau pakai apa, Kak?” |
| Follow-up: Flexi China 280 GSM standard | Rp198.000; previous size and count retained |
| Follow-up: change count to three | Rp297.000 |
| Vinyl A3+, 5×5 cm, 100 pcs, without kiss cut | 54 pcs/sheet, two sheets, Rp25.000 |
| Standard Flexi 280, 0.7×1.1 m, one sheet | Rp13.000 after rounding upward |
| Hardcover with emboss and foil | No invented price; special-finishing quotation guidance |
| Thanks | “Sama-sama, Kak.” |
| 200 A5 brochures, Art Paper 150 GSM, two sides | Correctly identified 50 A3+ sheets; retrieval missed the applicable tariff, so no total was invented |

All eight answers omitted HTML and reset reminders. Four available-price totals
matched the expected amounts. The brochure retrieval miss remains unresolved.
These observations are a small behavior smoke test, not an improvement percentage,
a complete pricing benchmark, or a customer-conversation evaluation.

The paid DeepEval check used the same active KB in disposable local state, the
existing `deepseek/deepseek-v4.1-flash` judge, unchanged metrics and an existing
reference. `prompt-deepeval-result.json` records the answer, metric reasons,
captured prompt and matching hash. Scores: Faithfulness 1.0, Answer Relevancy 1.0,
Contextual Precision 0.7, Contextual Recall 1.0, and Business correctness 0.7.
The last score reflects omitted operating hours from the legacy expected answer;
the customer asked for location. The reference and scoring threshold were kept.
An initial isolated invocation cleared the LangSmith key and failed during
feedback reporting after metrics passed. Rerunning with the existing authenticated
reporting configuration completed with exit 0. No production conversation records
were added by either invocation.

## Antislop DURING delivery gate

- Hard gate PASS for the changed surface: real Save/Restore/Discard behavior,
  validation/loading/error feedback, keyboard focus and a 320 px overflow check;
  no invented customer, performance or business claims.
- Purpose gate PASS: the editor reuses the existing paper-and-ink fields, panel
  and blue action style to make one configuration task readable; no decorative
  assets, icons, motion or navigation were added.
- Liveliness PASS within the existing dashboard direction: the long instructions
  have their own work area, Save is the action focal point, and the inherited
  blue focus treatment remains visible. Review dials: energy 1, rhythm 2, motion 1.
- Craft/copy PASS for scoped changes: concise action labels, literal examples
  without embedded prices, optional lists/emojis in customer replies, no routine
  reset footer. Build and browser interactions were run, not inferred from code.

## Remaining limits and release

Retrieval can still omit a needed tariff. History is bounded and does not create
a permanent structured order ledger. Calculations and grounding remain model
instructions rather than a deterministic pricing engine. No broad multi-turn
judge benchmark or fresh end-to-end WhatsApp delivery test was run for this
unreleased change. Prompt saves use the existing settings model's last-save-wins
behavior across administrators.

Release the backend and frontend together once reviewed. Afterwards, admin prompt
saves are immediately visible to new LLM requests across workers. No reindex or
schema migration is required. The pre-existing `.gitignore` edit and the separate
single-KB release/evaluation records are outside this change.

Implementation follows the current documented LangChain
[MessagesPlaceholder contract](https://reference.langchain.com/python/langchain-core/prompts/chat/MessagesPlaceholder),
Supabase [private-schema behavior](https://supabase.com/docs/guides/database/tables),
and DeepEval [test-case metadata support](https://github.com/confident-ai/deepeval/blob/main/test_case/llm_test_case.py).

## Release addendum: warmer conversational default

The final default is more descriptive (usually two to four useful sentences),
explains price calculations naturally, and describes spare capacity as unused
slots rather than promising extra printed products. Built-in greetings, thanks,
and acknowledgements are warmer. Grounding and tariff rules remain unchanged.

Final effective system SHA-256:
`82adbd598e96ea5296a1b531e71c3c436d6b240ee3c4275dd9f113097f418e05`.

The earlier DeepEval and smoke artifacts above document the earlier candidate;
they are not a judge benchmark of this final style. Baseline UI evidence is in
`prompt-playground-e2e/`; final UI evidence is in
`prompt-playground-warm-style/responses-final.json` (four successful requests: two
price estimates, sticker capacity, and thanks). Three generated answers matched
the final prompt hash. The earlier candidate also encountered two browser
transport failures; those are retained separately and their cause is unconfirmed.
The short brochure-query retrieval limitation remains unresolved.

Release regression rerun: 183 backend tests passed (two dependency warnings),
19 JavaScript tests passed, frontend production build passed, and lint exited 0
with existing warnings. All 35 staged release files passed the local secret scan.
