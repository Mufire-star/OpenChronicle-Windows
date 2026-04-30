# Windows implementation notes

OpenChronicle in this repository is a Windows-only build.

## Runtime shape

- `capture/window_meta.py` reads the foreground window via `user32`
- `capture/watcher.py` polls foreground app and window-title changes
- `capture/ax_capture.py` runs `resources/windows-uia-dump.ps1`
- `resources/windows-uia-dump.ps1` uses UI Automation to snapshot the focused window

## Supported behavior

- Foreground app/window tracking
- Focused-window UIA snapshots
- Screenshot capture
- Timeline aggregation
- Session cutting
- Reducer/classifier pipeline
- MCP server hosting

## Known limitations

- UIA depth and quality depend on the target app
- Some Electron apps expose incomplete trees
- Elevated apps may hide process metadata
- The watcher is strongest at window/app changes rather than per-keystroke editor updates

## Packaging

The wheel includes only the Windows UIA PowerShell script. Non-Windows helper binaries and build scripts are intentionally excluded in this branch.
