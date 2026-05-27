import pytest

from stealth_browser.config import BrowserConfig


def test_default_config():
    cfg = BrowserConfig()
    assert cfg.headless is False
    assert cfg.block_webrtc is True
    assert cfg.humanize is True
    assert cfg.window == (1366, 768)
    assert cfg.os_target == "windows"
    assert "pt-BR" in cfg.locale


def test_from_env_headless(monkeypatch):
    monkeypatch.setenv("STEALTH_HEADLESS", "true")
    cfg = BrowserConfig.from_env()
    assert cfg.headless is True


def test_from_env_headless_false(monkeypatch):
    monkeypatch.setenv("STEALTH_HEADLESS", "false")
    cfg = BrowserConfig.from_env()
    assert cfg.headless is False


def test_from_env_locale(monkeypatch):
    monkeypatch.setenv("STEALTH_LOCALE", "en-US,en")
    cfg = BrowserConfig.from_env()
    assert cfg.locale == ["en-US", "en"]


def test_from_env_window(monkeypatch):
    monkeypatch.setenv("STEALTH_WINDOW", "1920,1080")
    cfg = BrowserConfig.from_env()
    assert cfg.window == (1920, 1080)


def test_from_env_os_target(monkeypatch):
    monkeypatch.setenv("STEALTH_OS_TARGET", "linux")
    cfg = BrowserConfig.from_env()
    assert cfg.os_target == "linux"


def test_from_env_humanize_float(monkeypatch):
    monkeypatch.setenv("STEALTH_HUMANIZE", "0.7")
    cfg = BrowserConfig.from_env()
    assert cfg.humanize == pytest.approx(0.7)


def test_from_env_humanize_bool(monkeypatch):
    monkeypatch.setenv("STEALTH_HUMANIZE", "true")
    cfg = BrowserConfig.from_env()
    assert cfg.humanize is True


def test_from_env_proxy(monkeypatch):
    monkeypatch.setenv("STEALTH_PROXY_SERVER", "http://proxy:8080")
    monkeypatch.setenv("STEALTH_PROXY_USERNAME", "user")
    monkeypatch.setenv("STEALTH_PROXY_PASSWORD", "pass")
    cfg = BrowserConfig.from_env()
    assert cfg.proxy == {"server": "http://proxy:8080", "username": "user", "password": "pass"}


def test_from_env_no_proxy_without_env(monkeypatch):
    monkeypatch.delenv("STEALTH_PROXY_SERVER", raising=False)
    cfg = BrowserConfig.from_env()
    assert cfg.proxy is None


def test_typing_defaults():
    cfg = BrowserConfig()
    assert cfg.typing_cps_mean > 0
    assert cfg.typing_hesitation_prob >= 0
