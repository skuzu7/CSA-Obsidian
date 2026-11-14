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
- The MCP server is an automation interface, not an OS sandbox, network egress filter, or authorization policy engine.

An MCP client or model must not be treated as a trusted authorization authority. The operator must independently constrain the target, profile, account, permitted actions, and data exposed to the client.

## 3. Request interception and sensitive headers

The current `RequestInterceptor` implementation stores matching request URLs, methods, and the **full request-header dictionary** in an in-memory deque (up to 500 records). It does not redact Cookie, Authorization, CSRF, or other sensitive headers automatically.

The Binance-specific `BinanceTokenTask` explicitly waits for and returns the `csrftoken` header (and retains matching request records). The CLI exposes this through `stealth-browser binance-tokens`.

Treat all captured header values as secrets. Do not run this integration against a real or funded account, do not forward captured values to an LLM, do not write them to logs or reports, and do not share them. The presence of this command is a sensitive legacy capability and should be reviewed for removal or replacement with a synthetic/test-only fixture.

## 4. Cookies, sessions, and storage persistence

The project supports reading and persisting browser state. These behaviors must not be described as “zero credential persistence”:

- The browser context can expose cookies to the application.
- `stealth_browser/session.py` writes cookie dictionaries to JSON with ordinary file writing; this function does not itself enforce restrictive permissions or exclusive file creation.
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
4. Do not run the Binance-specific token capture command against a real account; retire or redesign it as a test-only integration before recommending this project for security-sensitive use.
5. Do not expose the browser MCP server to untrusted clients or remote networks.
6. Do not claim sandboxing, automatic secret redaction, or zero credential persistence unless those controls are implemented and tested.

## 8. Remaining engineering work

- Remove or isolate the service-specific token-capture task behind a synthetic/test-only fixture.
- Add default redaction for sensitive request headers and tests proving raw values are not logged or serialized.
- Harden generic session exports with restrictive file permissions, exclusive creation, and platform-specific ACL guidance.
- Add an explicit host allowlist and per-tool authorization policy before using the MCP server with untrusted agent plans.
- Add tests for denied origins, sensitive-header redaction, storage export, and session file permissions.
- Have an independent reviewer inspect the resulting code and threat model.

**Scope:** this document does not authorize testing of any third-party system. See [SECURITY.md](../SECURITY.md) for reporting and use restrictions.
