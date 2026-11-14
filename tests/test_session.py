import json
import os
import stat
from unittest.mock import AsyncMock, MagicMock

import pytest

from stealth_browser.session import save_cookies


async def test_save_cookies_creates_private_file_and_parent(tmp_path):
    page = MagicMock()
    page.context.cookies = AsyncMock(return_value=[{"name": "session", "value": "synthetic"}])
    destination = tmp_path / "sessions" / "qa" / "cookies.json"

    await save_cookies(page, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == [
        {"name": "session", "value": "synthetic"}
    ]
    if os.name == "posix":
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600


async def test_save_cookies_restricts_permissions_of_existing_file(tmp_path):
    if os.name != "posix":
        pytest.skip("POSIX mode bits are not Windows ACLs")
    destination = tmp_path / "cookies.json"
    destination.write_text("{}", encoding="utf-8")
    destination.chmod(0o644)
    page = MagicMock()
    page.context.cookies = AsyncMock(return_value=[])

    await save_cookies(page, destination)

    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


async def test_save_cookies_replaces_symlink_without_following_target(tmp_path):
    if os.name != "posix":
        pytest.skip("Symlink creation requires POSIX test permissions")
    target = tmp_path / "target.json"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "cookies.json"
    link.symlink_to(target)
    page = MagicMock()
    page.context.cookies = AsyncMock(return_value=[{"name": "x", "value": "secret"}])

    await save_cookies(page, link)
    assert not link.is_symlink()
    assert json.loads(link.read_text(encoding="utf-8")) == [
        {"name": "x", "value": "secret"}
    ]
    assert target.read_text(encoding="utf-8") == "keep"
