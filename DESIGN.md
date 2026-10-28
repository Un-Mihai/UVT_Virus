---
name: Hackathon starter
description: A calm, evidence-first workspace for checking documents.
colors:
  surface: "oklch(0.985 0.004 95)"
  surface-2: "oklch(0.962 0.006 95)"
  ink: "oklch(0.24 0.014 255)"
  ink-2: "oklch(0.43 0.014 255)"
  ink-3: "oklch(0.53 0.012 255)"
  line: "oklch(0.9 0.006 95)"
  line-strong: "oklch(0.8 0.008 95)"
  accent: "oklch(0.46 0.13 258)"
  accent-hover: "oklch(0.4 0.13 258)"
  on-accent: "oklch(0.985 0.004 95)"
  ok: "oklch(0.5 0.12 155)"
  warn: "oklch(0.56 0.12 70)"
  bad: "oklch(0.52 0.18 27)"
typography:
  headline:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
  code:
    fontFamily: "Atkinson Hyperlegible Mono, ui-monospace, monospace"
    fontSize: "0.92em"
rounded:
  control: "6px"
  pill: "9999px"
spacing:
  row: "14px"
  section: "48px"
  page-x: "20px / 40px from 640px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-quiet:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "6px 10px"
  button-quiet-hover:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
---

# Design System: Hackathon starter

## Overview

**Creative North Star: "The Audit Ledger"**

A reviewer's desk, not a dashboard. Pages read like a well-kept ledger: rows separated by hairlines,
quiet surfaces, numbers that line up, and colour reserved for state. The interface should disappear
into the task of checking documents; trust comes from precision, not decoration.

Density is welcome where people compare values. Motion only reports state changes.

**Key Characteristics:**
- One sans family (Atkinson Hyperlegible Next) for everything, with tabular figures for numbers;
  its mono sibling only inside `<code>` (identifiers, URLs, model names). Both keep 0/O, 1/l/I
  and 5/S apart, which matters when checking IDs and sums.
- Warm paper surfaces, cool ink text, one blue accent for actions and selection.
- Light by default (offices, daytime), dark when the system asks for it.

## Colors

Tokens live in `web/src/app/globals.css`; Tailwind's default palette is disabled, so these are the
only colours that exist. Dark-mode values are defined there under `prefers-color-scheme: dark`.

### Primary
- **Ledger Blue** (`accent`): primary actions, focus rings, text selection, the caret, progress.
  Never decoration.

### Neutral
- **Paper** (`surface`) and **Shelf** (`surface-2`): page and secondary panels or tracks.
- **Ink** (`ink`), **Ink Soft** (`ink-2`), **Ink Faint** (`ink-3`): text, descriptions, table
  headers. All pass 4.5:1 on Paper.
- **Rule** (`line`) and **Rule Strong** (`line-strong`): hairlines between rows and under headers.

### Named Rules
**The State-Only Colour Rule.** `ok`, `warn` and `bad` mark state (a status dot, a failed call, an
inconsistency). Each state also has a word; colour is never the only signal.

## Typography

- **Headline** (600, 1.5rem, tracking -0.025em): one per page.
- **Title** (600, 1.125rem): section headings. No labels or eyebrows above headings.
- **Body** (400, 1rem, 1.5): descriptions, capped at 65ch.
- **Label** (500, 0.875rem): table headers, statuses, button text.
- **Code** (mono, `<code>` only): identifiers, URLs, environment variables, model names.
- **Numbers**: the sans with tabular figures (`tabular-nums`), right-aligned in tables.

## Layout

Single column, max 64rem, 20px side gutters (40px from 640px). Sections are separated by 48px and
a heading, not by boxes. Lists are hairline-divided rows; tables scroll horizontally on phones
rather than collapsing into cards. Header actions sit beside the title from 1024px and below it on
smaller screens.

## Elevation & Depth

Flat. Depth comes from tonal surfaces (Paper vs Shelf) and hairlines. No shadows at rest; if an
overlay (menu, dialog) needs one, use a single soft offset shadow and document it here.

## Shapes

Controls have 6px corners; progress tracks and status dots are fully rounded. No cards around
sections; a panel, when unavoidable, uses Shelf with 8px corners and no border plus shadow combo.

## Components

### Buttons
- **Primary:** Ledger Blue fill, on-accent text, 6px corners, 8px 16px padding, semibold label
  that names the action ("Run AI check", not "Submit").
- **Quiet:** no fill, Ink 2 text, 6px corners, 6px 10px padding; Surface 2 fill and Ink text on
  hover. For actions around the work rather than in it, such as Sign out in the account bar.
- **Hover / Focus:** darker blue in 150ms; 2px blue focus ring offset 2px.
- **Loading / Disabled:** label changes to the running action ("Checking…"), 70% opacity,
  `cursor: progress`.

### Status rows
Dot, name, detail, status word. The detail teaches the next step when something is wrong
("Set AI_BASE_URL and AI_API_KEY in .env, then restart the API.").

### Tables
Hairline rows, Ink Faint headers, tabular numbers right-aligned, durations and money formatted by
`web/src/lib/format.ts`.

### Admin regulation editor (`/admin/regulations`)
Administrators pick a funding project type, then switch cleanly between two rule sets: the
**Client Verification Rules** (the applicant's pre-submission regulation) and the **Reviewer
Verification Rules** (the internal audit regulation). Only one set is editable at a time and the
active one is named in the page.

### Document review workspace (`/projects/[id]`)
A two-pane ledger split:

1. **Left pane, highlights-only list.** A hairline-divided vertical list of the flagged findings
   for the active role's rule set and confidence threshold, and nothing else. Each row shows the
   status (`bad` or `warn`, always with its word), the confidence as a tabular percentage
   (`92%`), the document name, the page number, the exact quote, the error reason and the change
   recommendation.
2. **Right pane, highlighted document viewer.** Renders the highlighted file provided by the
   backend, in context.

**Jump to location.** Clicking a row in the left list scrolls the viewer smoothly to the exact
page and highlight anchor (`#finding-{id}`) and moves focus there. The passage is highlighted and
its reason and recommendation appear inline.

## Do's and Don'ts

### Do:
- **Do** show the source (document, page, quote) next to every finding.
- **Do** write empty states that say what to do next.
- **Do** theme the browser's own surfaces: selection, caret, focus ring, scrollbars.

### Don't:
- **Don't** add Tailwind palette colours (`text-gray-500`, `bg-purple-600`); add a token instead.
- **Don't** use gradient text, glass, decorative blur, or emoji as icons.
- **Don't** wrap sections in cards or nest cards.
- **Don't** use a big-number "hero metric" block; numbers live in sentences and tables.
