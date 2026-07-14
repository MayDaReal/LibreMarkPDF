# Gate G1 archive

Gate G1 was accepted on 2026-07-14 and closed by signed commit
`a8a30075d67276aeb5d33d2559c7fb93f290ba38` (`Close Gate G1`). This directory
contains its historical program state and evidence reports.

## Archive policy

- Files in this directory are historical records, not active instructions.
- Do not edit them to reflect later implementation or task state.
- Use the active [`../../BACKLOG.md`](../../BACKLOG.md) and
  [`../../AGENT_PROMPTS.md`](../../AGENT_PROMPTS.md) for current work.
- Accepted ADRs and [`../../TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md)
  remain active outside the archive.
- Relative links and paths inside archived files reflect their original
  repository location. To reproduce them exactly, inspect the G1 closure commit.

For current navigation, use the accepted
[`ADR-002`](../../ADR-002-VISUAL-EQUIVALENCE.md),
[`ADR-003`](../../ADR-003-PLATFORM-POLICY.md),
[`ADR-004`](../../ADR-004-MARKDOWN-TRUST-MODEL.md),
[`ADR-005`](../../ADR-005-OUTPUT-INTEGRITY-AND-FEEDBACK.md),
[`ADR-006`](../../ADR-006-RENDER-DATE.md),
[`ADR-007`](../../ADR-007-WINDOWS-ARTIFACT-FORMAT.md), and
[`ADR-008`](../../ADR-008-PRODUCT-IDENTITY.md) at their active locations.

## Contents

| Record | Purpose |
| --- | --- |
| [`G1_GATE_REPORT.md`](G1_GATE_REPORT.md) | Integrator decision, task handoff, commands, risks, and next dependencies |
| [`G1_EXECUTION_BOARD.md`](G1_EXECUTION_BOARD.md) | Final G1 ownership and state snapshot |
| [`G1_RENDERER_SPIKE_REPORT.md`](G1_RENDERER_SPIKE_REPORT.md) | Renderer, font, resource, visual, and Windows format selection evidence |
| [`G1_QAS_EVIDENCE.md`](G1_QAS_EVIDENCE.md) | Dependency, clean-install, CI, quality, and supply-chain evidence |
| [`G1_WINDOWS_NATIVE_EVIDENCE.md`](G1_WINDOWS_NATIVE_EVIDENCE.md) | Native Windows commands, artifacts, measurements, limitations, and follow-ups |
| [`G1_IDENTITY_RESEARCH.md`](G1_IDENTITY_RESEARCH.md) | Historical research; ADR-008 remains authoritative |
| [`BACKLOG.md`](BACKLOG.md) | Complete program backlog as it stood when G1 closed |
| [`AGENT_PROMPTS.md`](AGENT_PROMPTS.md) | Full prompts used to bootstrap and execute the original waves |
| `G1_EVIDENCE_MANIFEST.sha256` | Hash manifest recorded at integration closure |
| `G1_WINDOWS_EVIDENCE_MANIFEST.sha256` | Hashes for the retained native Windows evidence package |

The G1 manifest records repository-relative paths from the closure commit; it
is intentionally not rewritten after this archival move. Git history and the
signed closure commit preserve the exact tree it describes.

The final supplied Windows visual archive is external to source control:
`LibreMark G1 Windows visual flagged 5264143.zip`, 1,631,037 bytes, SHA-256
`8fae9aa3e3e7044316c9aa5f5ddffef8c8e510eaf0b95534ff7817aa0a00ee1d`.
It must remain in durable evidence storage; it is not a product artifact.
