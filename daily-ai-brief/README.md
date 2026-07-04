# Daily AI and Agentic Engineering Brief

This package contains a skill for producing a ranked, dated AI and agentic-engineering brief with live web research, source-quality rules, dedupe, and a portable local run log.

## Install

Place the `daily-ai-brief` folder in your skills directory, then restart or refresh your agent environment if needed.

The skill uses this local state file by default:

```text
./.daily-ai-brief/run-log.md
```

Keep the automation workspace pointed at the folder where you want that run log to live.

## Codex Automation Prompt

Use this prompt when creating a scheduled Codex automation:

```text
Use $daily-ai-brief to create today's Daily AI and Agentic Engineering brief. Use or create ./.daily-ai-brief/run-log.md as the portable run log, use up-to-date web research, prioritize trusted source tiers, avoid duplicate stories and recent repeats, choose 10 influential AI people based on current newsworthiness, keep each summary under 500 characters, update the run log, and finish in about 8-10 minutes.
```

Choose any schedule that fits your workflow. The skill is not tied to a time of day.

## What The Automation Should Do

The automation should run in a workspace where it can read and write the run log. On each run, the skill will:

1. Read recent entries from the run log.
2. Search current AI and agentic-engineering news using the source strategy.
3. Select 10 influential AI people based on current newsworthiness.
4. Produce a ranked dated brief.
5. Append a concise run-log entry for future dedupe.

## Files

- `SKILL.md`: agent-facing workflow
- `references/source-strategy.md`: source tiers and search policy
