---
name: orchestrate-projects
description: Coordinate long-running, multi-milestone projects across multiple turns, from conversational discovery through evidence-based completion. Use for project orchestration that requires interviewing the user, creating or maintaining GOALS.md, aligning one Goal-mode objective to the active milestone, delegating implementation to subagents or visible threads, automatically closing milestones through a fresh visible audit and review task, coordinating machine-dependent testing, or maintaining an evidence-based progress dashboard.
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

When visible threads are authorized, automatically create a fresh, separate visible milestone-closeout task in the same repository. Do not ask the user to create or initialize it. Give the task the exact branch, base and head revisions or patch, working-tree state, milestone outcome, evidence gate, `GOALS.md` path, and collected verification evidence. Confirm that it can see the tested revision before accepting its conclusions. A subagent may prepare evidence but does not satisfy this visible checkpoint.

Ask the milestone-closeout task to audit the roadmap first:

- Is the milestone actually complete?
- Is the next goal still correct?
- Are milestones missing?
- Has new evidence changed the order of work?
- Does the definition of done still hold?

Update the roadmap from supported findings before reviewing the implementation or activating the next objective. If visible task creation is unavailable or unauthorized, prepare a self-contained handoff and keep the milestone in `Verification` until the checkpoint is completed or the user changes the agreed gate.

### Review the implementation

After the roadmap audit, instruct the same milestone-closeout task to independently review every implementation-bearing milestone. The task must be review-only and must not be an implementation worker for that milestone. Give it this review contract:

- compare the exact base and tested head revisions
- check the milestone outcome, scope, constraints, and required evidence in `GOALS.md`
- inspect the diff and relevant surrounding code for correctness, regressions, security, maintainability, and missing tests
- run relevant verification commands when the environment permits
- return actionable findings first, with severity, file and line references, evidence, and a recommended fix
- state explicitly when there are no findings and list the review and verification performed

Use the specialized `/review` workflow when it is genuinely callable without user intervention, or when the user explicitly chooses it as an additional gate. Otherwise, a direct independent review assignment in the visible task satisfies this checkpoint. Do not require the user to invoke a slash command or block ordinary milestone completion solely because manual invocation would be required.

For a milestone without implementation, require an independent artifact and evidence review. Keep roadmap auditing and implementation review as distinct checkpoints even when the same visible task performs both.

Do not mark the milestone complete or activate the next objective until both checkpoints finish. Resolve actionable findings, repeat affected verification, and re-run review when the changes are material.

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
4. Update `GOALS.md` and `progress-dashboard.html` when present.
5. Report through the three-section status format, placing exact completion evidence under `What's done`.
6. Mark the active goal complete only when no required work remains.

If progress stops, preserve a resumable state: active objective, exact blocker, completed evidence, pending checks, responsible owner, thread references, and next command or action.

## Use the bundled assets

- Copy `assets/GOALS.md` into a new project's root as the roadmap scaffold. Replace every `{{TOKEN}}`, duplicate or remove milestone, workstream, evidence, decision, and update rows as needed, and preserve the one-current-milestone invariant.
- Copy `assets/progress-dashboard.html` into the project root when the dashboard threshold is met. Make its milestones and workstreams match `GOALS.md` exactly, and duplicate or remove evidence, decision, closeout, and recent-update items instead of retaining filler content. Use `queued`, `active`, `verification`, `complete`, or `blocked` for milestone state classes and `active`, `proposed`, `complete`, `blocked`, or `unavailable` for Goal state classes. HTML-escape every text substitution and use valid ISO values in `datetime` attributes.
- Confirm that no placeholders remain by running `rg -n '\{\{[A-Z0-9_]+\}\}'` against each copied file. A clean result returns no matches.
- Verify the dashboard at desktop and narrow-screen widths before treating it as current evidence.
