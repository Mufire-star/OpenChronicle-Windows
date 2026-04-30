You are summarizing one user work window into a structured session entry. The window is presented as an ordered list of pre-computed timeline blocks; each block already contains a list of activity records in the format `[<app>] <context>: <what happened>. <verbatim authored text in quotes, if any>. Involving: <people/topics/files>`. The timeline stage was instructed to preserve authored text, URLs, and proper nouns verbatim, so the content inside quotes is the user's own typed text and you must carry it forward without paraphrasing.

Window: {start_time} to {end_time} ({block_count} timeline blocks, {capture_count} raw capture records).

Timeline blocks (your primary evidence):
---
{blocks_text}
---

## Preceding entries in {event_daily_name}

The file below already contains the most recent session/flush entries from today, written by earlier runs of this same reducer. Treat them as context only; do not rewrite, restate, or append content that merely rehashes what's already there.

---
{preceding_text}
---

## Rules

**Context binding rule.** Every named person / file / project in your output MUST be stated next to the same app or channel it appeared in inside the source blocks.

**Verbatim preservation rule.** When a source block contains a quoted verbatim excerpt, include it verbatim in the matching `sub_task`. Do NOT replace `user typed "buy milk, eggs, flour"` with `user typed a shopping list`.

**Authorship guard.** Do not upgrade "read / checked" into "participated / discussed / replied" unless the source blocks clearly show composing.

**No duplication with preceding entries.** Do not emit a sub_task whose `[HH:MM-HH:MM, app]` range overlaps the range of a preceding entry for the same activity.

**Observed-regularity surfacing.** A separate downstream classifier decides what long-term preference / habit / style facts are worth persisting. When the current window exhibits, or continues, a clearly repeated behavior, append one extra sentence to `summary` beginning with `Observed regularity:`.

## Output

Return a JSON object with exactly these fields:

- `summary`: 2-4 sentences describing this window's core tasks, progress, and any clear task switches.
- `sub_tasks`: ordered, de-duplicated array of sub-task lines in the format
  `[HH:MM-HH:MM, <app name>] <action>; <verbatim authored text or quoted evidence, if present>; involving <people/topics/files>`

`<app name>` must be the canonical Windows app name as it appeared in the source blocks, for example `Cursor`, `Claude`, `Chrome`, or `Code - Insiders`. A drill-down breadcrumb is appended to each line by code using exactly this app name, so mismatches will break raw-content lookups.

Output only the JSON object, with no markdown fences and no surrounding prose. Do not emit any other fields.
