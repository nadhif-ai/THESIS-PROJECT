# Public landing page verification

Verified locally on 14 October 2026. The public `/` route serves the paper-and-ink landing page; `/admin/login` and `/admin/` open the existing administrator application. Successful login preserves a requested workspace section. Private APIs continue to require the administrator session and CSRF protection.

The page contains six selectable workspace previews, seven authentic captures, five detailed capability sections, the five-stage publication workflow, and workspace/login actions. Screenshot values are explicitly dated. Playground replays an existing benchmark answer with its source evidence. The supporting print photograph and existing mark reuse this project's Codex-generated assets; the photograph is labeled illustrative. See [capture provenance](../frontend/src/assets/landing/README.md) and [generation prompts](../frontend/src/assets/image-prompts.md).

## Validation

| Check | Result and evidence |
| --- | --- |
| Production build | PASS: `npm run build` completes TypeScript and Vite production compilation. |
| Lint | PASS: `npm run lint` exits 0; existing shared component/hook warnings remain. |
| Route and authentication regressions | PASS: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 venv/bin/python -m pytest testing/test_public_landing.py testing/test_admin_workflow.py::test_api_authentication_and_csrf -q`: 3 passed. Tests use temporary administration data. |
| Served application | PASS: port 8000 returns 200 for `/`, `/admin/`, `/admin/login`, compiled JavaScript/CSS/favicon, and the legacy asset mount. Recorded in `.impeccable/review/landing-served-routes.json`. |
| Responsive layout | PASS: browser widths 320, 390, 540, 768, 800, 1024, 1280, and 1440 have no page overflow or controls smaller than 44px. Recorded in `landing-layout.json`. |
| Links | PASS: 26 desktop/mobile navigation and CTA clicks reach their actual destinations. All seven enlarged-preview workspace links and the unavailable-preview workspace link also reach the expected route. Recorded in `landing-links.json` and `landing-dialog-links.json`. |
| Interactive previews | PASS: 14 checks cover six tabs, enlargement, Escape, five section previews, Close, focus return, mobile Menu, skip link, and unavailable-image/retry recovery. Recorded in `landing-interactions.json`. |
| Login and logout | PASS: 18 checks cover required-field validation, password visibility, overview return, preserved Knowledge destination, all five authenticated feature links, dashboard access, logout, and the subsequent private-API 401. Recorded in `landing-auth.json`; credentials are excluded. |
| Themes and browser surfaces | PASS: final desktop 1440×1000 and mobile 390×844 captures inspected in both themes, plus complete pages. Theme-token scrollbars, keyboard image panning, and reduced motion are recorded in `landing-browser-surfaces.json`. |
| Contrast | PASS: measured normal-text pairs exceed 4.5:1 in both themes; the lowest recorded pair is 5.34:1. Recorded in `landing-contrast.json`. |
| Runtime | PASS: final public browser run reports no uncaught errors. |
| Asset provenance | PASS: seven screenshot rasters have embedded capture provenance; the existing generated logo/photo retain their original embedded prompts. |

The browser evidence and independent review files are retained locally under `.impeccable/review/`. The independent finish review matched the requested surface and identified scrollbar theming; the scored fix and bundled dialog layout changes received **disposition: ship**, with no observed regressions (`landing-finish-review.md`, `landing-verdict.md`). Final viewport/full captures use `landing-{desktop,mobile}-{light,dark}.png` and `landing-{desktop,mobile}-{light,dark}-full.png`; mobile dialog captures use `landing-preview-mobile-{light,dark}.png`. Full captures use a document-height viewport at native CSS resolution to avoid the browser CLI's oversized full-capture canvas.

## Design reasons

Reading: a public product overview for administrators, inside the existing paper-and-ink world, ENERGY 2 / RHYTHM 3 / MOTION 1.

- Color: inherited paper, graphite, and proof blue connect reading and actions to the printing workspace.
- Layout: task-shaped splits, a wide conversation ledger, reference notes, and an ordered workflow explain different review activities without repeating feature cards.
- Typography: IBM Plex Sans preserves the product's voice; larger public headings establish reading hierarchy.
- Spacing: a 4px base, compact detail rows, and generous section gaps distinguish related facts from the next task.
- Frames: quiet borders identify authentic interface captures and their captions as inspectable proof sheets.
- Imagery: actual product screens provide evidence; the labeled print composition gives the workflow its physical printing context.
- Icons: sun/moon, enlargement, close, and loading symbols describe their controls and states.
- Motion: brief hover/selection feedback supports orientation; the existing near-zero reduced-motion convention removes perceptible animation.

## Antislop delivery gate

Mode: **During**. Overall gate: **PASS**. Each item below was checked by the implementing agent against the source and recorded browser evidence.

### Hard gate

| Item | Status and concrete evidence |
| --- | --- |
| R-02, em dashes | PASS: authored landing copy contains no em dash. |
| R-03, mobile layout | PASS: all eight measured widths have `overflow: false`; final phone captures show stacked reading layouts. |
| R-17, statistics | PASS: no promotional statistics; numbers appear inside dated authentic product captures with source provenance. |
| R-18, testimonials | PASS: no testimonials, invented names, or avatar endorsements. |
| R-23, asset authority | PASS: actual screenshots and supporting Codex imagery follow the user's explicit request; the existing logo is reused and the photo is labeled illustrative. |
| R-24, navigation | PASS: all section IDs and administrator destinations exist; 26 links were clicked. |
| R-25, contrast | PASS: ten measured theme/text pairings exceed AA, minimum 5.34:1. |
| R-26, behavior | PASS: links navigate, tabs select captures, images enlarge, dialog buttons open workspaces, Menu/theme toggle, and Retry reloads its image. |
| R-27, states | PASS: preview loading status, actionable unavailable state and retry are implemented and exercised; workspace loading and existing login feedback remain available. |
| R-28, FAQ | PASS: no filler FAQ; actual capability details answer administrator tasks. |
| R-32, keyboard | PASS: Tab/Enter skip-link navigation, Escape closure and focus return, tab semantics, visible focus, and arrow-key image panning were verified. |
| R-33, source implementation | PASS: product behavior and styling are written directly in TSX/CSS; browser scripts only verify and capture the running application. |
| R-34, theme resilience | PASS: light/dark desktop and mobile captures render correctly; theme controls were clicked and scrollbar colors checked in both modes. |
| R-35, run and click-through | PASS: production build, lint, three regressions, 26 page links, eight dialog/fallback links, 14 preview controls, and 18 authentication checks are recorded above. |
| R-36, commercial claims | PASS: no security, compliance, uptime, speed, or customer claims; authentication preservation is demonstrated by tests. |
| R-37, direction | PASS: the surface contract records the inherited world and explicit 2/3/1 dials; the user supplied the requested narrative and features. |
| R-38, realistic content | PASS: capabilities were checked against actual routes/UI; dated captures and benchmark replay have explicit sources. |

### Purpose gate

| Item | Status and concrete evidence |
| --- | --- |
| R-01, gradients/glows | PASS: no decorative gradients or glows; flat inherited theme surfaces. |
| R-04, icons | PASS: only relevant theme, enlargement, close, and loading icons; their reasons are recorded above. |
| R-06, type choice | PASS: IBM Plex Sans inherits the established product face; display hierarchy uses scale/weight, with no oversized monospace or tracked uppercase labels. |
| R-07, background patterns | PASS: no decorative grid, dots, graph paper, or blueprint background. |
| R-08, arrows | PASS: no decorative CTA arrows. |
| R-09, badges | PASS: no promotional capsule or repeated headline label. |
| R-10, glass | PASS: solid page/header surfaces; the shared dialog backdrop separates the temporary preview. |
| R-12, elevation | PASS: sections and capture frames use quiet borders; temporary dialog elevation follows the existing system. |
| R-13, glow saturation | PASS: no glow treatment. |
| R-14, feature repetition | PASS: Knowledge split, reversed Playground, wide Conversations ledger, Providers path, and Evaluations notes use content-specific proportions. |
| R-19, animation | PASS: hover/selection feedback follows MOTION 1; reduced-motion transitions use the existing near-zero duration. |
| R-22, illustration relevance | PASS: the illustrative print proof belongs to the printing workflow; real screens provide product evidence. |

### Liveliness

| Item | Status and concrete evidence |
| --- | --- |
| Explicit dials | PASS: ENERGY 2 / RHYTHM 3 / MOTION 1 is recorded in the public surface contract. |
| Dial consistency | PASS: prominent reading hierarchy, varied task compositions, and restrained interaction feedback match 2/3/1. |
| Focal point | PASS: the opening knowledge thesis leads into the selected proof; each feature's heading and evidence establish the next reading focus. |
| Structural whitespace | PASS: section separation, detail-row cutlines, and mobile stacking group related facts visibly. |
| Deliberate accent | PASS: proof blue identifies actions, selected views, the knowledge thesis, and workflow order. |
| Identity motif | PASS: authentic proof sheets repeatedly pair workspace evidence with source/capture notes. |
| Design Read | PASS: the administrator audience, public overview, inherited paper-and-ink world, and dials were declared before implementation. |

### Craftsmanship and quality locks

| Item | Status and concrete evidence |
| --- | --- |
| C-1, intentionality | PASS: color, layout, typography, spacing, frames, imagery, icons, and motion each have a written purpose. |
| C-2, completeness | PASS: every visible action has a verified route or state change, including error recovery and dialog workspace buttons. |
| C-3, content composition | PASS: all five capability sections and all five workflow stages correspond to real administrator work. |
| C-4, resilience | PASS: both themes, eight widths, native image failure/retry, login validation, keyboard focus, and preview scrolling were checked. |
| C-5, evidence | PASS: product captures and replay are sourced; no invented commercial proof. |
| R-05, template avoidance | PASS: varied task layouts, an authentic preview selector, and the actual five-stage workflow; no logo bar, pricing grid, fake terminal, or uniform feature-card sequence. |
| R-11, corners | PASS: established 8px controls, 12px capture frames, and flat section borders provide radius variation. |
| R-15, CTA specificity | PASS: Open Knowledge/Playground/Conversations/Providers/Evaluations, Open dashboard, and Enter the workspace identify actual destinations. |
| R-16, language | PASS: authored copy explains sources, publication, connection checks, and saved results without AI marketing buzzwords. |
| R-20, identity | PASS: printing-file questions, source passages, knowledge publication, and observed WhatsApp delivery are specific to this product. |
| R-21, theme choice | PASS: light default and a working persisted user toggle inherit the workspace's paper/graphite themes. |
| R-29, palette | PASS: paper/graphite neutrals and one proof-blue accent; existing semantic colors appear within authentic captured UI. |
| R-30, originality | PASS: the existing printing workspace determines the visual vocabulary and proof-sheet structure; no named-product clone. |
| R-31, reasons | PASS: the eight major decision reasons are written above and in the public surface contract. |
