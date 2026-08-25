---
name: luma-event-interest-to-use-case-mapping
description: Analyze live Luma event registration interests, rank participant themes, map them to verified official ChatGPT use cases, and create audience-ready showcase tasks when explicitly requested. Use when event-planning insights should come directly from Luma instead of a CSV export.
---

# Luma Event Interest to Use Case Mapping

Use the connected Luma account as the source of truth. Keep the workflow read-only unless the user separately requests a specific event mutation.

## Retrieve the responses

1. Locate the event with the Luma connector.
   - Use the supplied event ID when available.
   - Otherwise list the user's events and match by title and date.
   - If multiple events remain plausible, ask the user to choose.
2. Get the event and require manager-level data before reading registrations. If only guest or public data is available, report that manager access is required.
3. Read `registration_questions` and select the requested question by ID or label. Ask only when multiple questions plausibly match.
4. List guests through every page, following `next_cursor` until `has_more` is false.
5. Extract the answer from each guest's `registration_answers`, matching by question ID first and label second.
6. Include registered guests with a non-empty answer. Honor any approval-status scope the user specifies. Otherwise exclude invite-only records without submitted answers.

Record the event name, event date, retrieval time, guest count, included-answer count, excluded blank or unclear count, and status scope. Treat every run as a live snapshot.

## Protect participant data

Analyze only the selected answer and approval status when status is relevant. Do not expose or retain names, emails, phone numbers, LinkedIn profiles, dietary information, QR codes, ticket keys, or raw guest records. Do not quote an answer when it could identify its author unless the user explicitly requests that disclosure.

Do not approve, decline, invite, message, check in, or modify guests or the event as part of this workflow.

## Rank the themes

- Before coding, define a mutually exclusive theme frame at one consistent level of abstraction.
- Do not rank both a parent theme and one of its child themes unless their boundaries are explicit.
- Assign each substantive response one primary theme to avoid double counting.
- For a multi-topic response, use the participant's dominant requested outcome.
- Keep vague answers such as no preference or generic exploration in an `Unclear` group and exclude them from the ranking.
- Assign every retrieved record the first applicable disposition in this order: outside the requested status scope, invite-only without a submitted answer, blank, unclear, or one substantive theme. Verify that the disposition counts sum to the retrieved guest count.
- When comparing snapshots, reuse the same theme frame for both. Otherwise state that their theme counts are not longitudinally comparable.
- Rank the requested number of themes, defaulting to ten.
- Report raw counts. State that the coding is directional when responses overlap.
- Keep theme names concrete and faithful to the submitted intent.

## Match official use cases

Search the official OpenAI documentation for `https://learn.chatgpt.com/use-cases`. Prefer the OpenAI documentation connector. If the catalog page is dynamic or cannot be fetched as Markdown, inspect the live page with the Browser skill in read-only mode.

When several use cases fit, prefer the broadest direct catalog match to the dominant participant outcome. Use a narrower match only when the participant theme is equally narrow.

For every ranked theme:

1. Select one use case that is actually listed in the catalog.
2. Open its detail page and verify its exact title, URL, and summary.
3. Explain the match in one sentence.
4. Label it as the closest catalog match when the fit is indirect.

Never invent a use-case title or link. The Luma connector supplies registration data; the official catalog supplies the use-case matches.

## Create the showcase tasks

Create showcase tasks only when the user explicitly requests them or explicitly invokes the full showcase workflow. If this skill was selected implicitly for an analysis-only request, stop after the mapping report and offer to create the tasks.

1. Create one visible Codex task for each ranked official use case, up to the requested number of themes. If fewer substantive themes exist, create only the available tasks and report the difference.
2. List the available Codex projects and select the current project. Ask the user to choose only when the current project cannot be identified unambiguously. For a Git project, use an isolated worktree for each task. Otherwise use the saved project directly.
3. Give each task one non-overlapping folder under `showcases/`, named with its two-digit rank and a short use-case slug. Do not let showcase tasks edit shared files or another showcase folder.
4. Include only the aggregated participant theme, response count, verified use-case title, URL, summary, and relevant event context in each task prompt. Never include participant names, contact information, raw answers, or guest records.
5. Ask each task to build the smallest high-impact artifact that demonstrates the mapped use case to a live audience in three to five minutes. Match the artifact type to the use case instead of defaulting to an app.
6. Prefer existing project capabilities, native formats, and already-installed dependencies. Search for a real external asset only when it materially improves the showcase, then verify its direct source and license before use. Prefer public-domain, CC0, or permissively licensed open data and media, and OSI-approved code. If provenance is unclear or sourcing adds little value, create clearly labeled synthetic data or mock files locally instead.
7. Require each task to place a concise `SHOWCASE.md` beside the artifact with the audience hook, presentation flow, open or run steps, source and license details, verification performed, and a fallback if the live demo fails.
8. Require proportionate verification before completion. Test browser experiences in a browser, render document or media artifacts, and run relevant checks for code. Keep the result self-contained and usable without private accounts or participant data.
9. Task creation is asynchronous. Follow every created task to completion or a user-attention request. Wait in batches of up to eight tasks, read each final result, and do not treat task creation as successful delivery.

## Report

Lead with the result and include:

- Event name and live snapshot scope
- Total retrieved registrations, substantive answers, and excluded unclear answers
- A table with rank, participant theme, response count, linked official use case, and concise rationale
- A short recommendation on which themes deserve the most workshop time
- When showcase tasks were authorized, a table with each task title, reference, status, and showcase folder
- Confirmation that no Luma records were changed

Do not include a conversation transcript, raw guest export, or personal participant details.

If Luma is unavailable or unauthenticated, report the access blocker. Offer a user-provided CSV only as an optional fallback.
