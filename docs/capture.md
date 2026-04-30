# Capture

Capture is the only layer that touches the outside world. It writes one JSON file per observation into `~/.openchronicle/capture-buffer/`.

## Signal sources

OpenChronicle for Windows uses two inputs:

1. **Foreground-window watcher**  
   `capture/watcher.py` polls the foreground app and window title, then emits synthetic focus-change events.

2. **Heartbeat timer**  
   Every `heartbeat_minutes`, the scheduler writes a capture even when no watcher event arrived.

## Capture pipeline

Each capture runs through:

1. `window_meta.active_window()` for app name, title, and process path
2. `ax_capture.capture_frontmost()` via `resources/windows-uia-dump.ps1`
3. `s1_parser.enrich()` for `focused_element`, `visible_text`, and `url`
4. `screenshot.grab()` when screenshots are enabled
5. JSON write into `capture-buffer/`

## What the Windows build captures well

- Foreground app switches
- Window-title changes
- Focused-window UIA trees
- Screenshots
- Searchable visible text when the target app exposes useful UIA metadata

## What is best-effort

- Per-keystroke typing updates
- Browser URL extraction in apps with poor UIA exposure
- Some Electron apps with shallow or noisy trees
- Elevated or protected windows

## Buffer hygiene

Older captures are cleaned in tiers:

- delete old absorbed JSON files
- strip screenshots from stale captures
- evict oldest absorbed captures when the buffer exceeds `buffer_max_mb`

## Smoke test

```powershell
openchronicle capture-once
```

If this succeeds, the buffer should contain a new JSON file and the captures index should receive a matching row.
