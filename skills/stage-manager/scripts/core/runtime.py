#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Stage-Manager runtime utilities: paths, I/O, output, env discovery, and write lock."""

import contextlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


SESSION_MAX_ENTRIES = 20
VERSION = "1.1.0"
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(PACKAGE_DIR)
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(SKILL_DIR, "references", "stage_template.md")
LOCK_FILENAME = ".stage-manager.lock"

ALLOWED_STAGE_STATUS = {"PLANNING", "IN_PROGRESS", "TESTING", "COMPLETED", "ARCHIVED"}
ALLOWED_LOG_STATUS = {"done", "in-progress", "blocked"}
ALLOWED_EXECUTOR = {"human", "agent", "sub_agent"}
ALLOWED_VERIFY_BY = {"task_completion", "evidence_review", "metric_threshold", "artifact_presence"}

STRINGS = {
    "stages_index_head": (
        "# Stages Index\n\n"
        "> This file is auto-maintained by stage-manager. All assets are under `.stages/`.\n\n"
        "---\n\n## Stage Index\n"
    ),
    "adrs_head": "# Architectural Decision Records (ADRS)\n\n---\n\n## Decision Index\n",
    "sessions_head": "# Stage Session Logs (Compressed)\n\n---\n\n## Session Summaries\n",
    "backlogs_head": "# Project Backlogs\n\n## [TECH_DEBT] Technical Debt\n\n## [ROADMAP] Roadmap\n",
}


@dataclass
class PathConfig:
    """Store all derived runtime paths used by stage-manager."""

    root_dir: str = ""
    asset_root: str = ""
    backlog_file: str = ""
    stages_index: str = ""
    adr_index: str = ""
    session_file: str = ""
    stages_exec_dir: str = ""
    archive_exec_dir: str = ""

    def configure(self, project_root: str):
        """Refresh runtime path config from project root without file I/O."""
        self.root_dir = os.path.abspath(project_root)
        self.asset_root = os.path.join(self.root_dir, ".stages")
        self.backlog_file = os.path.join(self.asset_root, "BACKLOGS.md")
        self.stages_index = os.path.join(self.asset_root, "STAGES.md")
        self.adr_index = os.path.join(self.asset_root, "ADRS.md")
        self.session_file = os.path.join(self.asset_root, "STAGE_SESSIONS.md")
        self.stages_exec_dir = os.path.join(self.asset_root, "stages")
        self.archive_exec_dir = os.path.join(self.asset_root, "archive", "stages")


@dataclass
class OutputCtx:
    """Store JSON output mode and accumulated payload."""

    json_mode: bool = False
    data: Dict[str, Any] = field(default_factory=dict)


cfg = PathConfig()
_out = OutputCtx()


def emit(key: str, value: Any):
    """Accumulate one output field in JSON mode instead of printing."""
    if _out.json_mode:
        _out.data[key] = value


def info(msg: str):
    """Emit user-facing message; append to `messages` in JSON mode."""
    if _out.json_mode:
        _out.data.setdefault("messages", []).append(msg)
    else:
        print(msg)


def flush_json():
    """Print accumulated JSON payload once at the end."""
    if _out.json_mode:
        print(json.dumps(_out.data, ensure_ascii=False, indent=2))


