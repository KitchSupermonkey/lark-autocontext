"""Tests for auto_sync list-only + finalize flow."""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def _make_config(tmp_path, sources=None):
    """Create a minimal config.json in tmp_path."""
    cfg = {"sources": sources or [
        {"type": "folder", "token": "fldFAKE", "name": "Test", "key": "folder:fldFAKE"}
    ]}
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return str(p)


def test_list_only_first_run(tmp_path, monkeypatch):
    from auto_sync import cmd_list_only
    import argparse

    cfg_path = _make_config(tmp_path)
    state_path = str(tmp_path / "state.json")

    # Monkeypatch scanner.list_changed to return fake data
    import scanner
    monkeypatch.setattr(scanner, "list_changed", lambda sources, since: {
        "changed": [{"doc_token": "DOC1", "url": "https://x", "title": "T1", "edited_time": "2026-06-21", "source": "folder:fldFAKE"}],
        "source_results": {"folder:fldFAKE": {"ok": True, "error": None}}
    })

    # Monkeypatch load_state / save_state paths
    import auto_sync
    monkeypatch.setattr(auto_sync, "STATE_PATH", state_path)
    monkeypatch.setattr(auto_sync, "PENDING_PATH", str(tmp_path / "pending.json"))

    args = argparse.Namespace(config=cfg_path)
    ret = cmd_list_only(args)
    assert ret == 0
    pending = json.loads((tmp_path / "pending.json").read_text(encoding="utf-8"))
    assert len(pending["changes"]) == 1
    assert pending["changes"][0]["doc_token"] == "DOC1"
    assert "folder:fldFAKE" in pending["source_scans"]


def test_list_only_no_changes(tmp_path, monkeypatch):
    from auto_sync import cmd_list_only
    import argparse

    cfg_path = _make_config(tmp_path)
    state_path = str(tmp_path / "state.json")

    import scanner
    monkeypatch.setattr(scanner, "list_changed", lambda sources, since: {
        "changed": [], "source_results": {}
    })

    import auto_sync
    monkeypatch.setattr(auto_sync, "STATE_PATH", state_path)
    monkeypatch.setattr(auto_sync, "PENDING_PATH", str(tmp_path / "pending.json"))

    args = argparse.Namespace(config=cfg_path)
    ret = cmd_list_only(args)
    assert ret == 0
    pending = json.loads((tmp_path / "pending.json").read_text(encoding="utf-8"))
    assert pending["changes"] == []


def test_finalize_updates_state(tmp_path, monkeypatch):
    from auto_sync import cmd_finalize
    import argparse

    state_path = str(tmp_path / "state.json")
    pending_path = str(tmp_path / "pending.json")

    pending = {
        "scan_at": "2026-06-21T08:00:00+08:00",
        "source_scans": {"folder:fldFAKE": "2026-06-21T08:00:00+08:00"},
        "changes": [],
    }
    with open(pending_path, "w", encoding="utf-8") as f:
        json.dump(pending, f)

    import auto_sync
    monkeypatch.setattr(auto_sync, "STATE_PATH", state_path)
    monkeypatch.setattr(auto_sync, "PENDING_PATH", pending_path)

    args = argparse.Namespace(commit=False)
    ret = cmd_finalize(args)
    assert ret == 0
    assert not os.path.exists(pending_path)  # pending deleted
    state = json.loads(open(state_path, "r", encoding="utf-8").read())
    assert state["last_scan_at"] == "2026-06-21T08:00:00+08:00"
    assert state["sources"]["folder:fldFAKE"]["last_success"] is True


def test_finalize_no_pending(tmp_path, monkeypatch):
    from auto_sync import cmd_finalize
    import argparse

    import auto_sync
    monkeypatch.setattr(auto_sync, "STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setattr(auto_sync, "PENDING_PATH", str(tmp_path / "nonexistent.json"))

    args = argparse.Namespace(commit=False)
    ret = cmd_finalize(args)
    assert ret == 0
