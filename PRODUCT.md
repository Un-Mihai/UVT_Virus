# Product

<!-- impeccable:product-schema 1 -->

Fill in the open decisions as soon as the team settles them; every agent reads this file.

## Platform

web

## Users

Open decision: the challenge track is confirmed on 27 October 2026. The working assumption is
staff who check large sets of documents by hand, such as bank teams reviewing documentation for
investment projects or procurement files before money is released.

Everyone signs in (docs/auth.md). The realm has two roles, `reviewer` and `admin`. Open decision:
what each role may do; no route checks a role yet.

## Product Purpose

Help people verify documents for public procurement and investment projects faster. The product
reads the documents in a file, finds inconsistencies between them (amounts, dates, parties,
identifiers, required documents) and shows each finding with the page and quote it comes from, so
a person can confirm or dismiss it. Errors caught before submission avoid funds being cut at
settlement because documents do not match.

Success: a reviewer reaches the same conclusions in a fraction of the time, and every flagged
inconsistency can be traced to its source in one click.

## Positioning

Open decision. Candidate: evidence-first verification. Every finding carries its source quote and
page, and the checks that matter (sums, dates, identifiers) are computed in code, not guessed.

## Operating Context

- Documents are mostly Romanian PDFs: many are scans, many are long, tables carry the amounts.
- Hackathon: NEXXT AI Hackathon, Bucharest, 28–29 October 2026, track "Raiffeisen Bank —
  Operational Efficiency: AI agents that reduce repetitive work involving documents, data and
  verification". Submission and video pitch are due on the second morning.
- AI runs on whatever endpoint `.env` names (organiser tokens, Azure for Students credits via
  Azure AI Foundry, or another OpenAI-compatible provider), so the client can bring their own.

## Capabilities and Constraints

- Proposed (confirm): the cost per checked document is measured and shown, from the `ai_calls`
  ledger.
- Proposed (confirm): personal data such as CNPs and private persons' IBANs is masked before it
  reaches a model unless the check needs it.
- Open decision: which document types and which checks the demo covers.
- Open decision: whether reviewers can correct an extracted value and re-run the checks.

## Evidence on Hand

None yet. Use real public procurement documents (published on SEAP/SICAP) or documents the
challenge partner provides. Never invent documents, findings, customers or metrics; label any
synthetic demo data as synthetic.

## Product Principles

Proposed; confirm or rewrite as a team.

1. Every finding shows its evidence: document, page, exact quote.
2. People decide; the product never approves or rejects on its own.
3. Code computes, the model reads: arithmetic and comparisons are deterministic.
4. Cost and speed per document are visible, not promised.

## Accessibility & Inclusion

Open decision: interface language (Romanian, English or both). Proposed baseline: WCAG 2.2 AA
contrast, every status conveyed by text and not colour alone, a review flow that works with the
keyboard only.
