# Security Architecture & Boundary Isolation

**Project:** `CSA-Obsidian` (Automation & Model Context Protocol Engine)  
**Security Principles:** Local Sandbox Isolation, Zero Credential Persistence, Anti-Abuse Controls

---

## 1. Architectural Overview

`CSA-Obsidian` provides controlled browser automation and data extraction tools exposed via the Model Context Protocol (MCP). Because browser automation interfaces can interact with dynamic web targets, the architecture implements strict defensive boundaries:

```
[ LLM Agent / MCP Client ]
         │ (JSON-RPC over stdio)
         ▼
[ MCP Server Layer (mcp_server/server.py) ]
         │
         ├──► Parameter Validation & Type Guards
         │
         ├──► Request Interception & Header Sanitization (stealth_browser/intercept.py)
         │
         └──► Isolated Browser Sandbox (stealth_browser/browser.py)
```

---

## 2. Defensive Controls & Safe Operating Principles

1. **Ephemeral Profile Execution:**
   - Automation runs inside dedicated temporary directories or explicitly declared test profiles.
   - Session tokens, authentication cookies, and profile caches are strictly separated from user production directories.

2. **Automated Secret Filtering & Secret Scrubbing:**
   - All network interception hooks scrub sensitive `Authorization`, `Cookie`, and custom token headers before telemetry serialization.
   - Staged data extraction strips inline credentials to prevent prompt injection and data leakage.

3. **Strict Local Testing Scope:**
   - Tools are architected exclusively for authorized local evaluation, accessibility auditing, and web performance benchmarking on maintainer-controlled domains.
   - The repository maintains an active `SECURITY.md` establishing non-disclosure and private security reporting channels.
