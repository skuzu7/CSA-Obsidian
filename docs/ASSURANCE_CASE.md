# Defensive browser automation: assurance case

**Scope:** first-party or expressly authorized browser QA, accessibility and LLM-agent testing. **Not** an accredited pentest product, a production sandbox, a trusted government system or evidence of CVP access.

## Security objective

Reduce accidental unapproved network access and exposure of persisted browser sessions during **local** evaluation. This is not a complete security boundary against a compromised process, arbitrary page JavaScript or browser vulnerabilities.

| Claim | Enforcement/verification | Known limits |
| --- | --- | --- |
| Network requests default to deny | `BrowserConfig.allowed_hosts=()`; `BrowserManager._route_request`; `tests/test_browser_policy.py` | Interception is not an operating-system firewall, DNS/IP allowlist or network egress proxy |
| Authorized hosts and ports must match | `stealth_browser/policy.py`; `tests/test_policy.py` | An allowlisted hostname can still be unsafe; do not include client infrastructure without authorization |
| Cookie values are redacted from MCP tools | Existing cookie/session tests and `SECURITY.md` | Browser memory, profiles, direct Python APIs and arbitrary page scripts remain privileged |
| Sensitive browser state is not newly committed | `scripts/check_sensitive_paths.py`; `tests/test_sensitive_path_guard.py`; automated CI | Path-only audit cannot detect embedded secrets, past Git history or renamed artifact values |
| Filesystem permissions receive regression coverage | `tests/test_file_security.py`; Windows ACL CI job | This checks library behavior, not the underlying workstation security posture |
| CI must be reproducible without real credentials | Synthetic fixtures, `pytest`, Ruff, GitHub Actions | Passing CI does not establish live model safety or third-party assurance |

## Operational rules for institutional evaluation

1. **Written authorization:** define owner, legal scope, exact authorized hosts and ports, permitted methods, time window, contact and emergency stop procedure. A wildcard is not a substitute for an explicit scope.
2. **Data minimization:** use synthetic accounts and disposable profiles. No production browser profile, cookies, third-party credentials, private communications or sensitive government data may enter an LLM-controlled browser session.
3. **Human control:** require review before privileged actions (authentication, account changes, access to sensitive data, export of artifacts). Tool success does not prove an action was authorized.
4. **Network isolation:** run the browser in a container/VM with a real egress policy. The HTTP(S) route guard is defense in depth only; control DNS rebinding, redirects, and native process egress separately.
5. **Secrets and incident handling:** store credentials in a managed vault, minimize retention, redact logs, revoke compromised sessions and report only through approved channels.
6. **Independent assurance:** seek code review, external tests and signed organizational policies before claiming operational readiness. Do not label the project government-certified or assert NIST/ISO compliance based on this file.

## Reproducible verification

```sh
python -m scripts.check_sensitive_paths
pytest -q tests/test_policy.py tests/test_browser_policy.py tests/test_sensitive_path_guard.py
```

Test reports substantiate the individual local invariants above. They cannot establish organization verification, government contracts, formal CVP Red Team / Specialized eligibility or model-provider approval.
