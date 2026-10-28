---
name: Document checks
description: An evidence-first document workspace with a premium yellow-and-black FinTech identity.
colors:
  canvas: "#f5f5f5"
  surface: "#ffffff"
  surface-2: "#f1f2f3"
  ink: "#141414"
  ink-2: "#525252"
  ink-3: "#696969"
  line: "#e5e5e5"
  line-strong: "#b4b4b4"
  accent: "#ffed00"
  accent-hover: "#edda00"
  on-accent: "#141414"
  focus: "#756900"
  ok: "#227346"
  warn: "#8a5800"
  bad: "#be3030"
typography:
  headline:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  headline-wide:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Atkinson Hyperlegible Next, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
  code:
    fontFamily: "Atkinson Hyperlegible Mono, ui-monospace, monospace"
    fontSize: "0.92em"
rounded:
  control: "10px"
  panel: "12px"
  pill: "9999px"
spacing:
  row-y: "14px"
  panel: "24px"
  panel-wide: "32px"
  section: "40px"
  review-section: "48px"
  page-x: "20px"
  page-x-wide: "40px"
  page-y: "40px"
  page-y-wide: "56px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.control}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 20px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-2}"
  button-quiet:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-quiet-hover:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "24px"
  status:
    backgroundColor: "{colors.surface-2}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
---

# Design System: Document checks

## Overview

**Creative North Star: "The Audit Ledger"**

An evidence-first reviewer's desk with a Raiffeisen-inspired premium FinTech identity: vibrant
yellow actions, deep black navigation, clear white panels and generous space on a light-gray
canvas. Soft shadows and rounded controls give the workspace a confident, tactile finish while
rows, quotes and aligned figures keep document checking precise.

This is an Operate interface. Familiar forms and tables carry the work; visual emphasis helps
people find the next action and its supporting evidence. Motion reports interaction and state.

**Key Characteristics:**

- One self-hosted sans family, with clear identifiers and tabular figures; its mono sibling is reserved for code.
- Yellow action and selection cues, a black account bar, and softly elevated panels.
- Light by default, with system-driven dark mode and original PDFs kept on white paper.

## Colors

The semantic palette lives in `web/src/app/globals.css`; Tailwind's default palette is disabled.

### Primary

- **Signal Yellow** (`accent`): primary actions, selected language and tabs, text selection, progress, and the account-bar and page-header rules. `accent-hover` gives actions a darker yellow hover and active state; `on-accent` keeps their text dark.
- **Focus Gold** (`focus`): a darker outline on light surfaces; dark mode and the account bar use Signal Yellow for focus.

### Neutral

- **Canvas** (`canvas`): the page background. **White Paper** (`surface`): panels, fields and inline notes. **Soft Gray** (`surface-2`): secondary surfaces, table headers, hover and selected finding rows.
- **Deep Ink**, **Soft Ink**, **Faint Ink** (`ink`, `ink-2`, `ink-3`): primary text, supporting copy and quieter metadata.
- **Rule** and **Strong Rule** (`line`, `line-strong`): dividers, table boundaries and field borders.

System dark mode overrides the following values; yellow and its dark text remain unchanged:

| Token | Dark value |
| --- | --- |
| canvas | `#101010` |
| surface | `#1b1b1b` |
| surface-2 | `#252525` |
| ink | `#fafafa` |
| ink-2 | `#c2c2c2` |
| ink-3 | `#a3a3a3` |
| line | `#333333` |
| line-strong | `#606060` |
| focus | `#ffed00` |
| ok | `#79d29c` |
| warn | `#edc16a` |
| bad | `#ff9292` |

**The State-Only Colour Rule.** `ok`, `warn` and `bad` communicate verification or service state;
each state also has a word. Yellow communicates action, selection and identity.

## Typography

Atkinson Hyperlegible Next is the sole interface family, self-hosted from `web/src/app/fonts/`,
with `ui-sans-serif, system-ui, sans-serif` fallbacks. Atkinson Hyperlegible Mono is used only
inside `<code>` for identifiers, URLs and model names. The families distinguish 0/O, 1/l/I and
5/S, which matters when checking IDs and amounts.

- **Headline:** one per page, using `headline`; switches to `headline-wide` from 640px. Balanced wrapping.
- **Title:** `title` for section headings; subordinate regulation headings use 18px semibold text.
- **Body:** `body`; leads use relaxed line height (1.625) and supporting text uses Soft Ink. Reading copy is capped at 65ch.
- **Label:** `label` for fields and table headers; primary buttons use bold (700), secondary buttons semibold (600), quiet actions and status words medium (500).
- **Numbers:** tabular figures; numeric table columns are right-aligned. Dates, durations and money use `web/src/lib/format.ts`.

**The One Voice Rule.** Keep the sans family throughout the interface; reserve its mono sibling for code.

## Layout

General pages use a centered column (maximum 72rem). Horizontal gutters grow from 20px to 40px
at 640px; vertical page padding grows from 40px to 56px there. Main panels are generally 40px
apart; the findings section uses 48px. Panels have 24px internal padding, increasing to 32px at
640px. Forms stay within 48rem and related fields become two columns at 640px.

Page headers use a bottom divider and short yellow rule (48px wide, 4px high). Actions sit below
the title with a 24px gap, moving alongside it at 1024px. The account bar spans the viewport;
its contents cap at 90rem and wrap, with account controls on their own row below 640px.

