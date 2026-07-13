# Gate G1 execution board

Date: 2026-07-13
Integrator: repository integration owner
Working model: shared workspace, one writer (integrator); specialists provided
read-only evidence and review.

| Work | Owner | State | Owned files/evidence | Next dependency |
| --- | --- | --- | --- | --- |
| SPIKE-REN-001..007, SPIKE-PKG-001..002 | renderer/package-spike owner | partial/blocked | `spikes/g1/`, `G1_RENDERER_SPIKE_REPORT.md` | native Windows + second-OS font/parity and package measurements |
| QAS-001..010 | quality/supply-chain owner | partial/review | `pyproject.toml`, `requirements/`, workflows, hygiene tool/tests | clean Python 3.9 install, hosted CI/scanners, installed-wheel resource decision |
| OSS-001..008 | community/documentation owner | review | community health files, templates, sync checklist, notices plan | maintainer/private-report settings review |
| BRD-001..005 | identity-research owner | research partial | `G1_IDENTITY_RESEARCH.md` only | authoritative registry/legal checks; no identity change |
| Backlog and gate decision | integrator | active | `BACKLOG.md`, `G1_GATE_REPORT.md` | review all evidence against G1 acceptance |

No owner may begin Lot 2 from this board. Production renderer, default CSS,
fonts, margins, pagination, icons, GUI, CLI, skill, and approved identity remain
unchanged.
