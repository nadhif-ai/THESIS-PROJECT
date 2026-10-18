---
name: Asia Visual Grafika Admin Workspace
description: A paper-and-ink workspace for reviewing and publishing printing guidance.
colors:
  paper: "#f8f7f4"
  ink: "#202927"
  press-blue: "#29577a"
  press-blue-hover: "#1c4566"
  proof-tint: "#e8eef3"
  cutline: "#deddd7"
  desk: "#f0efeb"
  sheet-white: "#ffffff"
  muted-ink: "#5b6365"
  danger: "#9f3838"
  input-line: "#858c8d"
  control-paper: "#f5f5f2"
  success: "#2f654b"
  success-surface: "#edf4ee"
  warning: "#75521c"
  warning-surface: "#faf0dd"
  danger-surface: "#fcf0ef"
  paper-dark: "#171d22"
  ink-dark: "#eff0eb"
  press-blue-dark: "#9cc4dd"
  press-blue-hover-dark: "#aed5e9"
  proof-tint-dark: "#283946"
  cutline-dark: "#354049"
  desk-dark: "#232b31"
  card-dark: "#1d252b"
  popover-dark: "#26313a"
  primary-ink-dark: "#16222a"
  muted-ink-dark: "#b1bcc2"
  danger-dark: "#f2aaa6"
  input-line-dark: "#76858f"
  control-dark: "#141b20"
  success-dark: "#a7d1b5"
  success-surface-dark: "#243a30"
  warning-dark: "#e8c688"
  warning-surface-dark: "#3d3323"
  danger-surface-dark: "#3a2729"
typography:
  display:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  title:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "20px"
    fontWeight: 500
    letterSpacing: "-0.02em"
  panel:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.375
  body:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  xl: "12px"
  2xl: "16px"
spacing:
  unit: "4px"
  xs: "8px"
  control-gap: "12px"
  sm: "16px"
  compact: "20px"
  md: "24px"
  lg: "32px"
  page-gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.press-blue}"
    textColor: "{colors.sheet-white}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
  button-outline:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.proof-tint}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
  input:
    backgroundColor: "{colors.control-paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "4px 10px"
    height: "44px"
  status-chip:
    backgroundColor: "{colors.success-surface}"
    textColor: "{colors.success}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
    height: "24px"
  card:
    backgroundColor: "{colors.sheet-white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.xl}"
    padding: "24px"
  nav-item:
    backgroundColor: "{colors.proof-tint}"
    textColor: "{colors.press-blue}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 12px"
    height: "44px"
  proof-record:
    backgroundColor: "transparent"
    textColor: "{colors.muted-ink}"
    typography: "{typography.body}"
  table:
    backgroundColor: "{colors.sheet-white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "16px 12px"
---

# Design System: Asia Visual Grafika Admin Workspace

## Overview

**Creative North Star: "Paper + ink workspace"**

This admin workspace brings the printing desk into daily review work: paper-like surfaces, graphite text, restrained proof-blue actions, quiet cutlines, and readable status marks. One IBM Plex Sans family keeps Indonesian customer questions, filenames, metadata, and operational figures in a consistent voice. The graphite dark theme preserves the same hierarchy for longer review sessions.

The recurring visual signature is a proof record: version, observed state, evidence, and next action stay close enough to review together. Each task gets the shape that helps it: cards group summaries, tables hold records, evidence sits beside answers, and checklists show connection readiness. The sign-in story uses the generated mark at `frontend/src/assets/brand-mark.png` and illustrative printing-desk image at `frontend/src/assets/printing-desk.jpg`; [image prompts and provenance](frontend/src/assets/image-prompts.md) confirm the photo is not a record of the shop premises.

The approved admin dials remain ENERGY 1 / RHYTHM 2 / MOTION 1. The 4px spacing base aligns document and control groups, while larger gaps separate work areas.

**Key Characteristics:**
- Paper, graphite, and quiet borders carry most of the screen; blue marks actions, focus, and current proof.
- Version, state, evidence, and next action form one recurring review unit.
- Task-specific columns, tables, and checklists keep operational work ahead of decorative metrics.

## Colors

The palette pairs warm paper and graphite with a single proof-blue identity accent; the dark theme shifts those roles into cool graphite surfaces while keeping status colors legible.

### Primary

- **Press Blue** (press-blue): the established identity color for primary actions, active navigation, visible focus, links, and current evidence.
- **Proof Tint** (proof-tint): a pale selection and evidence surface that keeps blue relationships quiet.

### Neutral

- **Paper and Graphite** (paper, ink): the default canvas and primary text.
- **Sheet White** (sheet-white): cards, popovers, and light-theme button text.
- **Desk and Cutline** (desk, cutline): muted control surfaces and the thin boundaries between panels, rows, and fields.
- **Muted Ink** (muted-ink): metadata and supporting copy.
- **Dark Paper and Ink** (paper-dark, ink-dark): the graphite alternative canvas and its high-contrast text.
- **Dark Proof, Desk, and Cutline** (proof-tint-dark, desk-dark, cutline-dark): selected, muted, and boundary surfaces in dark mode.
- **Dark Card and Popover** (card-dark, popover-dark): raised reading surfaces in dark mode.

### Named Rules

**The Proof Blue Rule.** Keep the accent attached to an action, active selection, focus, or evidence relationship; let neutral surfaces carry the rest of the screen.

**The Status Palette Rule.** Pair success, warning, and danger colors with explicit readable labels so state never depends on hue alone.

## Typography

**Display Font:** IBM Plex Sans (with a sans-serif fallback)  
**Body Font:** IBM Plex Sans (with a sans-serif fallback)  
**Label/Mono Font:** Labels use IBM Plex Sans; there is no separate mono face.