**The workspace exception.** `/{lang}/projects/[id]` expands to 90rem from 1280px. At 1024px the
review splits into a findings column (20–26rem) and a flexible PDF column with a 24px gap;
each pane can scroll within `calc(100dvh - 6rem)`. Below 1024px they stack, findings first.
Tables scroll horizontally on narrow screens. Long identifiers and filenames wrap where needed.
Paragraphs use pretty wrapping.

**Languages.** Screens exist under `/en/...` and `/ro/...`. The account-bar switcher uses plain
links with `hrefLang`; the current language is marked with `aria-current` and yellow fill.
Interface strings live in both dictionaries under `web/src/i18n/dictionaries/`; diagnostic
report content on `/status` remains English. Document quotes retain their source language.

## Elevation & Depth

White panels lift softly from the gray canvas; borders and tonal surfaces still separate rows
and fields. Shadows stay diffuse, without decorative blur or hard offsets.

- **Card:** `0 4px 24px -8px rgb(0 0 0 / 10%)`; dark mode uses 35% opacity. Used on the main panels.
- **Action:** `0 3px 8px -3px rgb(0 0 0 / 22%)`; dark mode uses 45% opacity. Used on primary buttons and active PDF notes. Disabled primary buttons remove their shadow.

Color changes use 150ms transitions; table-row hover uses `ease-out`. Reduced-motion preferences
reduce animation and transition durations to 0.01ms and disable smooth highlight scrolling.

## Shapes

Controls, fields, document pages and inline PDF notes use the control radius. Main panels use
the panel radius. Status badges, progress tracks and dots are fully rounded. Fields and document
pages retain hairline borders; panels rely on their surface and shadow. Tables use horizontal
rules without a rounded outer frame.

## Components

### Buttons and links

Confident, compact actions with clear hierarchy. Primary buttons have yellow fill, dark bold
text, an action shadow and a minimum height of 44px. Secondary buttons share the size with a
Strong Rule border and semibold text; hover strengthens the border and fills Soft Gray. Quiet
actions have a 40px minimum height and turn from Soft Ink to Deep Ink on a Soft Gray hover.

All receive the global focus-visible outline (2px, offset 3px). Disabled actions use 70% opacity
and a progress cursor; running labels name the current action. Content links use semibold Deep
Ink and a yellow underline (2px), which turns to Deep Ink on hover.

### Panels, tables and status

Panels group substantial tasks with the shared surface, radius, padding and card shadow.
Inside them, lists remain hairline-divided rows rather than nested cards. Tables have top and
bottom hairlines (1px, Rule), row dividers, Soft Gray headers, semibold Soft Ink headings, 16px
vertical cell padding and a row hover/focus-within fill.

Status badges pair an 8px colored dot with a word, using a pill-shaped Soft Gray background.
Service rows keep name, detail and status aligned; error details explain the next step.

### Forms

Labels sit above fields, with required text in Faint Ink and hints or inline errors below.
Controls have a minimum height of 48px, a Strong Rule border and the shared surface. Hover
strengthens the border; focus uses Focus Gold; invalid fields use `bad`. Disabled fields use
70% opacity and a not-allowed cursor. Errors retain the input and name the recovery. Irreversible
actions confirm inline with a sentence and two buttons. File uploads list each file's outcome.

### Account bar and navigation

The account bar stays black in both modes, with a yellow lower rule (3px). Its scoped colors are
surface `#111111`, secondary surface `#292929`, primary text `#ffffff`, supporting text
`#c4c4c4`, faint text `#aaaaaa`, line `#383838` and strong line `#606060`. Navigation and sign-out
controls use the scoped hover surface and yellow focus. The existing yellow checkmark icon
(`/icon.svg`) precedes the app name at 32px; keep this identity asset rather than inventing a bank logo.

Admin regulation navigation uses yellow selected tabs. Administrators pick all projects, a
project type, or one project, then switch between separately named client and reviewer rules.
PDF rows show OCR/indexing state and offer reprocessing after failure.

### Document review workspace

The left panel contains findings for the active role's rule set and threshold. Each row shows
the severity word, tabular confidence percentage, source document/page/quote, reason and
recommendation; PDF regulation citations link to their source file and page. Selected findings
use Soft Gray and a one-pixel inset focus-colored outline. OCR evidence carries its text label.

The right pane renders the **original PDF** on a white canvas in either theme, with highlight
boxes layered over it; the annotated PDF remains a separate download. Selecting a finding
scrolls to `#finding-{id}` and moves keyboard focus there. Error highlights use `bad` at 25%
(40% on hover), warnings `warn` at 30% (45% on hover); the active highlight adds a 2px state
outline and an inline note above or below the passage. Selecting it again closes the note.

## Do's and Don'ts

### Do:

- **Do** keep every finding beside its document, page and exact quote.
- **Do** use semantic tokens and shared controls for new screens.
- **Do** preserve English and Romanian layouts, visible focus, state words and reduced-motion behavior.
- **Do** keep original PDF pages white and evidence highlights legible in both themes.
- **Do** write empty states and errors that explain the next action.

### Don't:

- **Don't** add Tailwind palette colors; add a semantic token and document it with the source.
- **Don't** use gradient text, glass, decorative blur, emoji icons or labels above page headings.
- **Don't** nest cards inside task panels or replace dense tables with equal-size icon cards.
- **Don't** use invented metrics, documents or findings as visual decoration.
