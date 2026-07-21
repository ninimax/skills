---
name: orchestrate-projects
description: Coordinate long-running, multi-milestone Codex projects from discovery through evidence-based completion. Use when the user asks Codex to orchestrate a project over multiple turns, maintain GOALS.md, work through one Goal-mode objective at a time, delegate investigations or implementations, audit and review milestone outcomes, coordinate local Computer Use checks, or publish concise status updates through chat, Slack, or progress-dashboard.html.
---

# Orchestrate Projects

Act as the project coordinator. Preserve the objective, constraints, decisions, evidence, and current state while delegating bounded execution work.

## Begin with discovery

1. Inspect available project context, including `AGENTS.md`, existing roadmaps, repository status, relevant documentation, and current verification commands.
2. Interview the user conversationally. Ask one to three high-leverage questions at a time about the intended outcome, users, constraints, non-goals, risks, environments, and completion evidence. Accept rough ideas, reflect back the current understanding, and let the plan emerge through dialogue.
3. Resolve only choices that materially change the result. Make safe, reversible assumptions when they preserve momentum, and record them as decisions.
4. Keep a provisional outline in the conversation until the answers provide enough context for a useful roadmap. If the user asks work to begin immediately, label the outline provisional and record unanswered questions as blockers or assumptions.
5. Propose a milestone sequence. Define each milestone by an outcome and evidence gate, not by an oversized flat task list.
6. Create `GOALS.md` from `assets/GOALS.md` once the initial plan is grounded. Merge the required structure into an existing roadmap without overwriting useful project state.

## Maintain the roadmap

Keep one milestone active at a time. For every milestone, maintain:

- intended outcome
- work in scope and explicit non-goals
- important decisions and assumptions
- known blockers
- evidence required for completion
- evidence collected
- next actions

Use `Queued`, `Active`, `Verification`, `Complete`, or `Blocked` as milestone states. Update `GOALS.md` whenever evidence changes scope, ordering, decisions, blockers, or the definition of done. Keep a short decision log and update log. Never declare completion before the agreed evidence exists.

## Maintain one Goal-mode objective

Map the active Goal-mode objective to the active milestone.

1. Inspect any existing goal before creating another one.
2. Create a goal only when the user explicitly asks for Goal mode. Invoking this skill by itself is not authorization to create one.
3. State the milestone outcome and evidence gate in the objective. Keep implementation details in `GOALS.md`.
4. Do not replace an unfinished objective or mark it complete merely because the plan changed, work is difficult, or the budget is low. Follow the available goal tool's status rules.
5. Complete the objective only after implementation, evidence collection, roadmap audit, and review are resolved.
6. Activate the next milestone only after the current milestone closes.

If the user has not requested Goal mode or the tools are unavailable, keep the proposed objective in `GOALS.md` and tell the user what can be activated with `/goal`. Do not pretend that Goal mode is active.

## Keep the main thread on coordination

Use the main thread for objective management, constraints, decisions, project state, integration, and evaluation. Perform small checks directly when efficient, but delegate bounded investigations, implementations, and verification when parallel work improves the result.

- Use subagents for temporary work whose detailed history does not need to remain visible.
- Use a separate thread for work the user may want to revisit, when the user has requested visible parallel work or explicitly permits thread creation.
- Use a local thread for checks that require the user's machine only when the user requests or permits local thread creation.
- Avoid concurrent edits to the same files. Give each worker a clear ownership boundary.

Give every worker a compact brief containing the objective, scope, constraints, relevant paths or revision, allowed mutations, required evidence, and expected return format. Require workers to return:

1. what they learned
2. what changed
3. supporting evidence
4. what should happen next

Integrate worker results into `GOALS.md`; do not make the coordinator carry raw implementation history.

## Close every milestone with two checkpoints

Stop advancement once implementation and its first-pass checks finish.

### Audit the roadmap

Use an independent thread or subagent to compare `GOALS.md` with the current project state. Ask:

- Is the milestone actually complete?
- Is the next goal still correct?
- Are milestones missing?
- Has new evidence changed the order of work?
- Does the definition of done still hold?

Update the roadmap from supported findings before moving on.

### Review the implementation

Require `/review` after every milestone. Run it in a separate thread when callable. If it cannot be invoked programmatically, ask the user to run `/review` in a separate thread and return the findings. Do not mark the milestone complete or activate the next objective until that checkpoint finishes. An independent code review may prepare for `/review`, but never replaces it.

Resolve actionable findings, repeat affected verification, and re-run review when the changes are material. Keep roadmap auditing and code review separate because they answer different questions.

## Coordinate local Computer Use testing

With the user's explicit permission, use a local Codex thread with a Computer Use surface, such as the Codex Chrome extension, for checks that depend on a signed-in browser, local credentials, Xcode, macOS permissions, a simulator, hardware, or another machine-specific capability. If local thread creation is unavailable or not authorized, prepare a self-contained local handoff instead.

1. Identify the exact branch, commit, patch, or build under test.
2. Give the local thread setup steps, test steps, expected behavior, and required screenshots or logs.
3. Keep credentials local and out of prompts, logs, dashboards, and roadmap files.
4. Ask the local thread to return screenshots, logs, findings, and the tested revision.
5. Delegate fixes to the appropriate worker, then re-run the same local test.

If the local environment is unavailable, continue independent remote work and record the local check as an unresolved evidence gate. Never infer that an unrun local check passed.

## Report state changes

Send a concise update whenever project state materially changes:

```text
What's done
- Outcome plus strongest evidence

What's next
- Immediate next action and owner

Any blockers
- Decision, approval, or environment needed; write "None" when clear
```

Keep updates short enough to scan after time away. Link to evidence when useful.

For projects with two or more milestones or parallel workstreams, copy `assets/progress-dashboard.html` to the project root and replace every `{{TOKEN}}`. Keep it current with the active goal, milestone states, evidence, blockers, decisions, and recent updates. Do not place secrets or sensitive logs in the dashboard. Deploy it only when the user authorizes publication.

Send the same update to Slack only when a Slack connector is available, the destination is known, and the user has explicitly authorized sending. Otherwise prepare a ready-to-send draft. Do not install a connector, choose a destination, or send a message by assumption.

## Finish or hand off

Before closing a milestone or the project:

1. Review the diff and run all relevant lint, build, test, and interaction checks.
2. Confirm that evidence matches the current revision and environment.
3. Reconcile the roadmap audit and code review.
4. Update `GOALS.md` and `progress-dashboard.html`.
5. Report what completed, what remains, blockers, and exact evidence.
6. Mark the active goal complete only when no required work remains.

If progress stops, preserve a resumable state: active objective, exact blocker, completed evidence, pending checks, responsible owner, and next command or action.

## Use the bundled assets

- Copy `assets/GOALS.md` into a new project's root as the roadmap scaffold. Replace every `{{TOKEN}}` and remove unused sample milestones.
- Copy `assets/progress-dashboard.html` into the project root for a self-contained status view. Replace every `{{TOKEN}}`, duplicate milestone or activity items as needed, and verify it at desktop and narrow-screen widths.
