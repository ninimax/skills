---
name: daily-ai-brief
description: Produce or maintain a scheduled Daily AI and Agentic Engineering brief as a versioned, stateful workflow graph. Use for live research, ranked standalone HTML editions, recent-run dedupe, bounded recovery loops, verified publication updates, safe execution traces, and fail-closed success history.
---

# Daily AI and Agentic Engineering Brief

## Contracts

Before each run:

1. Read `references/workflow-graph.json` as the authoritative nodes, edges, budgets, and terminal-state contract.
2. Read `references/run-state.schema.json` when creating or resuming structured run state.
3. Read `references/source-strategy.md` before web research.

Do not add an orchestration framework. Execute the graph with the available tools and use the bundled validator for deterministic gates.

## People-first editorial guardrail

Rank consequential people, not convenient papers. Require evidence that each person made, led, authored, maintained, or is directly accountable for the dated action. Do not automatically promote a paper's first author or attach a CEO to an unrelated company event.

Before selecting, scan all four discovery channels: official company/product announcements; engineering blogs and major open-source maintainer releases; independent original reporting; and research/lab publications. Include at least 14 genuine person/story pairs and record which channels were checked. Exclude future-dated candidates rather than counting them toward a historical edition's slate.

Apply influence and direct agency first, then AI-builder relevance, source specificity, freshness, and novelty. Preserve any required numeric score arithmetic, but do not let retrieval convenience determine the shortlist. A complete edition needs at least eight core builders, executives, researchers, product/engineering leaders, or major maintainers, with at most two independently consequential policy/legal/geopolitical entries.

Do not infer ethnicity or nationality from names, set demographic quotas, or exclude people based on perceived identity. Correct narrow sourcing by broadening discovery and evaluating agency, not by demographic balancing.

Do not default to an arXiv-only or research-only edition. If papers dominate, explicitly compare them against the strongest verified product, engineering, maintainer, and executive actions. Keep research when it genuinely wins on consequence and agency. Disclose a research-heavy edition and the sourcing reason; do not impose an arbitrary paper cap or pad with weak industry news.

Use today/yesterday, then the edition's current week. Keep historical editions free of later findings by reading the original source or dated revision. Reject repeated events even when a new person or URL is attached. Publish an honest shortfall only after the broad channels and bounded confirmation pass have been tried; distinguish unavailable evidence from an exhausted news supply.

## Runtime State

Use these workspace-relative defaults unless the scheduler provides alternatives:

- HTML artifact: `./daily-ai-brief-YYYY-MM-DD.html`
- Attempt state: `./.daily-ai-brief/runs/<run-id>.json`
- Successful history: `./.daily-ai-brief/run-log.md`

Resolve the run date and timezone from explicit scheduler values, then the runtime environment, then UTC. Use one stable run ID for retries and recovery.

Write attempt state atomically with a same-directory temporary file and replacement. Persist operational states such as `blocked`, `publish_failed`, and `failed`, but never treat them as successful history. Keep each trace event to the allowlisted schema fields. Record counts, routes, durations, attempts, reason codes, and errors only. Never store prompts, raw responses, source bodies, credentials, headers, secrets, private reasoning, or chain-of-thought.

## Execute Graph v1

Follow only edges declared in `references/workflow-graph.json`:

1. `load_state`: Read up to two recent successful run-log entries. Extract people, themes, and source URLs. Accept legacy entries without v1 fields, but require URLs in every new v1 success entry. Verify any preconfigured publication adapter read-only.
2. `parallel_discovery`: Run the primary, independent-reporting, and specialist branches concurrently when tools allow. Join their results into at least 14 candidate person-story pairs.
3. `normalize`: Canonicalize URLs, normalize themes, and assign stable story fingerprints.
4. `verify_sources`: Confirm dates, source tiers, HTTPS URLs, and consequential claims. Allow at most one confirmation search per candidate.
5. `score_dedupe`: Apply the deterministic score in the source strategy. Reject duplicate people, normalized themes, story fingerprints, and canonical URLs.
6. `quality_gate`: Select up to 10 qualified candidates. Route through `targeted_research` only while both targeted budgets remain. If fewer than 10 survive after budget exhaustion, declare the shortfall and continue without padding.
7. `render`: Write the standalone HTML artifact and compute its SHA-256 plus the ordered-content fingerprint defined by the validator.
8. `validate`: Set the current node to `validate` with `artifact.validated` false, then run the bundled validator. On success, set it true with the validation timestamp. Use the single repair backedge only for a repairable artifact failure.
9. `publish_update`: Use only a verified, preconfigured adapter that publishes the exact validated edition and returns the same content fingerprint. Keep the payload fingerprint and idempotency key unchanged across retries.
10. `live_verify`: Independently read both the live edition and its immutable archive entry. Compare their date, ordered people, canonical URLs, item count, and content fingerprint with the local state.
11. `persist_success`: Before writing history, run the validator with current node `persist_success` to recheck artifact, live, and archive proof. Use the pending-append recovery protocol below, then mark the state `succeeded` at `done` and run the validator again.

