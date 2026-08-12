---
name: orchestrate-projects
description: Coordinate long-running, multi-milestone projects across multiple turns, from conversational discovery through evidence-based completion. Use for project orchestration that requires interviewing the user, creating or maintaining GOALS.md, aligning one Goal-mode objective to the active milestone, delegating implementation to subagents or visible threads, automatically closing milestones through fresh visible roadmap audits and repeated specialized review tasks, coordinating machine-dependent testing, or maintaining an evidence-based progress dashboard.
---

# Orchestrate Projects

Act as the project coordinator. Preserve the objective, constraints, decisions, evidence, and current state while delegating bounded execution work.

## Begin with discovery

1. Inspect available project context, including applicable agent instruction files such as `AGENTS.md`, existing roadmaps, repository status, relevant documentation, and current verification commands.
2. Interview the user conversationally. Ask one to three high-leverage questions at a time about the intended outcome, users, constraints, non-goals, risks, environments, and completion evidence. Accept rough ideas, reflect back the current understanding, and let the plan emerge through dialogue.
3. Resolve only choices that materially change the result. Make safe, reversible assumptions when they preserve momentum, and record them as decisions.
4. Keep a provisional outline in the conversation until the answers provide enough context for a useful roadmap. If the user asks work to begin immediately, label the outline provisional and record unanswered questions as blockers or assumptions.
5. Propose a milestone sequence. Define each milestone by an outcome and evidence gate, not by an oversized flat task list.
6. Create `GOALS.md` from `assets/GOALS.md` once the initial plan is grounded. Merge the required structure into an existing roadmap without overwriting useful project state.

## Maintain the roadmap

For every milestone, maintain:

- intended outcome
- owner and dependencies
- work in scope and explicit non-goals
- important decisions and assumptions
- known blockers
- evidence required for completion
- traceable evidence collected
- closure checkpoints
- next actions

Use `Queued`, `Active`, `Verification`, `Complete`, or `Blocked` as milestone states. While work remains, keep exactly one current milestone in `Active`, `Verification`, or `Blocked`. Keep future milestones `Queued` and closed milestones `Complete`.

Update `GOALS.md` whenever evidence changes scope, ordering, decisions, blockers, ownership, or the definition of done. Keep a short decision log and update log. Never declare completion before the agreed evidence exists.

## Maintain one Goal-mode objective

Map the coordinator thread's Goal-mode objective to the current milestone.

1. Inspect any existing goal before creating another one.
2. Create a goal only when the user explicitly asks for Goal mode. A request that says to set, create, or maintain a Goal-mode objective counts as authorization; merely invoking this skill does not.
3. Keep Goal state in the coordinator thread. Workers do not inherit it and must not create their own Goal-mode objectives unless the user explicitly requests that in the relevant thread.
4. State the milestone outcome and evidence gate in the objective. Keep implementation details in `GOALS.md`.
5. Do not replace or falsely complete an unfinished objective. If a scope change invalidates it, update `GOALS.md`, report the mismatch, and ask the user to resolve the active objective through the available Goal-mode controls.
6. Complete the objective only after implementation, evidence collection, roadmap audit, and review are resolved.
7. Activate the next milestone only after the current milestone closes.

A roadmap milestone marked `Blocked` is project documentation. Goal-mode `blocked` is a separate tool status and may be set only when the goal tool's rules allow it. One does not imply the other.

If Goal tools are unavailable, keep the proposed objective in `GOALS.md` and ask the user to activate it through the Goal-mode control available in their client. Do not pretend that Goal mode is active.

## Keep the main thread on coordination

Use the main thread only for objective management, constraints, decisions, project state, integration, and evaluation. Perform small coordination and integration checks directly. Delegate implementation to subagents or separate threads.

