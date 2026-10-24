# Evaluation workspace verification

Verified locally on 23 October 2026. Scope: `/admin/evaluations`, its result view, and model selection in `/admin/providers`.

## Shipped behavior

- Setup and reference preparation share a responsive work area; history remains a separate record list.
- History shows short run IDs and supports status/task filters stored in the URL.
- Inspect result opens a dedicated `?run=ID` view. The history workspace stays mounted but hidden, preserving setup state. Back navigation restores filters, scroll, and the matching run action's focus. Browser back/forward and returning after a result-page reload were exercised.
- Result provenance includes full run ID, observed status/start time, dataset, knowledge snapshot, answering model, and judge. Saved averages, coverage counts, explanations, thresholds, answers, references, retrieved passages, and trace links remain evidence from the stored run.
- Missing case scores and cases without metrics need attention; missing results receive an explicit progress/error view rather than an indefinite loading message.
- Providers offers all requested model identifiers, retaining the saved model when outside the supplied options. Intent configuration persists in the existing settings store and reaches the shared classification runtime and recorded provenance. Legacy settings clients preserve an existing intent selection.
- Dataset dialogs restore focus to their opening button after closing with Escape.

## Design decisions

- Mode: Operate. ENERGY 1 / RHYTHM 2 / MOTION 1.
- Color: existing warm paper, graphite, and proof-blue tokens preserve the printing workspace identity in both themes.
- Typography: existing IBM Plex Sans carries labels and evidence; weight and scale distinguish run identity, metric values, and supporting metadata.
- Layout: setup leads; reference review supports it; history is a list of identifiable runs; results occupy their own reading context.
- Spacing: 16px control gaps, 24px work-area gaps, and 32px before case evidence distinguish related fields from separate tasks.
- Containers: existing panels group coherent tasks; metrics use a flat grid and cases use disclosures, without charts or metric cards.
- Motion: existing state transitions and focus indicators support interaction; no decorative animation was added.

## Automated checks

- `LANGSMITH_TRACING=false venv/bin/python -m pytest -q`: **273 passed, 11 skipped**. Paid evaluations remained disabled. PostgreSQL fixtures used only `chatbot_test_*` databases on loopback port 54585. Docker was unavailable, so disposable Homebrew PostgreSQL 15 served the test port.
- `node --test testing/test_evaluation_view.mjs testing/test_admin_navigation.mjs`: **10 passed**.
- `npm run lint && npm run build` in `frontend/`: **passed**. Existing lint warnings remain in shared UI/hooks and knowledge-page files.
- `impeccable detect --json frontend/src/App.tsx frontend/src/index.css`: **no findings**.
- `git diff --check`: **passed**.

New backend regressions in `testing/test_provider_models.py` cover authentication, persistent settings, legacy saves, invalid identifiers, intent classification/provenance, and structured client selection without restarting the process.

## Browser checks

Ego Lite on the existing local Vite app, using saved evaluation evidence. Screenshots cover wide and 390px mobile layouts in light and dark themes. Result and setup widths were also checked at 768px; a 320px result check had no horizontal overflow. Reduced-motion emulation preserved the existing near-zero transition duration.

- Result opening, return focus/scroll/filters, browser back/forward, reload and return: passed.
- Native select keyboard events, Tab focus, visible focus rings, Enter disclosures: passed.
- QA and conversation review dialogs, Escape and return focus: passed.
- All/attention case filters, metric disclosures, source passages, trace/experiment destinations, and JSON export (HTTP 200): checked.
- Real-data empty filter, simulated first-run empty history, loading result, failed result request with retry/back controls, absent result, zero cases, no attention cases, and reporting-retry notice: checked.
- Provider selector changes and Save settings payload: checked with a browser-only mocked PUT; no live model setting was changed.
- Run evaluation request: checked with a browser-only mocked POST; the existing `{dataset, limit}` contract was preserved and no paid run was queued.
- Computed text contrast, including alpha-composited dark button surfaces: no violations in the inspected visible result text. Closed disclosure contents were excluded from the visibility check.

