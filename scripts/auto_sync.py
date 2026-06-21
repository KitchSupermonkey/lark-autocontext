"""Auto-Sync coordinator: state management + workflow steps."""
import os
import sys
import json
from datetime import datetime


if sys.platform == "win32" and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_state(state_path):
    """Load .state.json, returning a default skeleton when missing."""
    if not os.path.exists(state_path):
        return {"last_scan_at": "", "sources": {}, "stats": {}}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state_path, state):
    """Atomically write state.json (write to .tmp, rename)."""
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, state_path)


def update_source_state(state, source_key, success, scan_at, error=None):
    """Update a single source's state entry."""
    src = state.setdefault("sources", {}).setdefault(source_key, {
        "last_scan_at": "",
        "last_success": True,
        "last_error": None,
        "consecutive_failures": 0,
    })
    if success:
        src["last_scan_at"] = scan_at
        src["last_success"] = True
        src["last_error"] = None
        src["consecutive_failures"] = 0
    else:
        src["last_success"] = False
        src["last_error"] = error or "unknown"
        src["consecutive_failures"] = src.get("consecutive_failures", 0) + 1
