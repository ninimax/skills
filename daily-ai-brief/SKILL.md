---
name: daily-ai-brief
description: Produce or maintain a Daily AI and Agentic Engineering brief on a scheduled run. Ranks 10 AI people by current newsworthiness using live web research, dedupes against recent runs, writes concise per-person summaries, and appends a run-log entry.
---

# Daily AI and Agentic Engineering Brief

## Workflow

1. Use `./.daily-ai-brief/run-log.md` as the default durable state file unless the user provides another path. Create it if missing.
2. Read `references/source-strategy.md` before web research.
3. Resolve the run date and timezone from the automation/runtime environment. If the scheduler passes an explicit date or timezone, use it; otherwise use the runtime clock's date and UTC. Record the resolved date and timezone in the run-log entry.
4. Extract the last two runs from the run log: selected people, URLs, and story themes. If the log is new or has fewer than two runs, proceed with whatever history exists (including none) and skip novelty-dedupe against missing runs.
5. Run one broad discovery pass over the trusted source tiers.
6. Build at least 14 candidate people or story-person pairs.
7. Run targeted searches only for missing primary confirmation, weak citations, or important people with unclear freshness. Cap this at about 8 targeted searches; if a candidate still lacks a credible current source after one confirmation attempt, drop it rather than searching further.
8. Stop broad searching once there are 10 distinct high-signal stories with credible current sources.
9. Draft 10 ranked items using the output contract below unless the shortfall fallback applies.
10. If fewer than 10 items clear the source-quality bar, still output the strongest set you have, mark the shortfall at the top of the brief (for example, `8/10 - 2 dropped for weak sourcing`), and record why in the run log. Never pad to 10 with weak or fabricated sources.
11. Append a concise run-log entry with the selected people, major themes, source-quality decisions, resolved date and timezone, any shortfall reason, and workflow notes.
12. Run the verification checks below before finalizing.

Target an 8-10 minute research budget.

## Selection Rules

Score candidates by:

1. Impact on AI agents, agentic engineering, coding agents, model releases, AI safety/governance, infrastructure, open source AI, or major AI business/product moves.
2. Credibility and specificity of the source.
3. Current newsworthiness relative to the resolved run date.
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

Format as a ranked brief with the exact date. Include 10 items unless the shortfall fallback applies.

For each item, include:

1. Person
2. Role/org
3. Why it matters
4. Source link
5. Concise summary

Each summary must be 500 characters or less. Keep the brief concrete and avoid speculative language unless the source itself reports uncertainty.

## Verification

Before finalizing, confirm:

- Item count is 10, or the shortfall is stated at the top of the brief.
- Every item has a resolvable current-source link (no placeholders, no invented URLs).
- Every summary is 500 characters or less.
- No two items share a story theme.
- A run-log entry was appended with the resolved date, timezone, and any shortfall reason.

## Run Log Entry

Use this structure:

```text
## YYYY-MM-DD HH:MM TZ

- Produced/updated:
- Selected people:
- Main themes:
- Source-quality notes:
- Resolved date/timezone:
- Shortfall reason:
- Runtime/workflow notes:
```
