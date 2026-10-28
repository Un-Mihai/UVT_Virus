# Judging rubric

How the jury will score the project, so the team and its agents can score it first. The seven
criteria follow the official rulebook (section "Evaluation and selection of winners", last updated
28 August 2026). The wording below is ours, and the scoring anchors are this template's reading
of the criteria, not the organiser's.

Before every evaluation run `python3 scripts/judging_criteria.py --show`: it reads the official
pages ([rulebook](https://nexxtsummit.com/rulebook), [agenda](https://nexxtsummit.com/agenda),
[hackathon](https://nexxtsummit.com/hackathon)) and says whether anything changed since
`sources.lock` was recorded. When the criteria, weights or presentation rules change, update this
file in the same change.

## How the score is formed

- Mentors and jurors appointed by the organiser score every team with fixed criteria and a fixed
  mechanism. No weights or scale are published yet; until they are, score each criterion 1 to 5
  with equal weight (total out of 35).
- The challenge partner (Raiffeisen Bank for the operational-efficiency track) may weigh more when
  its own challenge is judged, applied the same way to every team in it.
- Tied teams are compared again on the same criteria.
- Late or incomplete submissions may be left out of the evaluation.

## Criteria

For each criterion: what earns a 5, what keeps a project at 1 or 2, and the evidence to show. A
claim the jury cannot see, run or read scores 2 at most.

### 1. Relevance of the problem and the team's understanding of it

- **5:** a named user in the challenge partner's world, the task they repeat today, how long it
  takes and what mistakes cost, with figures from the challenge brief or a mentor, cited; the demo
  uses the kind of documents that user handles.
- **1–2:** a generic problem ("documents take long"), no user, invented numbers.
- **Evidence:** PRODUCT.md (Users, Product Purpose), the challenge brief below, what mentors said,
  the first 30 seconds of the pitch.

### 2. Clarity of the proposed approach

- **5:** one sentence says what the product does; one diagram shows the flow (documents in,
  extraction with citations, checks, findings, reviewer); it is explicit which steps are AI and
  which are code, and what is out of scope.
- **1–2:** a feature list, or an approach that differs between the pitch, the demo and the code.
- **Evidence:** the flow in the README or on a slide, and code that matches it.

### 3. Originality and innovation

- **5:** a mechanism that a generic "chat with your PDF" tool cannot offer, shown working: for
  example, mismatches between documents computed in code, each traced to its page and quote.
- **1–2:** a thin wrapper around a chat model, or a copy of a known product.
- **Evidence:** the demo moment that shows the mechanism, and a comparison with the obvious
  alternative.

### 4. Technical and operational feasibility

- **5:** deployed and reachable; works end to end on real documents; `make check` green; accuracy
  measured on a small golden set; cost and time per document measured (the `ai_calls` ledger);
  failures handled (scanned pages, timeouts, the daily budget, a provider outage).
- **1–2:** mock-ups, hard-coded results, or a demo that only works on one prepared file.
- **Evidence:** the deployed URL, `/status`, test results, golden-set numbers, the ledger.

### 5. Potential for implementation, adoption and scaling

- **5:** a credible path into the partner's operations: runs in their own Azure tenant through
  Terraform, uses their model endpoint through environment variables, fits their review workflow,
  costs a known amount per document at their volume, names a first pilot team, and says what
  scaling needs (parallel pages, queues).
- **1–2:** no answer to "who uses this on Monday, and what does it cost?".
- **Evidence:** docs/deploy-azure.md, cost figures from the ledger, the adoption slide.

### 6. Effective and responsible use of AI and other technologies

- **5:** AI only where it adds value; sums, dates and identifiers checked in code; every finding
  cites its source and the quote is verified on the page; a person confirms or dismisses each
  finding; personal data masked; data kept in an EU region; every AI call logged; known limits
  stated.
- **1–2:** the model decides alone, findings without sources, personal data sent unmasked, no
  account of how it fails.
- **Evidence:** the document-verification pipeline, the reviewer screen, the ledger, the
  limitations slide.

### 7. Ability to explain and demonstrate the work

- **5:** a three-minute story that lands; a live demo on real data with one memorable moment (a
  real mismatch found); clear answers at the jury checkpoint; the video pitch uploaded before the
  deadline.
- **1–2:** no working demo, an over-long pitch, answers that contradict the demo.
- **Evidence:** rehearsal timing, the recorded video, the jury question drill
  (`hackathon-judge` skill).

## Who evaluates

Mentors and jurors take part in the evaluation. For the Raiffeisen track, the mentors published on
the hackathon page include Raiffeisen Bank Romania's Chief Risk Officer, its Head of AI Practice
and Solutions, and many of its banking machine-learning engineers. Expect questions on risk,
governance, data protection, production readiness and running cost from people who build such
systems.

## When the project is evaluated

From the agenda (Bucharest time). Presentation length, demo rules and question time follow the
instructions the organiser publishes on the agenda page: add them here when they appear.

| When | What |
|---|---|
| Wed 28 Oct, 09:00 | Kick-off and challenge briefing: fill in the next section |
| Wed 28 Oct, 11:30 | Business mentor sessions, 15-minute slots |
| Wed 28 Oct, 14:00 and 18:30 | Mentor checkpoints |
| Wed 28 Oct, 20:00 | Pitch preparation, then building overnight |
| Thu 29 Oct, 09:00 | Morning checkpoint |
| Thu 29 Oct, 10:30 | Project submission and video pitch upload (deadline) |
| Thu 29 Oct, 15:30 | Jury checkpoint: the jury verifies the solution and asks follow-up questions |
| Thu 29 Oct, 17:10 | Finals on the main stage for the strongest teams, then the jury's final vote |
| Thu 29 Oct, 18:00 | Awards |

## Challenge-specific criteria

Fill in at kick-off from the challenge brief: what the challenge partner asks for, any criteria
or weights of its own, and where the text came from (brief, slide, mentor).

- Not available yet.
