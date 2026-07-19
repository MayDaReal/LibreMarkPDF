# Governance

LibreMark PDF currently uses lightweight maintainer governance. The repository
owner appoints maintainers, controls releases and credentials, and makes final
human decisions on compatibility, unsafe modes, signing expenditure, supported
platforms, and identity.

Maintainers integrate changes against `docs/VALIDATION.md`,
`docs/RELEASE.md`, and `docs/PLATFORM_SUPPORT.md`. Technical decisions with
compatibility, security, renderer, or distribution impact are recorded in a
focused decision document when needed. The integrator reviews evidence but
does not rewrite historical evidence.

Routine changes use pull-request review. When maintainers disagree, they record
alternatives, evidence, risks, and the accountable decision owner. No maintainer
may silently weaken a validation criterion, advertise an unvalidated platform, or merge a
renderer/default-style change without its required evidence.
