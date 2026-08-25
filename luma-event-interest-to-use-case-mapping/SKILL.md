---
name: luma-event-interest-to-use-case-mapping
description: Analyze live Luma event registration interests, rank participant themes, and map them to verified official ChatGPT use cases. Use when event-planning insights should come directly from Luma instead of a CSV export.
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

## Report

Lead with the result and include:

- Event name and live snapshot scope
- Total retrieved registrations, substantive answers, and excluded unclear answers
- A table with rank, participant theme, response count, linked official use case, and concise rationale
- A short recommendation on which themes deserve the most workshop time
- Confirmation that no Luma records were changed

Do not include a conversation transcript, raw guest export, or personal participant details.

If Luma is unavailable or unauthenticated, report the access blocker. Offer a user-provided CSV only as an optional fallback.