def now_date() -> str:
    """Return current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def now_datetime() -> str:
    """Return current time in YYYY-MM-DD HH:MM format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def read_text(path: str) -> str:
    """Read UTF-8 text file; return empty string when missing."""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path: str, content: str):
    """Write via temp-file replacement to avoid partial-write corruption."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(tmp, path)


def _lock_path() -> str:
    """Return stage write-lock file path for current project."""
    return os.path.join(cfg.asset_root, LOCK_FILENAME)


def _lock_payload(command: str) -> Dict[str, Any]:
    """Generate write-lock metadata for conflict hints and stale-lock cleanup."""
    return {
        "pid": os.getpid(),
        "user": get_sys_user(),
        "command": command,
        "cwd": os.getcwd(),
        "started_at": now_datetime(),
    }


def _read_lock_payload(path: str) -> Dict[str, Any]:
    """Read write-lock metadata; return empty dict on parse failure."""
    try:
        raw = read_text(path).strip()
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _pid_is_alive(pid: Any) -> bool:
    """Check whether the given PID is still alive."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _format_lock_holder(meta: Dict[str, Any]) -> str:
    """Format lock metadata into user-readable text."""
    parts = []
    if meta.get("user"):
        parts.append(f"user={meta['user']}")
    if meta.get("pid"):
        parts.append(f"pid={meta['pid']}")
    if meta.get("command"):
        parts.append(f"cmd={meta['command']}")
    if meta.get("started_at"):
        parts.append(f"started={meta['started_at']}")
    return ", ".join(parts) if parts else "unknown holder"


@contextlib.contextmanager
def write_lock(command: str):
    """Acquire single-writer lock to ensure only one stage write command runs at a time."""
    ensure_structure()
    path = _lock_path()
    meta = _lock_payload(command)
    payload = json.dumps(meta, ensure_ascii=False, indent=2)
    acquired = False

    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            acquired = True
            break
        except FileExistsError:
            existing = _read_lock_payload(path)
            if existing.get("pid") == os.getpid():
                acquired = True
                break
            if not _pid_is_alive(existing.get("pid")):
                try:
                    os.remove(path)
                    continue
                except FileNotFoundError:
                    continue
            holder = _format_lock_holder(existing)
            raise RuntimeError(
                f"[BUSY] Detected another stage write command running: {holder}。"
                " Please wait until it finishes, or retry after confirming abnormal exit."
            )

    if not acquired:
        raise RuntimeError("[BUSY] Failed to acquire stage write lock. Please retry later.")

    try:
        yield
    finally:
        current = _read_lock_payload(path)
        if current.get("pid") == os.getpid():
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


def discover_project_root(root_override: str | None = None) -> str:
    """Detect project root: explicit arg first, then env var and upward search."""
    if root_override:
        return os.path.abspath(root_override)
    env_root = os.environ.get("STAGE_MANAGER_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    probe = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(probe, ".git")) or os.path.isdir(os.path.join(probe, ".stages")):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            return os.path.abspath(os.getcwd())
        probe = parent


def get_git_info() -> str:
    """Return current Git short commit hash; fallback to local-env on failure."""
    try:
        short_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return f"git@{short_hash}"
    except Exception:
        return "local-env"


def get_sys_user() -> str:
    """Return current system username."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def slugify_name(name: str) -> str:
    """Convert stage name to filename-safe slug."""
    slug = re.sub(r"[^a-z0-9\-_.]+", "-", re.sub(r"\s+", "-", name.strip().lower()))
    return re.sub(r"-{2,}", "-", slug).strip("-") or "unnamed-stage"


def ensure_structure():
    """Ensure `.stages` tree and base index files exist; auto-create when missing."""
    for directory in [cfg.asset_root, cfg.stages_exec_dir, cfg.archive_exec_dir]:
        os.makedirs(directory, exist_ok=True)

    defaults = [
        (
            cfg.stages_index,
            lambda: (
                STRINGS["stages_index_head"] + "\n---\n\n## Quick Status\n"
                f"- [HEARTBEAT] Init\n- [LAST_SESSION] NoneEN\n"
                f"- Last sync: {now_datetime()} | User: {get_sys_user()} | Version: {get_git_info()}\n"
            ),
        ),
        (
            cfg.adr_index,
            lambda: STRINGS["adrs_head"] + f"\n---\n\n## Statistics\n- Total decisions: 0\n- Last updated: {now_datetime()}\n",
        ),
        (
            cfg.session_file,
            lambda: STRINGS["sessions_head"] + "\n---\n\n## Recent Records\n- NoneEN\n",
        ),
        (cfg.backlog_file, lambda: STRINGS["backlogs_head"]),
    ]
    for path, content_fn in defaults:
        if not os.path.exists(path):
            write_text(path, content_fn())
