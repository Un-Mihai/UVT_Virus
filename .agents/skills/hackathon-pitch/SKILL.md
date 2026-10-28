---
name: hackathon-pitch
description: Prepare the hackathon demo, pitch and submission for the NEXXT AI Hackathon (Raiffeisen Bank operational-efficiency track) - build order, a 3-minute demo script, honest answers to "who pays for the AI tokens", data privacy and hallucination questions, demo-day safety and the submission checklist. Use when planning what to build first, writing pitch or video material, or rehearsing.
---

# Hackathon pitch and demo

## The event and how it is judged

- NEXXT AI Hackathon, FACE Convention Center, Bucharest, 28–29 October 2026. The rulebook lets
  teams work on their challenge only from the official start.
- The official criteria, the schedule of evaluation moments (submission and video pitch at 10:30
  on 29 Oct, jury checkpoint, finals) and scoring anchors are in `docs/judging/rubric.md`. Run
  `python3 scripts/judging_criteria.py` first: it re-reads the organiser's pages and reports any
  change.
- Use the `hackathon-judge` skill to score the project against them before every checkpoint.

Decide features by the criteria. A narrow flow that works on real documents beats a broad one
that works on none.

## Build order that keeps a demo alive

1. Hour 1: agree on the user, the one document set, and the three checks that matter most; write
   them into PRODUCT.md.
2. First working slice end to end: upload → extracted facts with quotes → one deterministic check
   → finding with evidence on screen. Deploy it (`azure-deploy` skill) the same evening.
3. Then more checks, then the reviewer's confirm and dismiss flow, then polish (`impeccable`).
4. Freeze features three hours before submission. After that: fixes, rehearsal, video.

## Three-minute demo script

1. Problem (30 s): who checks these documents today, how long it takes, what a missed mismatch
   costs (funds cut at settlement). Use a real number from the challenge brief or a mentor;
   never invent one.
2. Live demo (90 s): open a real document set, show the findings, click one to see the quote on
   its page, confirm it as the reviewer. Show one check computed in code ("these two totals
   differ by 1.250,00 lei").
3. Why it can be trusted (30 s): every finding has its source, arithmetic is deterministic, the
   person decides, every AI call is logged with its cost.
4. Business case (30 s): minutes saved per file, measured cost per document (from the
   `ai_calls` ledger on `/status`), how it gets deployed (below).

## Questions the jury will ask

- **Who pays for the AI after the hackathon?** The client. The app calls whatever model
  endpoint its environment variables name, and Terraform deploys the whole stack into the
  client's own Azure subscription, so documents and AI spend stay in their tenant. Quote the
  measured cost per document and the daily budget cap.
- **What about client data?** Deployed in an EU region of the client's tenant; personal data
  masked before model calls; Azure OpenAI does not use customer prompts to train models; every
  call is logged.
- **What if the model hallucinates?** Facts are accepted only when their quote is found on the
  cited page; sums, dates and identifiers are checked in code; nothing is approved without a
  person.
- **How accurate is it?** Answer with the golden set: "on N real files, it found X of Y known
  issues with Z false alarms". If you have not measured, say so.
- **Who can see the documents?** Only signed-in users (Keycloak). In the bank, staff would sign
  in with their company account through Keycloak's identity brokering, and roles decide who may
  approve; the app does not change (docs/auth.md).
- **How does it scale?** Pages are processed in parallel, Container Apps scale out, and the cost
  grows linearly with pages, which the ledger shows.

## Demo-day safety

- Rehearse on the deployed URL with `keep_warm = true`, signed in as the jury will be; keep the
  local Docker stack ready as the backup.
- Process the demo documents once before going on stage.
- If the network fails, show results from an earlier real run and say so. Never show fabricated
  output as live.
- Record the video pitch the night before, while everything works.

## Submission checklist

- [ ] Deployed URL works from a phone on mobile data, sign-in included.
- [ ] The jury has the URL, the user `reviewer` and the demo password.
- [ ] README says what it does, how to run it, and what is real versus mocked.
- [ ] No secrets in the repo (`git grep -i "api_key\|password"` finds only placeholders).
- [ ] Video pitch uploaded before the deadline.
- [ ] `keep_warm` and other paid extras switched off after the finals.
