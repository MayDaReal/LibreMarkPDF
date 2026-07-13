# Governance

LibreMark PDF currently uses lightweight maintainer governance. The repository
owner appoints maintainers, controls releases and credentials, and makes final
human decisions on compatibility, unsafe modes, signing expenditure, supported
platforms, and identity.

Maintainers integrate changes in the gate order recorded in
`docs/project-reliability/BACKLOG.md`. Technical decisions with compatibility,
security, renderer, or distribution impact are recorded as ADRs. The integrator
reviews evidence but does not rewrite the frozen baseline. A high-reliability
release requires an independent final audit by someone who did not implement
the audited changes.

Routine changes use pull-request review. When maintainers disagree, they record
alternatives, evidence, risks, and the accountable decision owner. No maintainer
may silently weaken a gate, advertise an unvalidated platform, or merge a
renderer/default-style change without its required evidence.
