# Security Architecture & Data-Handling Boundaries

**Project:** CSA-Obsidian (browser automation and MCP control surface)  
**Status:** descriptive security documentation, not a certification or claim of sandbox isolation.  
**Last reviewed:** 2026-11-14

## 1. Important security statement

This application can control a browser session and can access sensitive browser state. It is **not a security sandbox** and does not automatically make a target, account, cookie, request header, or page safe to expose to an LLM.

Use only systems and accounts that the operator owns or is explicitly authorized to test. Do not use the fingerprint-modification, proxy, timing-simulation, or browser-control features to bypass anti-bot controls, CAPTCHAs, rate limits, access restrictions, account protections, or a site's terms.

## 2. Browser and MCP trust boundary

The MCP server exposes browser navigation, interaction, screenshots, page text, cookie access, JavaScript evaluation, and session save/load operations. In particular:

- `browser_open` accepts a caller-supplied URL; the generic browser interface does not enforce a repository-wide host allowlist.
- `browser_evaluate` executes caller-supplied JavaScript in the active page context.
- `browser_get_cookies` returns cookies from the active browser context.
- Session save/load functions can read and write cookie and storage state.
- The MCP server is an automation interface, not an OS sandbox, network egress filter, or complete authorization policy engine. Named session paths reject traversal and absolute names.
- `browser_get_cookies` returns cookie metadata with each cookie `value` replaced by `[REDACTED]`. Direct Python APIs and arbitrary page JavaScript remain privileged surfaces.

An MCP client or model must not be treated as a trusted authorization authority. The operator must independently constrain the target, profile, account, permitted actions, and data exposed to the client.

## 3. Request interception and sensitive headers

`RequestInterceptor` stores matching request URLs, methods, and selected header names in a bounded in-memory deque. It exposes values only for a small allowlist of ordinary protocol metadata (for example `content-type` and `user-agent`). All unknown/custom headers and known sensitive headers are replaced with `[REDACTED]`; `wait_for_header` rejects names outside the allowlist. Captured URLs are reduced to scheme and host; path, query, fragment, and URL user-info are omitted. Tests cover authorization, cookies, API keys, CSRF headers, and custom trace/token headers.

The service-specific Binance CSRF-token task, CLI command, and Python example have been removed. There is no service-specific token-capture integration in the current CLI.

## 4. Cookies, sessions, and storage persistence

The project supports reading and persisting browser state. These behaviors must not be described as “zero credential persistence”:

- The browser context can expose cookies to the application.
- `stealth_browser/session.py` writes cookie dictionaries to JSON with owner-only mode `0600` on POSIX, including when an existing file's permissions need tightening. It uses `O_NOFOLLOW` where supported. Windows mode bits are not an ACL; Windows directory permissions still need separate review.
- Session storage helpers read and write localStorage and sessionStorage values for a supplied origin.
- Persistent browser profiles may retain authenticated state between runs.
- `chrome_cookies.py` can decrypt cookies from the operator's own Chrome profile. Its default path keeps values in memory; an explicit export path is required for file output.
- The dedicated Chrome export helper uses exclusive creation and requests mode 0600 on POSIX. On Windows, the containing directory's ACL determines access and must be checked separately.

A cookie or session export can function as a bearer credential. Prefer synthetic test accounts and short-lived sessions. Store any explicitly authorized export outside synced/shared folders, restrict filesystem access, never commit it, and revoke the session if exposure is suspected.

## 5. Fingerprint modification and input simulation

Camoufox fingerprint modification, automation-flag changes, WebRTC controls, proxy configuration, and randomized input timing are dual-use capabilities. They may change how a site observes the browser; they do not grant permission to access the site or evade its controls.

Permitted purpose: controlled browser compatibility, QA, accessibility, and evaluation on owned or explicitly authorized systems. Prohibited purpose: bypassing access controls, CAPTCHAs, bot defenses, rate limits, identity checks, account restrictions, or provider terms.

## 6. Repository and CI controls

- Browser profiles and known cookie/session artifacts are excluded by `.gitignore`.
- The Chrome cookie export path is explicit and defaults to memory-only behavior.
- CI exercises the export policy and Python tests; Linux CI does **not** validate live Windows Chrome decryption or Windows ACL behavior.
- A passing test suite does not establish that the MCP server is isolated from the network, that all headers are redacted, or that production credentials are protected.

## 7. Required handling rules

1. Use synthetic accounts and data wherever possible.
2. Do not load personal or production browser profiles into an LLM-connected MCP session.
3. Never capture, export, or reuse credentials, cookies, CSRF tokens, or session material belonging to another person or service.
4. The Binance-specific token-capture task and CLI command have been removed; do not reintroduce service-specific session-token capture.
5. Do not expose the browser MCP server to untrusted clients or remote networks.
6. Do not claim sandboxing, automatic secret redaction, or zero credential persistence unless those controls are implemented and tested.

## 8. Remaining engineering work

- Add an explicit host allowlist and per-tool authorization policy before using the MCP server with untrusted agent plans.
- Review Windows ACLs for the profiles and session directories; POSIX mode bits do not enforce Windows access control.
- Consider a separate policy for direct Python cookie access and arbitrary page JavaScript.
- Have an independent reviewer inspect the resulting code and threat model.
- Have an independent reviewer inspect the resulting code and threat model.

**Scope:** this document does not authorize testing of any third-party system. See [SECURITY.md](../SECURITY.md) for reporting and use restrictions.
