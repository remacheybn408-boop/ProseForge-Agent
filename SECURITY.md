# Security Policy

## Supported Versions

The latest tagged release on `main` is supported. Older tags receive fixes
only for critical issues at the maintainers' discretion.

## Reporting a Vulnerability

Please do not open a public issue for security problems. Report privately via
GitHub Security Advisories ("Report a vulnerability" on the repository's
Security tab). A PGP key can be exchanged on request for sensitive details.

## Triage SLA

- Acknowledgement within **3 business days**.
- A fix or a written explanation within **30 days** of acknowledgement.

## Scope

In scope:

- Provider credential handling and secret redaction.
- MCP tool boundaries and the approval gate.
- Execution environment isolation.
- Secret redaction in observability and trajectory exports.
- Filesystem containment for `fs.*` tools.

Out of scope:

- Findings in the ProseForge engine itself (`$PROSEFORGE_ROOT`) — report those
  to that project.
- Denial of service from deliberately pathological local input.

See `docs/security/threat-model.md` for the trust boundaries this project
claims to enforce.
