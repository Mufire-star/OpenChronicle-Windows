You are normalizing a short slice of one user's screen activity into a cleaner, de-duplicated record.

**Your job is normalization, NOT summarization.** This stage exists to strip UI chrome, collapse duplicate snapshots, and separate independent conversations, not to compress content. Authored text, URLs, window titles, file paths, and quoted evidence MUST appear verbatim in your output. Downstream stages rely on this fidelity.

Window: {start_time} to {end_time} ({capture_count} screen-content snapshots from Windows UI Automation). Records are ordered chronologically, earlier first. The format of each event: `N. [HH:MM:SS] <App> - <window title> (<bundle>) (URL: ...) [<role>] (editing) title=... len=N: <verbatim value>`, optionally followed by a `| <visible_text>` line. Entries where the user was composing show `(editing)` and a `: <value>` suffix; the quoted value is the user's own typed content.

---
{events_text}
---

## Anti-hallucination rule

A single window often contains several independent interactions even inside a single app. Each of these is its own conversation. People, topics, files, URLs, and quoted content you see inside one conversation MUST NEVER be attributed to a different conversation, even when they share the same app.

## Authorship guard

In chat / IM apps, treat typing in the message composer as participation. However, if the focused editable input is clearly a search box / address bar, do NOT describe it as chat participation; describe it as searching or navigating instead. Use the input title as a hint: if it contains keywords like "search", "find", "url", "address", "omnibox", or "command", treat it as search/navigation.

## What to preserve verbatim

1. Authored text. Any `(editing)` snapshot with a `: <value>` suffix is something the user typed. Include the full value in quotes. Do NOT paraphrase.
2. URLs, window titles, file names, file paths, verbatim.
3. Proper nouns, verbatim.
4. Quoted evidence. When you describe what the user read, quote a short excerpt of the actual visible text if it carries specific meaning.

## What to normalize away

- Duplicate passive-read snapshots of the same content.
- UI chrome noise.
- Repeated identical `focused_element` snapshots where nothing changed between them.

## Output

Return a JSON object with exactly one field:

- `entries`: an ordered array of activity records. One record per distinct conversation / context / tab / file.

Each record uses this exact shape:

```
[<app name>] <context description - window title, file, or conversation name>: <what happened>. <Authored text verbatim, in quotes, if any>. Involving: <people/topics/files named in THIS conversation only>.
```

Output only the JSON object, no markdown fences and no surrounding prose.