Browser-only network overrides were removed and the page reloaded afterward. No authentication bypass or test fixture was added to product source.

## Anti Slop delivery gate

- R-02 PASS: new UI copy uses ordinary punctuation; factual saved content remains verbatim.
- R-03 PASS: inspected mobile/tablet layouts have no horizontal overflow.
- R-17 PASS: run counts, scores, and coverage derive from API records.
- R-18 PASS: no testimonials or invented people added.
- R-23 PASS: no new visual assets or fabricated records added.
- R-24 PASS: navigation, exports, and trace destinations use existing routes or recorded URLs.
- R-25 PASS: inspected visible result text passes contrast checks in the existing theme palette.
- R-26 PASS: selectors, filters, inspection, return navigation, disclosures, and recovery controls have behavior.
- R-27 PASS: loading, first-run empty, filtered empty, missing result, zero cases, and failed requests checked.
- R-28 PASS: no FAQ introduced.
- R-32 PASS: keyboard selection/disclosures, focus rings, run return focus, and dialog Escape return checked.
- R-33 PASS: UI changes authored in source; browser network fixtures used only for verification.
- R-34 PASS: light/dark wide and mobile captures inspected.
- R-35 PASS: app built and exercised locally; paid writes were mocked and backend persistence tested offline.
- R-36 PASS: no new operational, security, customer, or performance claims introduced.
- R-37 PASS: explicit paper-and-ink direction and dials applied.
- R-38 PASS: shipped content reads real API data; fixture changes stayed inside browser verification.
- R-01 PASS: no gradients/glows introduced; proof-blue retains action/focus meaning.
- R-04 PASS: existing action/status icons retained for their established meanings.
- R-06 PASS: IBM Plex Sans retained for operational reading; tabular numbers support comparison.
- R-07 PASS: no decorative background pattern introduced.
- R-08 PASS: external-link arrows indicate recorded external trace/experiment destinations.
- R-09 PASS: badges identify real state, coverage, or recorded scores.
- R-10 PASS: no additional glass surfaces introduced.
- R-12 PASS: panels remain flat; existing dialogs/menus retain transient elevation.
- R-13 PASS: no glow introduced.
- R-14 PASS: metrics use one flat grid; case evidence uses disclosures instead of repeated cards.
- R-19 PASS: no looping/decorative motion introduced; reduced-motion checked.
- Liveliness PASS: declared dials match calm task UI, with setup/run identity as focal points, structural whitespace, restrained proof-blue, and the existing proof-record motif.
- C-1 PASS: major design choices and their reasons are recorded above.
- C-2 PASS: new controls have working handlers; writes verified through mocks plus offline persistence tests.
- C-3 PASS: setup, reference review, history, metrics, and evidence directly serve evaluation work.
- C-4 PASS: responsive themes, keyboard flow, content extremes and request states checked.
- C-5 PASS: displayed evaluation evidence remains recorded evidence.
- R-05 PASS: setup columns, history rows, metrics and case disclosures reflect distinct tasks.
- R-11 PASS: existing control/panel/status radii preserved.
- R-15 PASS: action labels name their task.
- R-16 PASS: no promotional AI copy introduced.
- R-20 PASS: knowledge snapshot and printing-question evidence preserve the workspace's domain.
- R-21 PASS: both existing themes remain available.
- R-29 PASS: existing neutral palette, proof-blue accent, and semantic status colors retained.
- R-30 PASS: incumbent product identity preserved.
- R-31 PASS: layout, color, type, spacing, containers, and motion reasons documented above.

## Limits

No deployment or paid model compatibility test was performed. The requested model IDs are selectable identifiers, not a claim of provider availability or structured-output compatibility. Restart the existing backend process when adopting the backend changes locally. No database migration is required.

The pre-existing `PRODUCT.md` still mentions SQLite and a local worker; current repository guidance and implementation use PostgreSQL and durable jobs. This stale context was observed and left outside this UI change.

Screenshots are saved outside the repository under `/Users/royanrosyad/.codex/visualizations/2026/10/23/01a1697a-1325-7411-a1a0-98939695ec21/`.
