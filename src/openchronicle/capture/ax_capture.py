"""Windows UI Automation capture provider."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Protocol

from ..logger import get
from .ax_models import AXCaptureResult

logger = get("openchronicle.capture")

_SUBPROCESS_TIMEOUT = 10


def _strip_frame_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_frame_fields(v) for k, v in value.items() if k != "frame"}
    if isinstance(value, list):
        return [_strip_frame_fields(item) for item in value]
    return value


class AXProvider(Protocol):
    @property
    def available(self) -> bool: ...

    def capture_frontmost(self, *, focused_window_only: bool = True) -> AXCaptureResult | None: ...

    def capture_all_visible(self) -> AXCaptureResult | None: ...

    def capture_app(
        self, app_name: str, *, focused_window_only: bool = True
    ) -> AXCaptureResult | None: ...


class UnavailableAXProvider:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    @property
    def available(self) -> bool:
        return False

    def capture_frontmost(self, *, focused_window_only: bool = True) -> AXCaptureResult | None:
        return None

    def capture_all_visible(self) -> AXCaptureResult | None:
        return None

    def capture_app(
        self, app_name: str, *, focused_window_only: bool = True
    ) -> AXCaptureResult | None:
        return None


def _resolve_windows_script() -> Path | None:
    override = os.environ.get("OPENCHRONICLE_WINDOWS_UIA_SCRIPT")
    if override:
        path = Path(override).expanduser().resolve()
        if path.is_file():
            return path
        logger.warning("OPENCHRONICLE_WINDOWS_UIA_SCRIPT set but file missing: %s", path)

    candidates: list[Path] = []
    try:
        from importlib.resources import files as pkg_files

        bundled_dir = Path(str(pkg_files("openchronicle").joinpath("_bundled")))
        candidates.append(bundled_dir / "windows-uia-dump.ps1")
    except (ModuleNotFoundError, ValueError):
        pass

    dev_root = Path(__file__).resolve().parents[3]
    candidates.append(dev_root / "resources" / "windows-uia-dump.ps1")

    for path in candidates:
        if path.is_file():
            return path
    return None


class WindowsUIAProvider:
    def __init__(self, *, script_path: Path, depth: int, timeout: int) -> None:
        self._script_path = str(script_path)
        self._depth = max(1, min(depth, 8))
        self._timeout = max(3, timeout)
        self.reason = ""

    @property
    def available(self) -> bool:
        return True

    def capture_frontmost(self, *, focused_window_only: bool = True) -> AXCaptureResult | None:
        return self._run(focused_window_only=focused_window_only)

    def capture_all_visible(self) -> AXCaptureResult | None:
        return self._run(focused_window_only=False)

    def capture_app(
        self, app_name: str, *, focused_window_only: bool = True
    ) -> AXCaptureResult | None:
        return self._run(focused_window_only=focused_window_only)

    def _run(self, *, focused_window_only: bool) -> AXCaptureResult | None:
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if not shell:
            logger.warning("PowerShell not found on PATH")
            return None

        args = [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            self._script_path,
            "-Depth",
            str(self._depth),
        ]
        if focused_window_only:
            args.append("-FocusedWindowOnly")

        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=min(self._timeout + 5, _SUBPROCESS_TIMEOUT),
            )
        except subprocess.TimeoutExpired:
            logger.warning("windows-uia-dump timed out after %ds", min(self._timeout + 5, _SUBPROCESS_TIMEOUT))
            return None
        except OSError as exc:
            logger.error("Failed to run windows-uia-dump: %s", exc)
            return None

        if proc.returncode != 0:
            stderr = (proc.stderr or proc.stdout).strip()
            logger.warning("windows-uia-dump exited %d: %s", proc.returncode, stderr[:300])
            return None

        if proc.stdout is None:
            logger.warning(
                "windows-uia-dump produced no stdout (stderr=%r)",
                (proc.stderr or "")[:300],
            )
            return None

        payload = proc.stdout.strip()
        if not payload:
            logger.warning(
                "windows-uia-dump produced empty stdout (stderr=%r)",
                (proc.stderr or "")[:300],
            )
            return None

        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(
                "Failed to parse windows-uia-dump JSON: %s (stdout=%r, stderr=%r)",
                exc,
                payload[:300],
                (proc.stderr or "")[:300],
            )
            return None

        data = _strip_frame_fields(data)
        mode = "frontmost" if focused_window_only else "all-visible"
        return AXCaptureResult(
            raw_json=data,
            timestamp=data.get("timestamp", ""),
            apps=data.get("apps", []),
            metadata={"mode": mode, "depth": self._depth, "platform": "windows"},
        )


def create_provider(*, depth: int = 8, timeout: int = 3, raw: bool = False) -> AXProvider:
    del raw
    script = _resolve_windows_script()
    if script is None:
        return UnavailableAXProvider("windows-uia-dump.ps1 not found")
    logger.info("Windows UIA capture initialized: %s", script)
    return WindowsUIAProvider(script_path=script, depth=depth, timeout=timeout)