- Use subagents for bounded work whose detailed history does not need to remain visible.
- Use a separate visible thread for work the user may want to inspect, continue, or review later.
- Use a local thread for checks that require the user's machine.
- Create visible or local threads only with explicit user permission. A request to use separate or local threads counts as permission within that agreed scope; invoking this skill alone does not.
- Prefer isolated worktree threads for concurrent implementation. Do not assume a worktree contains the coordinator's branch or uncommitted changes.
- Confirm the exact branch, commit, patch, or working tree visible to each worker before accepting its evidence.
- Treat visible-thread dispatch as asynchronous. Record the thread reference, follow its progress, and do not treat creation as completion.
- Give every visible task a concise sidebar title at creation, or rename it immediately if the creation tool assigns a generic title. Use `<project-tag> M<n> <purpose>: <short scope>`, keep the full title at 40 characters or fewer, and put the project, milestone, and purpose before optional scope. Use purpose labels such as `Build`, `Research`, `Audit`, `Review R<n>`, or `Local Test`; omit branch names, commit hashes, and filler such as `Task for`.
- Keep the coordinator as the sole visible-task dispatcher. Workers, auditors, and reviewers must not create further tasks unless the user explicitly changes this ownership model.
- Create every audit and review round as a new peer task from the coordinator. Never reuse a prior audit task, review task, or implementation thread for a later checkpoint.
- Do not archive visible tasks automatically. Keep them inspectable unless the user explicitly asks to archive them.
- Avoid concurrent edits to the same files. Give each worker a clear ownership boundary.

Keep `GOALS.md` and `progress-dashboard.html` under coordinator ownership. Workers return a concise result packet, never a full transcript:

1. conclusions
2. changes made
3. supporting evidence and tested revision
4. recommended next action

Give every worker a compact brief containing the objective, scope, constraints, relevant paths or revision, allowed mutations, required evidence, and expected return format. Integrate supported results into the project state.

## Close every milestone with two checkpoints

Move the current milestone to `Verification` after implementation and its first-pass checks finish. Stop advancement until both checkpoints close.

### Audit the roadmap

When visible threads are authorized, automatically create a fresh, separate visible roadmap-audit task in the same project. Do not ask the user to create or initialize it. Title the first task `<project-tag> M<n> Audit A1: <scope>` and increment the round for every repeat while keeping the full title at 40 characters or fewer. Give the task the exact branch, base and head revisions or patch, working-tree state, milestone outcome, evidence gate, `GOALS.md` path, and collected verification evidence. Confirm that it can see the tested revision before accepting its conclusions. Record its title and reference in `GOALS.md`. A subagent may prepare evidence but does not satisfy this visible checkpoint.

Ask the roadmap-audit task:

- Is the milestone actually complete?
- Is the next goal still correct?
- Are milestones missing?
- Has new evidence changed the order of work?
- Does the definition of done still hold?

Wait for the task and read its result directly. Record every audit round, candidate revision, task reference, findings, and disposition as an immutable `GOALS.md` ledger row. Do not require the user to copy findings between tasks. If visible task creation or reading is unavailable or unauthorized, prepare a self-contained handoff and keep the milestone in `Verification` until the checkpoint is completed or the user changes the agreed gate.

If an audit round returns actionable findings:

1. Keep the milestone in `Verification`.
2. Reconcile every validated finding in the roadmap, milestone contract, evidence, or implementation plan. Disposition only a finding proven invalid or non-actionable, or explicitly waived by the user, and record its evidence or waiver.
3. Repeat affected verification and refresh the evidence supplied to the auditor.
4. Freeze the corrected roadmap and exact candidate revision.
5. Create a new visible task for audit round `A<n+1>`. Never continue the previous audit task.
6. Repeat until the newest applicable audit round reports no actionable findings.

Do not start implementation review or activate the next objective until the latest roadmap audit is clean and still applies to the frozen candidate.

### Review the implementation

After reconciling the roadmap audit, automatically create a different fresh visible task for every review round of an implementation-bearing milestone only when visible tasks remain authorized. The task must be review-only, must not be an implementation worker or roadmap auditor for that milestone, and must not dispatch other tasks. Title the first task `<project-tag> M<n> Review R1: <scope>` and increment the round for every retry while keeping the full title at 40 characters or fewer. If visible task creation or reading is unavailable or unauthorized, use the same self-contained handoff and fail-closed `Verification` fallback as the roadmap audit.

