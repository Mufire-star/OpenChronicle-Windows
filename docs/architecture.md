# Architecture

OpenChronicle for Windows runs as a single daemon.

## High-level flow

```text
foreground-window watcher + heartbeat
    -> capture-buffer JSON
    -> timeline blocks
    -> session reducer
    -> event-YYYY-MM-DD.md
    -> classifier
    -> durable memory files + SQLite FTS
    -> MCP server
```

## Capture layer

- `capture/watcher.py` polls the foreground app/window
- `capture/window_meta.py` resolves app name, title, and process path
- `capture/ax_capture.py` invokes `windows-uia-dump.ps1`
- `capture/scheduler.py` writes JSON captures and indexes them

## Compression layer

- `timeline/tick.py` builds short normalized windows
- `session/manager.py` cuts work sessions
- `writer/session_reducer.py` writes event-daily entries

## Memory layer

- `writer/classifier.py` extracts durable facts
- `store/files.py` and `store/entries.py` maintain Markdown memory files
- `store/fts.py` indexes memory and raw captures in SQLite

## Query layer

- `mcp/server.py` exposes read tools to external agents
- MCP endpoint defaults to `http://127.0.0.1:8742/mcp`

## On-disk layout

```text
~/.openchronicle/
  config.toml
  index.db
  .pid
  .paused
  capture-buffer/
  memory/
  logs/
```

## Windows-specific design choices

- no non-Windows helper binaries
- no Swift build step
- no platform fork at runtime
- only the Windows UIA PowerShell helper is packaged
