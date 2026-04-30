"""Windows foreground-window watcher."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from ..logger import get
from . import window_meta

logger = get("openchronicle.capture")


class AXWatcherProcess:
    """Poll the Windows foreground window and emit focus-change events."""

    def __init__(self, *, poll_seconds: float = 1.0) -> None:
        self._callback: Callable[[dict[str, Any]], None] | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._poll_seconds = poll_seconds

    @property
    def available(self) -> bool:
        return True

    @property
    def running(self) -> bool:
        return self._reader_thread is not None and self._reader_thread.is_alive()

    def on_event(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._callback = callback

    def start(self) -> None:
        self._stop_event.clear()
        self._reader_thread = threading.Thread(
            target=self._poll_windows_foreground,
            daemon=True,
            name="window-watcher-reader",
        )
        self._reader_thread.start()
        logger.info("window watcher started (Windows)")

    def stop(self, *, join_timeout: float = 5.0) -> None:
        self._stop_event.set()
        reader = self._reader_thread
        if reader is not None and reader.is_alive():
            reader.join(timeout=join_timeout)
            if reader.is_alive():
                logger.warning(
                    "window watcher reader thread did not exit within %.1fs", join_timeout
                )
        self._reader_thread = None
        logger.info("window watcher stopped")

    def _poll_windows_foreground(self) -> None:
        last_bundle = ""
        last_title = ""
        while not self._stop_event.is_set():
            meta = window_meta.active_window()
            bundle = meta.bundle_id or meta.app_name or ""
            title = meta.title or ""
            if bundle or title:
                if bundle != last_bundle:
                    self._emit(
                        {
                            "event_type": "AXApplicationActivated",
                            "bundle_id": bundle,
                            "window_title": title,
                        }
                    )
                elif title != last_title:
                    self._emit(
                        {
                            "event_type": "AXFocusedWindowChanged",
                            "bundle_id": bundle,
                            "window_title": title,
                        }
                    )
            last_bundle = bundle
            last_title = title
            self._stop_event.wait(self._poll_seconds)

    def _emit(self, event: dict[str, Any]) -> None:
        if self._callback is None:
            return
        try:
            self._callback(event)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Event callback error: %s", exc)