Start the task with an explicit `$review-agent` invocation and include the full review contract in the initial prompt. Resolve the skill through the target host's available-skill catalog, a client-produced skill attachment, or a read-only lookup of the target host's configured skill roots that verifies the `review-agent` frontmatter name. If a resource link is required, verify that its expanded `review-agent/SKILL.md` target exists and is readable in the target environment before dispatch. Never invent or hardcode a machine-specific skill path. Do not send a bare `$review-agent` token, literal `/review`, plain `review`, or a request that merely calls itself a dedicated review in a delegated prompt. Those are ordinary instructions and do not prove that the specialized reviewer ran.

After dispatch, read the opening turn and confirm that it contains the resolved client-produced skill attachment or expanded resource link, not only coordinator-authored prose or a bare token. The resolved attachment plus its verified target is invocation provenance; a reviewer's self-report alone is not. If that provenance is absent, do not count the task as the review checkpoint. Retry with a valid explicit skill reference when one is available; otherwise keep the milestone in `Verification` and report the capability blocker instead of silently downgrading the gate.

Give every review round this contract:

- compare the exact base and tested head revisions
- check the milestone outcome, scope, constraints, and required evidence in `GOALS.md`
- inspect the diff and relevant surrounding code for correctness, regressions, security, maintainability, and missing tests
- run relevant verification commands when the environment permits
- use a unique uncommon port for any local server and confirm that it is released afterward
- remain read-only and leave repository files and Git state unchanged
- return actionable findings first, with severity, file and line references, evidence, and a recommended fix
- state explicitly when there are no findings and list the review and verification performed

Wait for each review task and read its result directly. Record the round, candidate revision, task reference, findings, and disposition in `GOALS.md`; do not replace earlier rounds or ask the user to copy findings back.

If a round returns actionable findings:

1. Keep the milestone in `Verification`.
2. Fix and reverify every validated actionable finding outside the review task. Disposition only a finding proven invalid or non-actionable, or explicitly waived by the user, and record its evidence or waiver.
3. Repeat affected verification and the full milestone gate when the change can affect it.
4. Commit or otherwise freeze a new exact candidate revision.
5. Create a new visible task for the next `$review-agent` round. Never continue the previous review task.
6. Repeat until the newest round reports no actionable findings.

Re-run the roadmap audit in another fresh task when fixes change milestone scope, ordering, acceptance evidence, or the next objective. Do not run reviews concurrently against a moving candidate. Close the milestone only when the latest roadmap audit is clean and applicable and the latest applicable review is clean on the exact terminal candidate: a confirmed `$review-agent` round for an implementation-bearing milestone, or an independent artifact-review round for a milestone without implementation. The user may explicitly change or waive an agreed gate; record that decision and rationale rather than presenting the skipped gate as passed.

Treat the clean review candidate as terminal for implementation, artifacts, tests, acceptance criteria, and collected evidence. After a clean result, the coordinator may make one closeout-metadata-only update to `GOALS.md` and `progress-dashboard.html`: append the immutable audit and review references and results, mark their checkpoints complete, transition the reviewed milestone to `Complete`, activate the already audited next milestone, and update timestamps or status summaries. Record the reviewed candidate and identify the metadata revision in those files as `the commit containing this closeout row`; after committing, report the resolved metadata commit hash without creating another commit solely to embed its own hash.

Before committing that update, compare it with the clean reviewed candidate. It is exempt from another review only when every changed line is administrative closeout metadata described above. Any change to another path, implementation, artifact, test, milestone scope, definition of done, evidence requirement, evidence claim, or unaudited next objective invalidates the clean result and requires the affected audit, verification, and a fresh review task.

For a milestone without implementation, use fresh independent artifact and evidence review tasks instead of invoking `$review-agent`. Apply the same visible-task authorization, reviewer independence, exact-candidate, read-only, unique-port, wait, direct-result reading, immutable ledger, and fail-closed fallback rules. Title the first task `<project-tag> M<n> Artifact R1: <scope>` and increment the round for every retry.

