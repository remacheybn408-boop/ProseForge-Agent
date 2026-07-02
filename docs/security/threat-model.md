# Threat Model — Trust Boundaries

This page names the trust boundaries ProseForge Agent claims to enforce, so
security reviewers and `pf-agent doctor` checks have a shared reference.

## Principals

- **User / operator** — the trusted principal who runs `pf-agent`.
- **Untrusted content** — retrieved evidence, file text, attachments, chat
  input, and any tool output. Treated as data, never as instructions.
- **External services** — LLM providers, MCP servers, messaging platforms,
  execution backends. Reached only through injected clients/transports.

## Boundaries Enforced

1. **Permission ceiling** — `PermissionPolicy` authorizes each tool against a
   session ceiling (`read_only` → `system_write`); `system_write` needs an
   explicit confirmation. Untrusted content can only lower the ceiling, never
   raise it (`InjectionGuard`).
2. **Filesystem containment** — `fs.read/write/edit` resolve every path inside
   the workspace root; a path that escapes raises before any I/O.
3. **MCP boundary** — per-server `MCPPolicy` (filesystem/network/command
   allow-lists), an approval gate for risky tools, and a credentials boundary
   that builds the exact environment a server may receive.
4. **Secret redaction** — credentials and secrets are redacted before they
   reach logs, event-bus JSONL, telemetry exports, trajectory datasets,
   approval payloads, or publish/installer reports.
5. **Execution isolation** — command execution runs list-form argv only, after
   permission + approval + safety checks, inside the workspace.

## Known Non-Goals

- The ProseForge engine at `$PROSEFORGE_ROOT` is a separate trust domain.
- Contract-only transports (placeholder MCP stdio, dry-run execution backends,
  fake gateway adapters) are not production-hardened until a real transport is
  wired; see the README's "production-ready vs contract-only" section.
