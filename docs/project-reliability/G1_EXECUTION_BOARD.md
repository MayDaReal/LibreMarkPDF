# Gate G1 execution board

Date: 2026-07-14
Integrator: repository integration owner
Working model: shared workspace, one writer (integrator); specialists provided
read-only evidence and review.

| Work | Owner | State | Owned files/evidence | Next dependency |
| --- | --- | --- | --- | --- |
| SPIKE-REN-001..007, SPIKE-PKG-001..002 | renderer/package-spike owner | one external result pending | `spikes/g1/`, `G1_RENDERER_SPIKE_REPORT.md`, `G1_WINDOWS_NATIVE_EVIDENCE.md` | run prepared Windows visual bundle and compare with Linux evidence |
| QAS-001..010 | quality/supply-chain owner | G1 acceptance met; follow-ups owned | `pyproject.toml`, `requirements/`, workflows, hygiene tool/tests, native Windows lock report | installed-wheel layout in Lot 2; retain hosted workflow/settings evidence after publication |
| OSS-001..008 | community/documentation owner | review | community health files, templates, sync checklist, notices plan | maintainer/private-report settings review |
| BRD-001..005 | identity-research owner | research partial | `G1_IDENTITY_RESEARCH.md` only | authoritative registry/legal checks; no identity change |
| Backlog and gate decision | integrator | active | `BACKLOG.md`, `G1_GATE_REPORT.md` | Windows/Linux visual report and owner appearance approval |

No owner may begin Lot 2 from this board. Production renderer, default CSS,
fonts, margins, pagination, icons, GUI, CLI, skill, and approved identity remain
unchanged.