Give every artifact-review task the milestone outcome, scope, non-goals, definition of done, exact artifact paths or references, `GOALS.md` path, collected evidence, candidate revision and environment, applicable standards, and explicit review questions. Require it to confirm access to the exact candidate, inspect the artifacts and surrounding evidence, run applicable validation, and return actionable findings first with severity, artifact location, evidence, and recommended correction, or an explicit no-findings result with the checks performed.

If a round returns actionable findings, fix and reverify every validated finding, freeze a new candidate, and create a new artifact-review task. Repeat until the latest artifact-review round is clean. Keep roadmap auditing and artifact review as separate tasks and checkpoints.

Do not mark the milestone complete or activate the next objective until both checkpoints finish under this protocol.

## Coordinate local machine testing

With the user's explicit permission, create or use a thread on the required local host and verify that it exposes the needed browser, Chrome, Computer Use, simulator, permission, credential, or hardware capability. A local or worktree environment selects code placement; it does not provision those capabilities.

1. Identify the exact branch, commit, patch, or build under test.
2. Give the local thread setup steps, test steps, expected behavior, and required screenshots or logs.
3. Keep credentials local and out of prompts, logs, dashboards, and roadmap files.
4. Ask the local thread to return screenshots, logs, findings, the tested revision, and the test environment.
5. Delegate fixes to the appropriate worker, then re-run the same local test.

Prefer the available Chrome integration for Chrome checks. Use desktop Computer Use for local applications or when the user explicitly requests it. If the required surface is unavailable, continue only independent work, prepare a self-contained local handoff, and keep the check as an unresolved evidence gate. Never infer that an unrun local check passed.

## Report state changes

For ordinary project state changes, send only the following three sections, with no preamble, closing note, or additional section:

```text
What's done
- Outcome plus strongest evidence

What's next
- Immediate next action and owner

Any blockers
- Decision, approval, or environment needed; write "None" when clear
```

Keep updates short enough to scan after time away. Link to evidence when useful. Discovery questions, required approval prompts, Goal token-usage reporting, and required thread UI directives are exceptions to this status format.

For projects with three or more milestones, two or more workers, or parallel workstreams, copy `assets/progress-dashboard.html` to the project root. Keep it current with Goal-mode status, milestone states, workstreams, evidence, closeout checkpoints, blockers, decisions, and recent updates. Do not place secrets or sensitive logs in the dashboard. Deploy it only when the user authorizes publication.

## Finish or hand off

Before closing a milestone or the project:

1. Review the diff and run all relevant lint, build, test, and interaction checks.
2. Confirm that evidence matches the current revision and environment.
3. Reconcile the roadmap audit and implementation review.
4. Update `GOALS.md` and `progress-dashboard.html` when present, applying and verifying the closeout-metadata-only exception after a clean review.
5. Report through the three-section status format, placing exact completion evidence under `What's done`.
6. Mark the active goal complete only when no required work remains.

If progress stops, preserve a resumable state: active objective, exact blocker, completed evidence, pending checks, responsible owner, thread references, and next command or action.

## Use the bundled assets

- Copy `assets/GOALS.md` into a new project's root as the roadmap scaffold. Replace every `{{TOKEN}}`, duplicate or remove milestone, workstream, evidence, decision, and update rows as needed, and preserve the one-current-milestone invariant.
- Copy `assets/progress-dashboard.html` into the project root when the dashboard threshold is met. Make its milestones and workstreams match `GOALS.md` exactly, and duplicate or remove evidence, decision, closeout, and recent-update items instead of retaining filler content. Use `queued`, `active`, `verification`, `complete`, or `blocked` for milestone state classes and `active`, `proposed`, `complete`, `blocked`, or `unavailable` for Goal state classes. HTML-escape every text substitution and use valid ISO values in `datetime` attributes.
- Keep every roadmap-audit task and specialized review round in the `GOALS.md` closeout ledger. Show the latest review round, candidate revision, task reference, status, and resolution on the dashboard without deleting earlier roadmap history.
- Confirm that no placeholders remain by running `rg -n '\{\{[A-Z0-9_]+\}\}'` against each copied file. A clean result returns no matches.
- Verify the dashboard at desktop and narrow-screen widths before treating it as current evidence.
