# Daily AI and Agentic Engineering Brief

Codex skill for producing and publishing a ranked, dated AI brief through a bounded, stateful workflow graph.

```text
load state -> parallel discovery -> normalize -> verify -> score/dedupe
           -> quality gate -> render -> validate -> publish/update
           -> live verify -> persist success -> done
```

Targeted research, artifact repair, publication retry, and live verification are bounded backedges. A run can finish as `done`, `blocked`, `publish_failed`, or `failed`. Only a live-and-archive-verified `done` run enters the portable Markdown success history.

The primary artifact remains `./daily-ai-brief-YYYY-MM-DD.html`. Structured attempt state lives under `./.daily-ai-brief/runs/`. The existing `./.daily-ai-brief/run-log.md` format remains readable, and new entries add URL and graph fields only after end-to-end success.

## Files

- `SKILL.md`: execution, publication, HTML, and persistence rules
- `references/workflow-graph.json`: versioned nodes, edges, budgets, and terminal contracts
- `references/run-state.schema.json`: structured state, source, trace, artifact, and publication schema
- `references/source-strategy.md`: source tiers, parallel discovery, scoring, and dedupe
- `scripts/validate_run.py`: dependency-free deterministic validator
- `tests/test_validate_run.py`: validator and graph-transition tests
