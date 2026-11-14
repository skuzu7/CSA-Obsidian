"""Cookie material must never hit disk without explicit opt-in."""

import json
import os
import stat

import pytest

from cookie_export import persist_cookie_export


def test_in_memory_default_creates_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert persist_cookie_export([{"name": "synthetic", "value": "TEST_ONLY"}], None) is None
    assert list(tmp_path.iterdir()) == []


def test_export_requires_explicit_destination_and_restricts_permissions(tmp_path):
    destination = tmp_path / "cookies.json"
    data = [{"name": "synthetic", "value": "TEST_ONLY"}]
    assert persist_cookie_export(data, destination) == destination
    assert json.loads(destination.read_text(encoding="utf-8")) == data
    if os.name == "posix":
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
        assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700


def test_existing_cookie_file_cannot_be_overwritten(tmp_path):
    destination = tmp_path / "cookies.json"
    destination.write_text("keep me", encoding="utf-8")
    with pytest.raises(FileExistsError):
        persist_cookie_export([{"name": "another"}], destination)
    assert destination.read_text(encoding="utf-8") == "keep me"
