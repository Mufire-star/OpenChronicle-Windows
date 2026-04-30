"""Foreground app/window metadata for Windows."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WindowMeta:
    app_name: str = ""
    title: str = ""
    bundle_id: str = ""


def active_window() -> WindowMeta:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return WindowMeta()

    length = user32.GetWindowTextLengthW(hwnd)
    title_buf = ctypes.create_unicode_buffer(max(1, length + 1))
    user32.GetWindowTextW(hwnd, title_buf, len(title_buf))

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return WindowMeta(title=title_buf.value)

    process_path = _query_process_path(kernel32, pid.value)
    app_name = Path(process_path).stem if process_path else f"pid-{pid.value}"
    bundle_id = process_path or app_name
    return WindowMeta(app_name=app_name, title=title_buf.value, bundle_id=bundle_id)


def _query_process_path(kernel32: ctypes.WinDLL, pid: int) -> str:
    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return ""

    try:
        size = wintypes.DWORD(32768)
        path_buf = ctypes.create_unicode_buffer(size.value)
        query = kernel32.QueryFullProcessImageNameW
        query.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        query.restype = wintypes.BOOL
        if query(handle, 0, path_buf, ctypes.byref(size)):
            return path_buf.value
    finally:
        kernel32.CloseHandle(handle)

    return ""
