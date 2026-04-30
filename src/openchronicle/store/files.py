"""Markdown memory file I/O: read, write, parse frontmatter, parse entries."""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter

from .. import paths

_REPLACE_RETRIES = 8
_REPLACE_RETRY_DELAY_SECONDS = 0.01


def atomic_write_text(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        with contextlib.suppress(FileNotFoundError):
            os.chmod(tmp_path, path.stat().st_mode & 0o7777)
        _replace_with_retry(tmp_path, path)
        with contextlib.suppress(OSError):
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
        raise


def _replace_with_retry(src: Path, dst: Path) -> None:
    last_exc: PermissionError | None = None
    for attempt in range(_REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_exc = exc
            if attempt + 1 == _REPLACE_RETRIES:
                break
            time.sleep(_REPLACE_RETRY_DELAY_SECONDS * (attempt + 1))
    if last_exc is not None:
        raise last_exc


VALID_PREFIXES = ("user-", "project-", "tool-", "topic-", "person-", "org-", "event-")

_lock_registry_lock = threading.Lock()
_path_locks: dict[str, threading.Lock] = {}


def _lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _lock_registry_lock:
        lock = _path_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _path_locks[key] = lock
        return lock


@contextlib.contextmanager
def file_lock(path: Path) -> Iterator[None]:
    with _lock_for(path):
        yield


ENTRY_HEADING_RE = re.compile(
    r"^##\s*\[(?P<ts>[^\]]+)\]\s*\{id:\s*(?P<id>[a-zA-Z0-9\-]+)\}(?P<tags>[^\n]*)$",
    re.MULTILINE,
)


@dataclass
class ParsedEntry:
    id: str
    timestamp: str
    tags: list[str]
    heading_line: str
    body: str
    superseded_by: str | None = None


@dataclass
class ParsedFile:
    path: Path
    description: str
    tags: list[str]
    status: str
    created: str
    updated: str
    entry_count: int
    needs_compact: bool
    entries: list[ParsedEntry] = field(default_factory=list)
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)


def memory_path(name: str) -> Path:
    if "/" in name or "\\" in name:
        raise ValueError(f"memory path must not contain slashes: {name!r}")
    if not name.endswith(".md"):
        name = name + ".md"
    return paths.memory_dir() / name


def validate_prefix(name: str) -> str:
    stem = name.removesuffix(".md")
    for p in VALID_PREFIXES:
        if stem.startswith(p) and len(stem) > len(p):
            return p.rstrip("-")
    raise ValueError(
        f"filename {name!r} must start with one of: {', '.join(VALID_PREFIXES)}"
    )


def today() -> str:
    return date.today().isoformat()


def default_frontmatter(*, description: str, tags: list[str]) -> dict[str, Any]:
    return {
        "description": description,
        "tags": tags,
        "status": "active",
        "created": today(),
        "updated": today(),
        "entry_count": 0,
        "needs_compact": False,
    }


def write_file(path: Path, fm: dict[str, Any], body: str) -> None:
    post = frontmatter.Post(content=body, **fm)
    text = frontmatter.dumps(post) + ("\n" if not body.endswith("\n") else "")
    atomic_write_text(path, text)


def read_file(path: Path) -> ParsedFile:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        post = frontmatter.load(f)
    fm = dict(post.metadata)
    body = post.content
    entries = _parse_entries(body)
    return ParsedFile(
        path=path,
        description=str(fm.get("description", "")),
        tags=list(fm.get("tags", []) or []),
        status=str(fm.get("status", "active")),
        created=str(fm.get("created", "")),
        updated=str(fm.get("updated", "")),
        entry_count=int(fm.get("entry_count", len(entries)) or 0),
        needs_compact=bool(fm.get("needs_compact", False)),
        entries=entries,
        raw_frontmatter=fm,
    )


def _parse_entries(body: str) -> list[ParsedEntry]:
    entries: list[ParsedEntry] = []
    matches = list(ENTRY_HEADING_RE.finditer(body))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        tag_str = m.group("tags") or ""
        raw_tags = [t.strip() for t in tag_str.split() if t.strip().startswith("#")]
        tags = [t[1:] for t in raw_tags]
        superseded_by = None
        for t in tags:
            if t.startswith("superseded-by:"):
                superseded_by = t.split(":", 1)[1]
                break
        entries.append(
            ParsedEntry(
                id=m.group("id"),
                timestamp=m.group("ts"),
                tags=tags,
                heading_line=m.group(0),
                body=body[start:end].strip("\n"),
                superseded_by=superseded_by,
            )
        )
    return entries


def render_heading(*, timestamp: str, entry_id: str, tags: list[str]) -> str:
    tag_part = "".join(f" #{t}" for t in tags) if tags else ""
    return f"## [{timestamp}] {{id: {entry_id}}}{tag_part}"


def render_file(
    *, fm: dict[str, Any], entries: list[ParsedEntry], header_lines: list[str] | None = None
) -> str:
    parts: list[str] = []
    if header_lines:
        parts.extend(header_lines)
        parts.append("")
    for e in entries:
        parts.append(e.heading_line)
        if e.body:
            parts.append(e.body)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def update_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    with file_lock(path):
        with path.open("r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        post.metadata.update(updates)
        atomic_write_text(path, frontmatter.dumps(post) + "\n")


def list_memory_files() -> list[Path]:
    if not paths.memory_dir().exists():
        return []
    return sorted(
        p for p in paths.memory_dir().iterdir() if p.suffix == ".md" and p.name != "index.md"
    )
