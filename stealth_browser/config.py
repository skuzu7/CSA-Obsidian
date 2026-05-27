from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_path = _PROJECT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()


@dataclass
class BrowserConfig:
    profile_dir: Path = field(default_factory=lambda: _PROJECT_DIR / "profiles" / "default")
    locale: list[str] = field(default_factory=lambda: ["pt-BR", "pt"])
    window: tuple[int, int] = (1366, 768)
    os_target: str = "windows"
    headless: bool = False
    block_webrtc: bool = True
    proxy: dict[str, str] | None = None
    humanize: bool | float = True
    enable_cache: bool = False
    import_chrome_cookies: bool = False
    chrome_cookie_ttl: int = 3600

    typing_cps_mean: float = 4.5
    typing_cps_std: float = 1.2
    typing_word_pause_mean: float = 0.15
    typing_word_pause_std: float = 0.08
    typing_hesitation_prob: float = 0.08
    scroll_steps_min: int = 3
    scroll_steps_max: int = 6
    click_hover_mean: float = 0.3
    click_hover_std: float = 0.1

    @classmethod
    def from_env(cls) -> BrowserConfig:
        _load_dotenv()
        kwargs: dict = {}
        if v := os.environ.get("STEALTH_PROFILE_DIR"):
            kwargs["profile_dir"] = Path(v) if Path(v).is_absolute() else _PROJECT_DIR / v
        if v := os.environ.get("STEALTH_LOCALE"):
            kwargs["locale"] = [x.strip() for x in v.split(",")]
        if v := os.environ.get("STEALTH_WINDOW"):
            parts = v.split(",")
            kwargs["window"] = (int(parts[0].strip()), int(parts[1].strip()))
        if v := os.environ.get("STEALTH_OS_TARGET"):
            kwargs["os_target"] = v
        if v := os.environ.get("STEALTH_HEADLESS"):
            kwargs["headless"] = v.lower() in ("true", "1", "yes")
        if v := os.environ.get("STEALTH_BLOCK_WEBRTC"):
            kwargs["block_webrtc"] = v.lower() in ("true", "1", "yes")
        if v := os.environ.get("STEALTH_HUMANIZE"):
            kwargs["humanize"] = v.lower() in ("true", "1", "yes") if v.lower() in ("true", "false", "1", "0", "yes", "no") else float(v)
        if v := os.environ.get("STEALTH_PROXY_SERVER"):
            kwargs["proxy"] = {"server": v}
            if u := os.environ.get("STEALTH_PROXY_USERNAME"):
                kwargs["proxy"]["username"] = u
            if p := os.environ.get("STEALTH_PROXY_PASSWORD"):
                kwargs["proxy"]["password"] = p
        if v := os.environ.get("STEALTH_IMPORT_CHROME_COOKIES"):
            kwargs["import_chrome_cookies"] = v.lower() in ("true", "1", "yes")
        if v := os.environ.get("STEALTH_CHROME_COOKIE_TTL"):
            kwargs["chrome_cookie_ttl"] = int(v)
        return cls(**kwargs)
