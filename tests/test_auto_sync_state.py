"""Tests for auto_sync state.json management."""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_load_state_returns_default_when_missing(tmp_path):
    from auto_sync import load_state
    state = load_state(str(tmp_path / "missing.json"))
    assert state["last_scan_at"] == ""
    assert state["sources"] == {}


def test_save_state_writes_atomically(tmp_path):
    from auto_sync import save_state
    state_path = tmp_path / "state.json"
    save_state(str(state_path), {
        "last_scan_at": "2026-06-21T08:00:00+08:00",
        "sources": {"folder:X": {"last_scan_at": "2026-06-21T08:00:00+08:00",
                                  "last_success": True, "last_error": None,
                                  "consecutive_failures": 0}},
        "stats": {}
    })
    assert state_path.exists()
    loaded = json.loads(state_path.read_text(encoding="utf-8"))
    assert loaded["last_scan_at"] == "2026-06-21T08:00:00+08:00"


def test_update_source_state_on_success(tmp_path):
    from auto_sync import update_source_state
    state = {"sources": {}}
    update_source_state(state, "folder:X", success=True,
                        scan_at="2026-06-21T08:00:00+08:00")
    assert state["sources"]["folder:X"]["last_success"] is True
    assert state["sources"]["folder:X"]["consecutive_failures"] == 0


def test_update_source_state_increments_failures(tmp_path):
    from auto_sync import update_source_state
    state = {"sources": {"folder:X": {"consecutive_failures": 1,
                                       "last_success": False,
                                       "last_scan_at": "2026-06-20T08:00:00+08:00",
                                       "last_error": "old"}}}
    update_source_state(state, "folder:X", success=False,
                        scan_at="2026-06-21T08:00:00+08:00", error="new error")
    assert state["sources"]["folder:X"]["consecutive_failures"] == 2
    assert state["sources"]["folder:X"]["last_error"] == "new error"
    # last_scan_at should NOT advance on failure
    assert state["sources"]["folder:X"]["last_scan_at"] == "2026-06-20T08:00:00+08:00"