Update `revision`, `node_status`, budgets, trace, and errors after every node handoff.

## Publication Boundary

Distinguish the two publication modes:

- `content_refresh`: Update edition content through an existing adapter without saving or deploying site code. Use this for normal daily editions.
- `full_deployment`: Record whether the existing target was verified, set authorization to required, then stop at `blocked`. This daily graph does not execute deployments because it has no deployment-bundle authorization or proof contract. A separately approved workflow must perform and verify that mutation.

Never create a site, replace a project ID, change access, alter design, modify automation, change hosting configuration, or execute `full_deployment` during a daily run. A refresh endpoint that independently researches or regenerates content is not a compatible adapter because it cannot prove local artifact and live-edition agreement. Route to `blocked` before mutation when the target or adapter cannot be verified.

Use `daily-ai-brief/<date>/<content-fingerprint>` as the idempotency key. Retry only transient network failures or HTTP 408, 425, 429, and 5xx responses. Allow an initial attempt plus two retries. Never use a force-regeneration option as an automatic retry. Treat same-date same-fingerprint content as `unchanged`; treat same-date different-fingerprint content as `conflict`.

Terminal meanings:

- `done`: Local artifact, delivery receipt, live edition, immutable archive entry, and Markdown success history all agree.
- `blocked`: Local artifact is valid, but the target, compatible adapter, or required mutation approval is unavailable. Do not publish or append success history.
- `publish_failed`: A verified adapter was attempted but delivery, live verification, or archive verification failed. Retain the HTML, record the failure, and do not append success history.
- `failed`: Local research, rendering, validation, or persistence failed irrecoverably.

## HTML Contract

Create one standalone UTF-8 HTML document with no scripts or external CSS, fonts, images, or assets. Include:

- One dated `<title>`, `<h1>`, `<ol>`, and footer
- One `<article>` per selected item
- A visible exact shortfall reason when fewer than 10 items qualify
- Person, role/org, why it matters, one real HTTPS source link, and a summary of at most 500 characters per item
- Article text that exactly matches those structured fields, the `Why it matters:` label, and the selected source record label
- The resolved date and generated timestamp/timezone

Preserve existing visual design when updating an established publication target. Daily runs may change edition content, archive metadata, and operational state only.

## Deterministic Validation

Run from the brief workspace, resolving `<skill-directory>` to this skill's installed or repository path:

```bash
python3 <skill-directory>/scripts/validate_run.py \
  --workspace . \
  --state ./.daily-ai-brief/runs/<run-id>.json
```

The validator checks graph transitions, retry bounds, trace safety, source and story uniqueness, score arithmetic, dates, item count or shortfall, summary length, HTML/state agreement, artifact digests, publication proof, live proof, and run-log idempotency.

## Successful Run-Log Entry

Keep legacy labels and add v1 fields:

```text
## YYYY-MM-DD HH:MM TZ

- Produced/updated:
- Selected people:
- Main themes:
- Source URLs: ["https://example.com/source"]
- Source-quality notes:
- Resolved date/timezone:
- Output file:
- Shortfall reason:
- Graph version:
- Run state:
- Publication:
- Live edition:
- Archive edition:
- Run ID:
- Runtime/workflow notes:
```

For v1 entries, write selected people and themes as exact comma-and-space joined ordered lists. Write `Resolved date/timezone` as `YYYY-MM-DD, IANA timezone, HH:MM TZ` from the run start. These values, source URLs, and the entry digest must exactly match run state.

Append this entry only after independent live and archive verification. Before the atomic append, store its intended digest with `run_log_status: pending_append`. On recovery, accept either no matching block or one exact matching block, then finish the same run ID without duplication. Only `done` changes the status to `written`.

## Final Response

Return the local HTML path, terminal status, and live edition URL when verified. For `blocked`, `publish_failed`, or `failed`, state the exact blocker or failure and the safe next action. Never claim end-to-end success before `done` passes validation.
