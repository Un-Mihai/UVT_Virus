---
name: hackathon-judge
description: Score the project the way the hackathon jury will, against the official criteria re-read from the organiser's pages (nexxtsummit.com rulebook, agenda, hackathon page) plus the challenge brief, and drill the jury's questions. Use before a mentor checkpoint, the submission, the jury checkpoint or the finals, or when asked how the jury would rate the project or what to improve before a deadline. Writes a scorecard with evidence, gaps and next actions.
---

# Judge the project like the jury

A flattering self-assessment costs points later. Score as a sceptical juror from the challenge
partner (for the operational-efficiency track: Raiffeisen's risk, AI and engineering people) who
has seen many prototypes. When you can, run this in a fresh session or subagent that did not
write the code.

## 1. Refresh the criteria, always first

Run `python3 scripts/judging_criteria.py --show`. It prints the current official rules, judging
criteria and hackathon schedule, and says whether any of it changed since
`docs/judging/sources.lock` was recorded.

- **Changed (exit 3):** read the diff or the new text. Update `docs/judging/rubric.md` (the
  criteria in your own words, plus any weights, scale, pitch format or new deadline) and commit it
  together with the refreshed `sources.lock`. Tell the team in one or two lines what changed. The
  rubric must cover exactly the official criteria: never drop one or invent one.
- **Offline (exit 2):** score with the rubric as it is and say so in the scorecard.
- Read the rubric's "Challenge-specific criteria". If it is still empty after kick-off (28 Oct,
  09:00), ask the team for the challenge brief before scoring.

## 2. Gather evidence instead of recalling it

Look at what a juror would see:

- PRODUCT.md and README: the problem, the user, the approach.
- The product itself: open `/` and `/status` locally or on the deployed URL and walk the demo flow
  on real documents, signed in as `reviewer`, with a browser tool if you have one, otherwise with
  `curl` through `node scripts/signed_in.mjs http://localhost:3000 curl ...` (local stack).
- `make check`, and the golden-set results if they exist.
- The `ai_calls` ledger on `/status`: cost and duration per call, failures.
- `git log --oneline -20`: what was actually built.
- Deployment state, a working jury sign-in and `keep_warm` (docs/deploy-azure.md), and whether
  the video pitch exists.

## 3. Score

Use the anchors in `docs/judging/rubric.md`. For each criterion: a score from 1 to 5, the evidence
(file, command, screen), the biggest gap, and the one action that would raise the score most,
with a time estimate. Without evidence a criterion scores 2 at most. Name weak criteria plainly
instead of averaging them away. Use equal weights unless the official pages or the challenge
brief give others, and note that the challenge partner may weigh more in its own challenge.

## 4. Write the scorecard

Save it as `docs/judging/scorecards/<YYYY-MM-DD-HHMM>.md` and summarise it in the chat:

```markdown
# Scorecard <date time>

Criteria: official pages checked <date>; changed: <no / yes, what / offline>.
Challenge brief: <in the rubric / missing>.

| Criterion | Score | Evidence | Biggest gap | Next action (time) |
|---|---|---|---|---|
| 1. Relevance of the problem and understanding of it | | | | |
| 2. Clarity of the approach | | | | |
| 3. Originality and innovation | | | | |
| 4. Technical and operational feasibility | | | | |
| 5. Implementation, adoption and scaling | | | | |
| 6. Effective and responsible use of AI | | | | |
| 7. Explaining and demonstrating the work | | | | |

Total: <n>/35, equal weights.

## Before <next milestone and time>

1. <the action with the most points per hour>
2.
3.

## Questions the jury will ask

| Question | Our answer today | Good enough? |
|---|---|---|
```

If there is an earlier scorecard, say what moved since then.

## Jury question drill

When the team wants to rehearse, play the jury: ask the ten hardest questions, at least one per
criterion, as the challenge partner's risk, AI and engineering people would (cost at the bank's
volume, what happens when the model is wrong, personal data, how it fits their process, why not
an existing product). Grade each answer against the evidence and suggest a better one.
