"""TOML config loader with defaults and per-stage LLM resolution."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import paths


@dataclass
class ModelConfig:
    model: str = "mimo-v2.5-pro"
    base_url: str = "https://token-plan-cn.xiaomimimo.com/anthropic"
    api_key: str = ""
    api_key_env: str = "ANTHROPIC_AUTH_TOKEN"
    max_tokens: int | None = None


@dataclass
class CaptureConfig:
    event_driven: bool = True
    heartbeat_minutes: int = 10
    debounce_seconds: float = 3.0
    min_capture_gap_seconds: float = 2.0
    dedup_interval_seconds: float = 1.0
    same_window_dedup_seconds: float = 5.0
    interval_minutes: int = 10
    buffer_retention_hours: int = 168
    screenshot_retention_hours: int = 24
    buffer_max_mb: int = 2000
    include_screenshot: bool = True
    screenshot_max_width: int = 1920
    screenshot_jpeg_quality: int = 80
    ax_depth: int = 100
    ax_timeout_seconds: int = 3


@dataclass
class TimelineConfig:
    window_minutes: int = 1
    cold_lookback_minutes: int = 30
    recent_context_blocks: int = 720


@dataclass
class WriterConfig:
    soft_limit_tokens: int = 20_000
    hard_limit_tokens: int = 50_000
    dedup_window_hours: int = 24
    cold_start_conservative_hours: int = 0
    max_tool_iterations: int = 12


@dataclass
class SessionConfig:
    gap_minutes: int = 5
    soft_cut_minutes: int = 3
    max_session_hours: int = 2
    tick_seconds: int = 30
    flush_minutes: int = 5


@dataclass
class ReducerConfig:
    enabled: bool = True
    daily_tick_hour: int = 23
    daily_tick_minute: int = 55


@dataclass
class ClassifierConfig:
    interval_minutes: int = 30


@dataclass
class MemoryConfig:
    auto_dormant_days: int = 30


@dataclass
class SearchConfig:
    default_top_k: int = 5
    filter_superseded_by_default: bool = True


@dataclass
class MCPConfig:
    auto_start: bool = True
    transport: str = "streamable-http"
    host: str = "127.0.0.1"
    port: int = 8742


@dataclass
class Config:
    models: dict[str, ModelConfig] = field(default_factory=dict)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    timeline: TimelineConfig = field(default_factory=TimelineConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    reducer: ReducerConfig = field(default_factory=ReducerConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)
    writer: WriterConfig = field(default_factory=WriterConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)

    def model_for(self, stage: str) -> ModelConfig:
        return self.models.get(stage) or self.models.get("default") or ModelConfig()


def resolve_api_key(cfg: ModelConfig) -> str | None:
    if cfg.api_key:
        return cfg.api_key
    if cfg.api_key_env:
        return os.environ.get(cfg.api_key_env)
    return None


def _as_dict(section: Any) -> dict:
    return section if isinstance(section, dict) else {}


def _build_models(raw: dict) -> dict[str, ModelConfig]:
    default_data = _as_dict(raw.get("default", {}))
    default_allowed = {
        k: v for k, v in default_data.items() if k in ModelConfig.__dataclass_fields__
    }
    default = ModelConfig(**default_allowed)
    models = {"default": default}
    for name, section in raw.items():
        if name == "default":
            continue
        data = _as_dict(section)
        allowed = {k: v for k, v in data.items() if k in ModelConfig.__dataclass_fields__}
        models[name] = ModelConfig(**{**default.__dict__, **allowed})
    return models


def _build_dataclass(cls, raw: dict):
    allowed = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
    return cls(**allowed)


def load(path: Path | None = None) -> Config:
    path = path or paths.config_file()
    raw: dict = {}
    if path.exists():
        with open(path, "rb") as f:
            raw = tomllib.load(f)

    return Config(
        models=_build_models(_as_dict(raw.get("models"))),
        capture=_build_dataclass(CaptureConfig, _as_dict(raw.get("capture"))),
        timeline=_build_dataclass(TimelineConfig, _as_dict(raw.get("timeline"))),
        session=_build_dataclass(SessionConfig, _as_dict(raw.get("session"))),
        reducer=_build_dataclass(ReducerConfig, _as_dict(raw.get("reducer"))),
        classifier=_build_dataclass(ClassifierConfig, _as_dict(raw.get("classifier"))),
        writer=_build_dataclass(WriterConfig, _as_dict(raw.get("writer"))),
        memory=_build_dataclass(MemoryConfig, _as_dict(raw.get("memory"))),
        search=_build_dataclass(SearchConfig, _as_dict(raw.get("search"))),
        mcp=_build_dataclass(MCPConfig, _as_dict(raw.get("mcp"))),
    )


DEFAULT_CONFIG_TEMPLATE = """# OpenChronicle configuration
# All LLM stages go through litellm. Each stage inherits from [models.default].

[models.default]
model = "gpt-5.4-nano"
api_key_env = "OPENAI_API_KEY"
# base_url = ""
# api_key = ""          # overrides api_key_env if set

[models.compact]
# Accuracy-sensitive: match or exceed the default.

[models.timeline]
# 1-minute activity normalisation (verbatim-preserving). The reducer,
# which runs every flush_minutes >= 5m, is the stage that does real
# compression: timeline only cleans up, de-duplicates, and separates
# independent conversations. A small model is fine: the prompt is short
# and the output is a bounded JSON list.

[models.reducer]
# Session-level S2 reduce-from-blocks. Prompt is short (blocks are already
# compressed) but output quality matters: consider a stronger model here.

[models.classifier]
# Extracts classifiable long-term facts from the day's event-daily entries
# into user-/project-/topic-/tool-/person-/org- files via tool calls.
# Accuracy-sensitive: pick a capable model.

[capture]
event_driven = true
heartbeat_minutes = 10
debounce_seconds = 3.0
min_capture_gap_seconds = 2.0
dedup_interval_seconds = 1.0
same_window_dedup_seconds = 5.0
buffer_retention_hours = 168
screenshot_retention_hours = 24
buffer_max_mb = 2000
include_screenshot = true
screenshot_max_width = 1920
screenshot_jpeg_quality = 80
ax_depth = 100
ax_timeout_seconds = 3

[timeline]
window_minutes = 1
cold_lookback_minutes = 30
recent_context_blocks = 720

[writer]
soft_limit_tokens = 20000
hard_limit_tokens = 50000
dedup_window_hours = 24
cold_start_conservative_hours = 0

[session]
gap_minutes = 5
soft_cut_minutes = 3
max_session_hours = 2
tick_seconds = 30
flush_minutes = 5

[reducer]
enabled = true
daily_tick_hour = 23
daily_tick_minute = 55

[classifier]
interval_minutes = 30

[memory]
auto_dormant_days = 30

[search]
default_top_k = 5
filter_superseded_by_default = true

[mcp]
auto_start = true
transport = "streamable-http"
host = "127.0.0.1"
port = 8742
"""


def write_default_if_missing(path: Path | None = None) -> bool:
    path = path or paths.config_file()
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    return True
