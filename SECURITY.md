# Security Policy

## Supported scope

This project is intended for controlled browser automation, QA, accessibility,
and agent evaluation. Tests must use accounts, profiles, and systems owned by
the tester or covered by explicit authorization.

## Sensitive artifacts

Never commit browser profiles, cookies, session exports, copied browser
databases, proxy credentials, or API tokens. Use redacted fixtures in tests and
bug reports. If any session artifact is exposed, remove it from the working tree
and history where appropriate, revoke the affected sessions, and rotate related
credentials.

## Reporting

Do not put credentials, session material, or exploit details in a public issue.
Use GitHub private vulnerability reporting when available. Otherwise, contact
the maintainer through the LinkedIn profile linked from
[skuzu7](https://github.com/skuzu7).

Include the affected component, a minimal redacted reproduction, the expected
security boundary, and the observed impact. Reports and proposed actions are
manually reviewed before changes are applied.

## Prohibited use

Do not use browser fingerprint modification, proxies, timing simulation, or MCP browser control to bypass CAPTCHAs, anti-bot controls, rate limits, access restrictions, account protections, or a site's terms of service. Do not collect, decrypt, export, or reuse cookies, CSRF tokens, or other authentication material from third-party accounts. The Binance-specific token-capture task and CLI command have been removed. Do not reintroduce service-specific session-token capture.

## Known sensitive capabilities

The MCP server can execute JavaScript in the active page and save/load browser sessions. Its cookie-inspection tool redacts cookie values, and request interception exposes only allowlisted protocol metadata while redacting unknown/custom header values. Named session paths are validated; POSIX session files use mode 0600. Direct Python APIs, arbitrary page JavaScript, persistent profiles, and Windows ACLs remain privileged surfaces. Treat the project as a local automation process, not a sandbox or a complete secret-redaction boundary. Use synthetic accounts, keep it off untrusted networks, and do not connect personal or production browser profiles to an LLM-connected session.
