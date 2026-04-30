"""Collect OAuth provider auth status from ~/.hermes/auth.json."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..cache import get_cached_or_compute
from .models import ProviderAuth, ProvidersState
from .utils import default_hermes_dir, parse_timestamp

# Human-readable names for known provider IDs.
_DISPLAY_NAMES = {
    "nous": "Nous Portal",
    "openai-codex": "OpenAI Codex",
    "anthropic": "Anthropic Claude",
    "openrouter": "OpenRouter",
    "zai": "Z.AI",
    "google": "Google",
    "xai": "xAI Grok",
}


def _mask_token(token: Optional[str]) -> str:
    if not token or not isinstance(token, str):
        return ""
    token = token.strip()
    if len(token) <= 8:
        return "•" * len(token)
    return f"{token[:4]}…{token[-4:]}"


def _classify(expires_at: Optional[datetime], has_token: bool) -> str:
    if not has_token:
        return "missing"
    if expires_at is None:
        return "connected"  # no expiry recorded → assume ok
    now = datetime.now()
    if expires_at < now:
        return "expired"
    # expiring soon: within 7 days
    delta = (expires_at - now).total_seconds()
    if delta < 7 * 86400:
        return "expiring"
    return "connected"


def _build_provider(pid: str, entry: dict, active_id: Optional[str]) -> ProviderAuth:
    name = _DISPLAY_NAMES.get(pid, pid.replace("-", " ").title())

    # Token can live under several keys depending on provider/flow.
    token = (
        entry.get("access_token")
        or entry.get("api_key")
        or entry.get("token")
        or (entry.get("tokens", {}) or {}).get("access_token")
        or entry.get("agent_key")
    )

    expires = parse_timestamp(
        entry.get("expires_at")
        or entry.get("expiry")
        or (entry.get("tokens", {}) or {}).get("expires_at")
        or entry.get("agent_key_expires_at")
    )
    obtained = parse_timestamp(
        entry.get("obtained_at")
        or entry.get("last_refresh")
        or entry.get("agent_key_obtained_at")
    )

    scope = entry.get("scope", "")
    if isinstance(scope, list):
        scope = " ".join(scope)

    auth_mode = entry.get("auth_mode") or entry.get("auth_type") or ("oauth" if token else "")

    return ProviderAuth(
        id=pid,
        name=name,
        status=_classify(expires, bool(token)),
        token_preview=_mask_token(token),
        expires_at=expires,
        obtained_at=obtained,
        scope=scope if isinstance(scope, str) else "",
        is_active=(pid == active_id),
        auth_mode=auth_mode if isinstance(auth_mode, str) else "",
    )


def _do_collect_providers(hermes_path: Path) -> ProvidersState:
    auth_path = hermes_path / "auth.json"
    anthropic_path = hermes_path / ".anthropic_oauth.json"

    providers: dict[str, ProviderAuth] = {}
    active: Optional[str] = None

    # auth.json — Nous + OpenAI-Codex via `providers`, plus `credential_pool` for the rest.
    if auth_path.exists():
        try:
            data = json.loads(auth_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            active = data.get("active_provider")
            for pid, entry in (data.get("providers") or {}).items():
                if isinstance(entry, dict):
                    providers[pid] = _build_provider(pid, entry, active)
            for pid, entry in (data.get("credential_pool") or {}).items():
                if pid in providers:
                    continue
                # credential_pool values are lists of credential records — take
                # the highest-priority one (lowest priority number, typically 0).
                if isinstance(entry, list) and entry:
                    records = [r for r in entry if isinstance(r, dict)]
                    if records:
                        records.sort(key=lambda r: r.get("priority", 999))
                        providers[pid] = _build_provider(pid, records[0], active)
                elif isinstance(entry, dict):
                    providers[pid] = _build_provider(pid, entry, active)
                elif isinstance(entry, str) and entry:
                    providers[pid] = ProviderAuth(
                        id=pid,
                        name=_DISPLAY_NAMES.get(pid, pid.title()),
                        status="connected",
                        token_preview=_mask_token(entry),
                        auth_mode="api_key",
                        is_active=(pid == active),
                    )

    # Anthropic PKCE tokens live in their own file when present.
    if anthropic_path.exists() and "anthropic" not in providers:
        try:
            data = json.loads(anthropic_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            providers["anthropic"] = _build_provider("anthropic", data, active)

    ordered = sorted(
        providers.values(),
        key=lambda p: (not p.is_active, p.status != "connected", p.name.lower()),
    )

    return ProvidersState(providers=ordered, active_provider=active)


def collect_providers(hermes_dir: Optional[str] = None) -> ProvidersState:
    hermes_path = Path(default_hermes_dir(hermes_dir))
    return get_cached_or_compute(
        cache_key=f"providers:{hermes_path}",
        compute_fn=lambda: _do_collect_providers(hermes_path),
        file_paths=[hermes_path / "auth.json", hermes_path / ".anthropic_oauth.json"],
        ttl=30,
    )
