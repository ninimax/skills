---
name: daily-ai-brief
description: Produce or maintain a Daily AI and Agentic Engineering brief. Use when asked for a ranked dated AI news brief, 10 influential AI people selected by current newsworthiness, live web research, source dedupe, concise per-person summaries, or scheduled automation setup for this recurring brief.
---

# Daily AI and Agentic Engineering Brief

## Workflow

1. Use `./.daily-ai-brief/run-log.md` as the default durable state file unless the user provides another path. Create it if missing.
2. Read `references/source-strategy.md` before web research.
3. Use the current date and the timezone provided by the user, automation, or runtime environment.
4. Extract the last two runs from the run log: selected people, URLs, and story themes.
5. Run one broad discovery pass over the trusted source tiers.
6. Build at least 14 candidate people or story-person pairs.
7. Run targeted searches only for missing primary confirmation, weak citations, or important people with unclear freshness.
8. Stop broad searching once there are 10 distinct high-signal stories with credible current sources.
9. Draft exactly 10 ranked items using the output contract below.
10. Before finalizing, confirm there are exactly 10 items, every item has a credible current source link, every summary is 500 characters or less, and no story themes are duplicated.
11. Append a concise run-log entry with the selected people, major themes, source-quality decisions, and workflow notes.

Target an 8-10 minute research budget.

## Selection Rules

Score candidates by:

1. Impact on AI agents, agentic engineering, coding agents, model releases, AI safety/governance, infrastructure, open source AI, or major AI business/product moves.
2. Credibility and specificity of the source.
3. Current newsworthiness relative to today's date.
4. Influence of the named person.
5. Novelty compared with the last two runs.

Prefer a stronger source over a hotter but weakly sourced claim. If a person has no genuinely important current news, replace them.

Treat these as duplicate stories unless there is a clearly different angle:

1. The same model launch covered through multiple executives.
2. The same policy dispute attributed to both a company and regulator.
3. The same funding, chip, data-center, or partnership news attached to several people.
4. Follow-up commentary that adds no new fact or decision.

Keep the person most directly responsible or most newsworthy for the story, then replace the others.

## Output Contract

Format as a ranked brief with the exact date. Include exactly 10 items.

For each item, include:

1. Person
2. Role/org
3. Why it matters
4. Source link
5. Concise summary

Each summary must be 500 characters or less. Keep the brief concrete and avoid speculative language unless the source itself reports uncertainty.

## Run Log Entry

Use this structure:

```text
## YYYY-MM-DD HH:MM TZ

- Produced/updated:
- Selected people:
- Main themes:
- Source-quality notes:
- Runtime/workflow notes:
```
