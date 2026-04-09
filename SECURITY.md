# Security Policy

## Supported Versions

Security fixes are prioritized for:

- The current default branch (`main`)
- The most recent tagged release

Older snapshots and personal forks may not receive coordinated fixes.

## Reporting a Vulnerability

Please report vulnerabilities privately before any public disclosure.

1. Use the repository's GitHub **Security Advisory** workflow (preferred).
2. If unavailable, open a private maintainer contact channel and include:
   - Affected file(s)/component(s)
   - Reproduction steps / PoC
   - Impact assessment (confidentiality, integrity, availability)
   - Suggested remediation (if known)

Please do **not** post zero-day details in public issues.

## Response Targets

- Initial acknowledgement: within **72 hours**
- Triage outcome: within **7 business days**
- Patch or mitigation timeline: provided after triage

## Priority Areas

Highest-priority findings include:

- Governance bypass for high-impact actions
- AuthN/AuthZ flaws on control-plane APIs
- Memory or ledger tampering (Akashic continuity/integrity)
- Remote code execution in vessel adapters or execution pipeline
- Provenance/correlation spoofing that breaks auditability

## Disclosure Process

After fixes are deployed, maintainers may publish:

- Affected versions and scope
- Technical root cause summary
- Upgrade or mitigation guidance
