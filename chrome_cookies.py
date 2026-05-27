"""Extract and decrypt all cookies from Chrome, export as Playwright-compatible JSON."""
from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CHROME_USER_DATA = Path.home() / "AppData/Local/Google/Chrome/User Data"
COOKIES_DB = CHROME_USER_DATA / "Default/Network/Cookies"
LOCAL_STATE = CHROME_USER_DATA / "Local State"


def _get_aes_key() -> bytes:
    import win32crypt  # noqa: PLC0415

    state = json.loads(LOCAL_STATE.read_text(encoding="utf-8"))
    encrypted_key = base64.b64decode(state["os_crypt"]["encrypted_key"])
    # Strip "DPAPI" prefix (5 bytes)
    encrypted_key = encrypted_key[5:]
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]


def _decrypt_value(encrypted: bytes, key: bytes) -> str:
    if not encrypted:
        return ""
    prefix = encrypted[:3]
    # v10 = DPAPI-protected AES key, v20 = app-bound encryption (Chrome 127+)
    if prefix in (b"v10", b"v20"):
        nonce = encrypted[3:15]
        ciphertext = encrypted[15:]
        try:
            return AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8", errors="replace")
        except Exception:
            return ""
    # Legacy DPAPI-only cookies
    try:
        import win32crypt  # noqa: PLC0415
        return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode("utf-8", errors="replace")
    except Exception:
        return ""


def _sameSite_map(val: int) -> str:
    return {-1: "None", 0: "None", 1: "Lax", 2: "Strict"}.get(val, "None")


def extract(output: Path | None = None) -> list[dict]:
    key = _get_aes_key()

    # Copy DB avoiding Chrome lock — open with shared read access
    tmp = Path(tempfile.mkdtemp()) / "Cookies"
    import ctypes
    import ctypes.wintypes as wt

    kernel32 = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x1
    FILE_SHARE_WRITE = 0x2
    FILE_SHARE_DELETE = 0x4
    OPEN_EXISTING = 3

    handle = kernel32.CreateFileW(
        str(COOKIES_DB), GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, 0, None,
    )
    if handle == -1:
        raise PermissionError(f"Não conseguiu abrir {COOKIES_DB}")

    size = COOKIES_DB.stat().st_size
    buf = ctypes.create_string_buffer(size)
    bytes_read = wt.DWORD(0)
    kernel32.ReadFile(handle, buf, size, ctypes.byref(bytes_read), None)
    kernel32.CloseHandle(handle)
    tmp.write_bytes(buf.raw[:bytes_read.value])

    conn = sqlite3.connect(str(tmp))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT host_key, name, path, encrypted_value, is_secure, is_httponly, "
        "samesite, expires_utc FROM cookies"
    ).fetchall()
    conn.close()
    tmp.unlink(missing_ok=True)

    cookies: list[dict] = []
    for r in rows:
        value = _decrypt_value(r["encrypted_value"], key)
        if not value:
            continue
        domain = r["host_key"]
        # Chrome stores epoch as microseconds since 1601-01-01; Playwright uses Unix epoch seconds
        expires_utc = r["expires_utc"]
        if expires_utc and expires_utc > 0:
            unix_ts = (expires_utc / 1_000_000) - 11644473600
        else:
            unix_ts = -1

        cookies.append({
            "name": r["name"],
            "value": value,
            "domain": domain,
            "path": r["path"],
            "expires": unix_ts,
            "httpOnly": bool(r["is_httponly"]),
            "secure": bool(r["is_secure"]),
            "sameSite": _sameSite_map(r["samesite"]),
        })

    dest = output or Path("chrome_cookies.json")
    dest.write_text(json.dumps(cookies, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exportados {len(cookies)} cookies -> {dest}")
    return cookies


if __name__ == "__main__":
    extract()
