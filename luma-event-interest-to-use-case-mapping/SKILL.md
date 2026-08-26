---
name: luma-event-interest-to-use-case-mapping
description: Analyze relevant interest questions from a live Luma event, rank the top ten participant themes, match them to verified official ChatGPT and Codex use cases, and design event-tailored showcase workflows.
---

# Luma Event Interest to Use Case Mapping

Use the connected Luma event and the official [ChatGPT use-case catalog](https://learn.chatgpt.com/use-cases) to turn participant interests into showcase workflows.

## Workflow

1. Find the event and read its description for the event purpose, target audience, and experience level. If no audience or level is stated, keep the showcases broadly accessible.
2. Inspect the registration-question labels and select only questions about participant interests, topics, themes, goals, or desired builds. Use every clearly relevant question unless the user names a specific one. Briefly list the selected questions in the result when there is more than one. Ignore irrelevant operational questions.
3. Retrieve all registration pages and reduce each record to the selected answer text before analysis. Do not inspect, retain, or report personal fields.
4. Group substantive answers into distinct themes, count each registration once, and rank the top ten. Exclude blank or unusably vague answers.
5. For each theme, find the closest direct match in the official catalog. Open the use-case page and verify its exact title, URL, and description. Clearly label an indirect match.
6. Design one concise showcase workflow for each matched use case. Tailor it to the event description and any stated audience or experience level. Include the demonstration goal, minimal inputs, practical flow, expected result, and audience takeaway.

## Output

- A short event and audience summary
- The selected registration questions when more than one was used
- A ranked table with theme, response count, verified use case, link, and match rationale
- One event-tailored showcase workflow for each ranked candidate

Do not include personal participant data. Do not create separate Codex tasks or artifacts unless the user asks.
