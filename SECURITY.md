# Security Policy

## Supported Versions

AETHERIUM-GENESIS is currently maintained on the default branch. Security fixes are prioritized for:

- Latest commit on `main` (or current default branch)
- Tagged releases published after `v2.3.0`

Older snapshots, forks, and sandbox-only branches may not receive coordinated fixes.

## Reporting a Vulnerability

Please report vulnerabilities **privately** before public disclosure.

1. Open a private security report via the "Security" tab on the GitHub repository.
2. Include:
   - Affected component/path
   - Reproduction steps (PoC)
   - Impact assessment (data exposure, execution risk, governance bypass risk)
   - Suggested mitigation (if available)
3. Do not publish exploit details until a fix or mitigation is available.

## Response Targets

- Initial acknowledgement: within **72 hours**
- Triage decision: within **7 business days**
- Mitigation plan or patch timeline: as soon as impact is confirmed

## Security Scope Priorities

Highest-priority issues include:

- Governance bypass on high-impact execution paths
- Memory/audit tampering (Akashic/ledger integrity)
- AuthN/AuthZ flaws in control-plane APIs
- Remote code execution in vessel adapters or execution pipeline
- Correlation/provenance spoofing that breaks audit traceability

## Coordinated Disclosure

After fix deployment, maintainers may publish:

- Affected versions
- Technical root cause summary
- Mitigation or upgrade guidance
