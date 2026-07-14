# Project reliability program

This directory contains the frozen audit reference and the execution package
for evolving LibreMark PDF into a high-reliability, local-first Markdown-to-PDF
product.

## Choose a reading path

This is an evidence directory, not a second contributor guide. Start with the
short path for your role and open detailed records only when the task requires
them:

| Role | Read in order | Result |
| --- | --- | --- |
| New contributor | repository `README.md` → `CONTRIBUTING.md` | Make a focused change without learning the whole program |
| Reliability implementer | `TARGET_ARCHITECTURE.md` → `BACKLOG.md` → assigned ADRs | Know the constraint, owner, and acceptance evidence |
| Integrator | `BACKLOG.md` → active ADRs → current gate evidence | Decide a gate from traceable records |
| Independent auditor | `BASELINE_AUDIT.md` → target architecture → gate reports | Re-score without changing the frozen baseline |

The table below identifies the single source of truth for each kind of
information. Reports summarize evidence; they do not replace the decision or
the command that produced it.

| Information | Source of truth |
| --- | --- |
| Historical score and findings | `BASELINE_AUDIT.md` (immutable, local historical input) |
| Target renderer, resources, and platforms | `TARGET_ARCHITECTURE.md` |
| Task state, owner, dependencies, and gate criteria | `BACKLOG.md` |
| Compatibility and security decisions | `ADR-002` through `ADR-008` |
| Closed G1 decision and command results | `archive/g1/README.md` and its indexed reports |
| File-level integrity of G1 evidence | manifests under `archive/g1/` |
| Current task assignment format | `AGENT_PROMPTS.md` |

Do not duplicate a decision in a new report. Update the owning ADR or active
backlog entry, then link the evidence from the gate report. When a gate closes,
move its working board, reports, prompts, and manifests into one immutable
`archive/<gate>/` directory; keep accepted ADRs and architecture active.

The original audit-to-gate reading order is:

1. [`BASELINE_AUDIT.md`](BASELINE_AUDIT.md) — immutable score and evidence
   captured on 2026-07-13 (**43/100**).
2. [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md) — renderer,
   deterministic-output, and native-distribution decision.
3. [`BACKLOG.md`](BACKLOG.md) — task IDs, parallel waves, dependencies, gates,
   and acceptance criteria.
4. [`AGENT_PROMPTS.md`](AGENT_PROMPTS.md) — compact assignment template for the
   active gate.

Closed G1 material is indexed in [`archive/g1/README.md`](archive/g1/README.md).
It is retained for auditability but is not part of the normal contributor
reading path.

The baseline document must not be edited to reflect future work. At the end of
the backlog, an independent auditor creates a separate dated final report using
the unchanged scoring breakdown.
