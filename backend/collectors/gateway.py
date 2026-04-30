"""Gateway status + actions (restart / update hermes)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from ..cache import get_cached_or_compute
from .models import GatewayState, PlatformStatus
from .utils import default_hermes_dir, parse_timestamp

# Maps a stable action name (used in URLs + state files) to the `hermes`
# argv to execute. Adding an action = adding one entry here.
ACTIONS: dict[str, list[str]] = {
    "gateway-restart": ["gateway", "restart"],
    "hermes-update": ["update"],
}
ACTION_NAMES = frozenset(ACTIONS)

# Bounded by len(ACTIONS); entries popped once we reap the child.
_action_procs: dict[str, subprocess.Popen] = {}


def _pid_alive(pid: Optional[int]) -> bool:
    """Return True only if the pid is live AND not a zombie.

    `os.kill(pid, 0)` succeeds for zombies too, so for real liveness we also
    read /proc/<pid>/status on Linux. On non-Linux we fall back to os.kill.
    """
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError, TypeError):
        return False
    try:
        with open(f"/proc/{int(pid)}/status", "r") as f:
            for line in f:
                if line.startswith("State:"):
                    return "Z" not in line.split(":", 1)[1]
    except (OSError, ValueError):
        pass
    return True


def _do_collect_gateway(hermes_path: Path) -> GatewayState:
    state_path = hermes_path / "gateway_state.json"
    if not state_path.exists():
        return GatewayState()

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return GatewayState()
    if not isinstance(data, dict):
        return GatewayState()

    pid = data.get("pid")
    platforms: list[PlatformStatus] = []
    for name, info in (data.get("platforms") or {}).items():
        if not isinstance(info, dict):
            continue
        platforms.append(
            PlatformStatus(
                name=name,
                state=str(info.get("state") or "unknown"),
                updated_at=parse_timestamp(info.get("updated_at")),
                error_code=info.get("error_code") or None,
                error_message=info.get("error_message") or None,
            )
        )
    platforms.sort(key=lambda p: p.name)

    return GatewayState(
        state=str(data.get("gateway_state") or "unknown"),
        pid=pid if isinstance(pid, int) else None,
        pid_alive=_pid_alive(pid),
        kind=str(data.get("kind") or ""),
        restart_requested=bool(data.get("restart_requested")),
        exit_reason=data.get("exit_reason"),
        updated_at=parse_timestamp(data.get("updated_at")),
        active_agents=int(data.get("active_agents") or 0),
        platforms=platforms,
    )


def collect_gateway_status(hermes_dir: Optional[str] = None) -> GatewayState:
    hermes_path = Path(default_hermes_dir(hermes_dir))
    return get_cached_or_compute(
        cache_key=f"gateway:{hermes_path}",
        compute_fn=lambda: _do_collect_gateway(hermes_path),
        file_paths=[hermes_path / "gateway_state.json"],
        ttl=5,
    )


# ── Actions: restart / update ──────────────────────────────────────────

def _log_dir(hermes_path: Path) -> Path:
    d = hermes_path / "logs" / "hud"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _state_path(hermes_path: Path, name: str) -> Path:
    return _log_dir(hermes_path) / f"{name}.json"


def _log_path(hermes_path: Path, name: str) -> Path:
    return _log_dir(hermes_path) / f"{name}.log"


def _write_state(path: Path, state: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run_action(name: str, hermes_dir: Optional[str] = None) -> dict:
    """Spawn a detached hermes action. Returns a descriptor dict."""
    if name not in ACTION_NAMES:
        raise ValueError(f"Unknown action: {name}")

    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        raise RuntimeError("hermes CLI not found on PATH")

    hermes_path = Path(default_hermes_dir(hermes_dir))
    log_file = _log_path(hermes_path, name)
    state_file = _state_path(hermes_path, name)

    argv_tail = ACTIONS[name]

    env = os.environ.copy()
    env["HERMES_NONINTERACTIVE"] = "1"

    log_fh = open(log_file, "wb", buffering=0)
    try:
        os.chmod(log_file, 0o600)
    except OSError:
        pass

    proc = subprocess.Popen(
        [hermes_bin, *argv_tail],
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        cwd=os.path.expanduser("~"),
        start_new_session=True,
    )
    log_fh.close()
    _action_procs[name] = proc

    state = {
        "name": name,
        "pid": proc.pid,
        "started_at": time.time(),
        "log_path": str(log_file),
    }
    _write_state(state_file, state)
    return state


def _tail_lines(path: Path, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    try:
        data = path.read_bytes()
    except OSError:
        return []
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return lines[-max_lines:]


def read_action_status(name: str, hermes_dir: Optional[str] = None) -> dict:
    if name not in ACTION_NAMES:
        raise ValueError(f"Unknown action: {name}")

    hermes_path = Path(default_hermes_dir(hermes_dir))
    state = _read_state(_state_path(hermes_path, name))
    log_file = _log_path(hermes_path, name)

    pid = state.get("pid")
    exit_code: Optional[int] = state.get("exit_code")

    # If we spawned it in this process, reap it non-blockingly so the pid
    # doesn't linger as a zombie.
    proc = _action_procs.get(name)
    if proc is not None and proc.pid == pid:
        rc = proc.poll()
        if rc is not None:
            exit_code = rc
            _action_procs.pop(name, None)

    running = exit_code is None and _pid_alive(pid)

    return {
        "name": name,
        "pid": pid,
        "running": running,
        "exit_code": exit_code,
        "started_at": state.get("started_at"),
        "log_path": str(log_file),
        "lines": _tail_lines(log_file),
    }