**Character:** A compact, neutral sans-serif voice lets operational labels and customer language share one clear hierarchy. Weight, size, and muted ink distinguish levels without introducing a second display style.

### Hierarchy

- **Display** (typography.display): the sign-in statement and the strongest single reading moment.
- **Headline** (typography.headline): page names and high-level task headings.
- **Title** (typography.title): major section headings.
- **Panel** (typography.panel): compact card and panel titles.
- **Body** (typography.body): instructions, questions, answers, evidence, and record values.
- **Label** (typography.label): metadata, table headings, and status chips. Use tabular figures for counts, times, and scores.

### Named Rules

**The One Family Rule.** Keep headings, body copy, controls, and labels in IBM Plex Sans; create hierarchy with scale, weight, and ink contrast.

## Layout

The admin shell places a persistent left navigation rail beside a top workbar and a centered content region. The main region caps at 1440px; desktop gutters use spacing.page-gutter, while narrower screens reduce the gutter. The rail defaults to a 72px icon state and expands to 248px. The mobile version uses a drawer.

Keep the six workspace destinations available in the rail. The dashboard and provider checks use asymmetric columns; Playground gives the conversation more width than its evidence column. At 1023px and below, multi-column work areas stack. At 767px and below, controls become full-width or wrap, secondary table columns give way to mobile records, and the sidebar becomes a drawer. The spacing vocabulary uses the 4px base, 12px control gaps, 24px panel interiors, and 32px between work areas.

## Elevation & Depth

The workspace is flat at rest: content panels use tonal surfaces and a quiet border ring, while shadows belong to transient dialogs, menus, and the mobile drawer. Sidebar motion stays subtle and state-led; reduced-motion preferences clear its duration and label reveal delay.

### Shadow Vocabulary

- **Dialog and sheet** (0 10px 15px -3px var(--tw-shadow-color, #0000001a), 0 4px 6px -4px var(--tw-shadow-color, #0000001a)): the broad shadow for modal and drawer layers.
- **Select menu** (0 4px 6px -1px var(--tw-shadow-color, #0000001a), 0 2px 4px -2px var(--tw-shadow-color, #0000001a)): the tighter lift used by transient option lists.

### Named Rules

**The Flat Surface Rule.** Keep cards and tables grounded by surface changes and borders; reserve lift for layers that temporarily sit above the work.

## Shapes

Controls and navigation use softly rounded corners; cards use the broader panel radius, while status labels remain compact and squarer. Borders define fields and table rows. Focus is visible through the blue ring and offset outline. Interactive targets keep at least 44px of height, and small supporting rows wrap rather than clip.

## Components

### Buttons

Buttons feel direct and usable. The primary action uses press-blue with contrasting text; outline actions sit on the canvas and gain a muted hover surface; secondary actions use proof tint; ghost actions remain quiet until hover. All variants share the same target height and focus treatment. Destructive actions retain their distinct danger color and confirmation context.

### Chips

Status chips are compact labels with a restrained fill and readable text. Use green for ready, completed, and published; amber for waiting; red for failures and uncertain delivery; use proof tint for active work and desk tint for neutral states.

### Cards / Containers

Cards group information without becoming dashboard decoration. Use them for a coherent summary or work area, with a thin boundary ring and no resting shadow. Tables, evidence, and operational checklists keep their own structure instead of being forced into equal cards.

### Inputs / Fields

Fields use a quiet control surface and visible border. Focus strengthens the blue border and ring; invalid and disabled states retain clear text contrast and a distinct boundary. Keep labels adjacent to their controls.

### Navigation

The sidebar keeps the workspace tasks available in both its collapsed icon rail and expanded labelled form. On desktop, the 72px and 248px states keep icon centers at 36px with 44px targets; the rail and content spacer transition together over 220ms with cubic-bezier(0.32, 0.72, 0, 1), and native transitions reverse from their current position. Brand, account, and navigation labels fade over 120ms, with a 60ms reveal delay. The group heading folds from 32px to zero; the footer note folds through a 1fr-to-0fr grid track at its expanded width so its copy does not rewrap mid-transition. The active item uses the proof tint and press-blue; collapsed items retain tooltips. On mobile, the same navigation opens as a drawer, closes after a destination is chosen, and returns focus to its trigger after Escape. Workspace search opens with Ctrl/Cmd+K and restores focus to its trigger when dismissed.

### Proof Record

Keep version, observed state, evidence, and next action in one compact row that can wrap without hiding its meaning. Reuse this pattern in publication review, conversation inspection, connection checks, and result review.

### Login

Keep the sign-in story beside a single focused form on wide screens and stack them on mobile. The printing-desk image is an illustrative supporting image, not evidence of the shop's real premises.

## Do's and Don'ts

### Do:

- **Do** keep the proof record's version, state, evidence, and next action together.
- **Do** show recorded counts, current phase, and observed check times where they exist; keep unavailable values explicit.
- **Do** use one knowledge source list with a prominent Sync knowledge action. Show pending changes, edit locking and observed progress. Playground and new evaluations always use synchronized knowledge; snapshot IDs belong to read-only result provenance.
- **Do** show loading, empty, and retryable error states with plain task language.
- **Do** keep provider configuration, session state, worker state, queue state, and delivery results distinguishable.
- **Do** keep evaluation references and per-case metrics readable beside each case.
- **Do** preserve the skip link, visible keyboard focus, proof-blue selection and caret, readable dark-theme text, and the 44px interaction target.

### Don't:

- **Don't** add a promotional hero or equal-weight metric cards ahead of the work that needs attention.
- **Don't** invent progress percentages or completion estimates; show only work that has been recorded.
- **Don't** rely on color alone for state or compress evidence into decoration.
- **Don't** present the illustrative printing-desk image as a photograph of the business premises.

