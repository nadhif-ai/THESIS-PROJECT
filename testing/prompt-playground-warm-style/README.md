# Warmer conversational style verification

18 October 2026, Asia/Jakarta. Active locally at `http://127.0.0.1:8000/admin/playground`.

## Changes

- Default conversational instructions now ask for a warm WhatsApp-admin voice, short descriptive explanations, context-aware follow-up questions and restrained optional emoji.
- Price answers confirm the specification and explain the calculation; capacity explanations distinguish unused layout slots from promised extra products.
- Greeting, acknowledgement and thanks shortcuts use warmer wording. Existing grounding and calculation rules remain separate from editable style.
- There was no saved prompt override when checked; the running local backend uses the new built-in default. No database prompt Save was needed.

## Executed verification

- `venv/bin/python -m pytest testing/test_prompt_settings.py -q`: **16 passed**, one third-party deprecation warning, rerun after the final wording change.
- `git diff --check` on the three changed code/test files passed.
- Final prompt SHA-256: `82adbd598e96ea5296a1b531e71c3c436d6b240ee3c4275dd9f113097f418e05`.
- Final UI run: **4 completed requests, HTTP 200**, three LLM answers returned the matching prompt hash. Price totals remained Rp198.000, Rp297.000 and Rp25.000. The last answer correctly describes eight unused slots, rather than extra delivered stickers. Thanks returned “Sama-sama, Kak! 😊”.
- `responses-final.json` and `price-final.png` capture the actual browser results. This small style check is not a new DeepEval benchmark or an engagement measurement.

## Earlier attempts and limits

`responses.json` records five completed UI responses from the first wording candidate. Two earlier browser requests reported Failed to fetch; one courtesy retry succeeded. The manual-sticker request completed on the backend/LangSmith although its browser response was lost; that server-only evidence is explicitly labelled in `server-response-not-delivered.json`. Database connection timeouts and an OpenRouter retry were observed in logs; no infrastructure root cause is claimed. Following a local backend restart, all four final UI requests completed normally.

This update changes conversational style. The brochure retrieval wording sensitivity documented in the earlier Playground baseline remains outside this change. No new knowledge synchronization, vector changes, WhatsApp sends, commit or deployment were performed for this style update. The refreshed local backend is left running for review.
