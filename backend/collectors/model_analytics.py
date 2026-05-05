"""Aggregate per-model usage from Hermes state.db."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..cache import get_cached_or_compute
from .model_info import _lookup_model, _read_models_cache
from .models import ModelAnalyticsState, ModelUsage
from .utils import default_hermes_dir, safe_get


def _table_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {str(row[1]) for row in cursor.fetchall()}


def _optional_column(columns: set[str], name: str, default: str = "NULL") -> str:
    return name if name in columns else f"{default} AS {name}"


def _model_from_row(row: sqlite3.Row) -> tuple[str, str]:
    model = safe_get(row, "model")
    provider = safe_get(row, "billing_provider") or ""

    mc_raw = safe_get(row, "model_config")
    if mc_raw:
        try:
            mc = json.loads(mc_raw)
            if not model:
                model = mc.get("model") or mc.get("default")
            if not provider:
                provider = mc.get("provider") or ""
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return str(model or "unknown"), str(provider or "")


def _capabilities(cache: dict, provider: str, model: str) -> dict:
    entry = _lookup_model(cache, provider, model)
    if not entry:
        return {}
    limit = entry.get("limit") if isinstance(entry.get("limit"), dict) else {}
    return {
        "supports_tools": bool(entry.get("tool_call")),
        "supports_vision": bool(entry.get("attachment")),
        "supports_reasoning": bool(entry.get("reasoning")),
        "supports_structured_output": bool(entry.get("structured_output")),
        "context_window": int(limit.get("context") or 0),
        "max_output_tokens": int(limit.get("output") or 0),
    }


def _do_collect(hermes_path: Path, days: Optional[int]) -> ModelAnalyticsState:
    db_path = hermes_path / "state.db"
    if not db_path.exists():
        return ModelAnalyticsState(period_days=days)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        columns = _table_columns(cursor, "sessions")
        cutoff_clause = ""
        params: list[float] = []
        if days is not None:
            cutoff_clause = "AND started_at >= ?"
            params.append(time.time() - days * 86400)

        cursor.execute(
            """
            SELECT id, source, started_at, message_count, tool_call_count,
                   input_tokens, output_tokens, cache_read_tokens,
                   cache_write_tokens, reasoning_tokens, estimated_cost_usd,
                   model_config,
                   {model},
                   {billing_provider},
                   {actual_cost_usd},
                   {api_call_count}
            FROM sessions
            WHERE LOWER(COALESCE(source, '')) != 'tool'
              {cutoff_clause}
            """.format(
                model=_optional_column(columns, "model"),
                billing_provider=_optional_column(columns, "billing_provider"),
                actual_cost_usd=_optional_column(columns, "actual_cost_usd", "0"),
                api_call_count=_optional_column(columns, "api_call_count", "0"),
                cutoff_clause=cutoff_clause,
            ),
            params,
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    models: dict[tuple[str, str], ModelUsage] = {}
    for row in rows:
        model, provider = _model_from_row(row)
        key = (model, provider)
        usage = models.setdefault(key, ModelUsage(model=model, provider=provider))
        usage.sessions += 1
        usage.messages += int(safe_get(row, "message_count", 0) or 0)
        usage.tool_calls += int(safe_get(row, "tool_call_count", 0) or 0)
        usage.api_calls += int(safe_get(row, "api_call_count", 0) or 0)
        usage.input_tokens += int(safe_get(row, "input_tokens", 0) or 0)
        usage.output_tokens += int(safe_get(row, "output_tokens", 0) or 0)
        usage.cache_read_tokens += int(safe_get(row, "cache_read_tokens", 0) or 0)
        usage.cache_write_tokens += int(safe_get(row, "cache_write_tokens", 0) or 0)
        usage.reasoning_tokens += int(safe_get(row, "reasoning_tokens", 0) or 0)
        usage.estimated_cost_usd = round(
            usage.estimated_cost_usd + float(safe_get(row, "estimated_cost_usd", 0.0) or 0.0),
            6,
        )
        usage.actual_cost_usd = round(
            usage.actual_cost_usd + float(safe_get(row, "actual_cost_usd", 0.0) or 0.0),
            6,
        )
        started = safe_get(row, "started_at")
        if started:
            dt = datetime.fromtimestamp(started)
            if usage.last_used_at is None or dt > usage.last_used_at:
                usage.last_used_at = dt

    cache = _read_models_cache(hermes_path)
    for usage in models.values():
        caps = _capabilities(cache, usage.provider, usage.model)
        for key, value in caps.items():
            setattr(usage, key, value)

    ordered = sorted(models.values(), key=lambda m: (m.total_tokens, m.sessions), reverse=True)
    return ModelAnalyticsState(models=ordered, period_days=days)


def collect_model_analytics(
    hermes_dir: Optional[str] = None,
    days: Optional[int] = 30,
) -> ModelAnalyticsState:
    hermes_path = Path(default_hermes_dir(hermes_dir))
    ttl_key = "all" if days is None else str(days)
    db_path = hermes_path / "state.db"
    return get_cached_or_compute(
        cache_key=f"model_analytics:{hermes_path}:{ttl_key}",
        compute_fn=lambda: _do_collect(hermes_path, days),
        file_paths=[db_path, hermes_path / "models_dev_cache.json"],
        ttl=30,
    )
