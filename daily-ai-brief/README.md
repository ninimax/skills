# Daily AI and Agentic Engineering Brief

Skill for producing a ranked, dated AI and agentic-engineering brief with live web research, source-quality rules, dedupe, and a portable run log.

## Workflow

On each run, the skill will:

1. Read recent entries from the run log.
2. Search current AI and agentic-engineering news using the source strategy.
3. Select 10 influential AI people based on current newsworthiness.
4. Produce a ranked dated brief.
5. Append a concise run-log entry for future dedupe.

## Related Files

- `SKILL.md`: skill workflow, selection rules, output contract, and run-log format
- `references/source-strategy.md`: source tiers, search loop, candidate scoring, and replacement rule
- `./.daily-ai-brief/run-log.md`: workspace-local run history used for recent-story dedupe
