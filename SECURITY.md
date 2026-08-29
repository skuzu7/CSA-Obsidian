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
