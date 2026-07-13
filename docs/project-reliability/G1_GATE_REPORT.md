# Gate G1 integration decision

Decision date: 2026-07-13
Decision: **NOT PASSED — Lot 2 is not authorized**
Integrator: repository integration owner
Integration source HEAD: `b2c194d31d08a3e8befae15941db8c4a1f2d0060`
Audited continuity identifier: `89f27f26c961b5b2776928e26b1f168ed2c87550`

The frozen baseline was read and was not edited. Production core, GUI, CLI,
i18n, skill, default CSS, fonts, margins, pagination, icons, build scripts,
specification, and approved product identity are unchanged. Unrelated ignored
or untracked brand work was not staged, deleted, or incorporated.

## Acceptance decision

| G1 criterion | Decision | Evidence / blocker |
| --- | --- | --- |
| Renderer/browser, fonts, resources, thresholds, Windows format selected from measurements | fail | Python 3.9 renderer candidate and Linux safety probe exist; no native Windows + second-OS embedded-font/parity report or native artifact-format comparison |
| Clean reproducible install and pure tests; dependency roles distinct; no renderer drift | partial | clean CPython 3.12 install, 36 pure tests, exact constraints and Windows CPython 3.9 hash lock; no clean CPython 3.9/native Windows execution, hosted CI, or installed-wheel resource proof |
| Contributor/security policies actionable without private knowledge | pass | OSS-001..008 documents/templates exist and focused tests pass; hosted private-report setting remains administrator work but documented fallback exists |
| Locked target engine and font licenses recorded | partial | Playwright 1.60.0 / Chromium 1223 archive hash lock and candidate OFL sources recorded; exact font files/hashes and full script coverage not locked |
| Every unresolved architecture question has an owner | pass | renderer, Windows packaging, QAS, security/core, administrator, integrator, and human-owner responsibilities are named in linked reports |

Blocking dependencies are `SPIKE-REN-003`, `SPIKE-REN-007`,
`SPIKE-PKG-001`, completion of font locks under `SPIKE-REN-002`, clean Python
3.9/hosted evidence under QAS-001/003/004/007, and installed-wheel resource
handling. G1 may be reconsidered only after those artifacts are reviewed.

## Lot 1A task handoff

All Lot 1A files are owned by the renderer/package-spike lane:
`spikes/g1/` and `G1_RENDERER_SPIKE_REPORT.md`. Observable production behavior
before/after is unchanged.

| Task | State | Acceptance evidence | Unverified/risk and next dependency |
| --- | --- | --- | --- |
| SPIKE-REN-001 | review/partial | exact Python 3.9 candidate: Playwright 1.60.0, Chromium/headless-shell 148.0.7778.96 rev 1223, FFmpeg 1011; Windows wheel SHA-256 in lock | clean Python 3.9/native install and golden review |
| SPIKE-REN-002 | review/partial | Noto Sans, Mono, Symbols 2, Emoji candidates and authoritative OFL sources | pin exact binaries/commits/hashes, CJK/RTL coverage, size and appearance |
| SPIKE-REN-003 | blocked | none | native Windows and second-OS current-style renders with embedded candidates |
| SPIKE-REN-004 | review/partial | target-revision probe: embedded image width 121, zero local external attempts/responses; hostile URL aborted | full relative-path/traversal/symlink/type/size/CSS corpus and OS-offline run |
| SPIKE-REN-005 | review/partial | JavaScript disabled, script not executed, service workers blocked, literal safe fragment | trusted-HTML sanitizer and hostile malformed-HTML corpus owner |
| SPIKE-REN-006 | review/partial | domain-separated canonical profile/HTML fingerprints and asset hashes | repeat across two clean builds and finalize schema |
| SPIKE-REN-007 | blocked | ADR-002 thresholds retained unchanged | native page pairs, pinned SSIM implementation, page-level report |
| SPIKE-PKG-001 | blocked | ADR-007 fallback direction retained; one ignored PE artifact only | native one-file/onedir hashes, Defender, timing, cleanup, concurrency, paths |
| SPIKE-PKG-002 | review/partial | full-browser/headless-shell compressed payload quantified; launch uses shell | rebuild `--only-shell` on Windows and run exact-candidate smoke tests |

## Lot 1B task handoff

Owned files are `pyproject.toml`, `requirements.txt`, `requirements/`, quality
and security workflows, Dependabot, `.gitignore`, `.gitattributes`, the hygiene
tool, and focused quality tests. Before, dependency lower bounds mixed runtime
and build roles and no repository automation/metadata existed. After, new
metadata separates roles and candidate resolution is exact and testable. The
legacy production build input remains unchanged until the missing renderer and
native review; production rendering is unchanged.

| Task | State | Acceptance evidence | Unverified/risk and next dependency |
| --- | --- | --- | --- |
| QAS-001 | review/partial | Python >=3.9 metadata, dynamic version and console entry install editably | ordinary wheel omits compatible top-level runtime resource layout; decide with core/package owners |
| QAS-002 | accepted | runtime, GUI, build, test, docs groups and input files | keep synchronized with specs/build scripts |
| QAS-003 | review/partial | exact constraints and hashed Windows x64 CPython 3.9 archive set | native `--require-hashes` install; add locks only for active lanes |
| QAS-004 | review/partial | clean CPython 3.12 pure run and Python 3.9/3.12 workflow | hosted Python 3.9 job has not executed |
| QAS-005 | accepted | Ruff syntax/undefined-name gate and compileall exit 0 | expand only with evidence; no mass formatting |
| QAS-006 | accepted | 31% measured branch coverage by module; 30% floor | GUI/dispatch coverage is zero; floor must rise with tests |
| QAS-007 | review/partial | CodeQL and dependency review workflows; admin checklist | hosted execution, secret scanning/push protection and branch settings |
| QAS-008 | accepted | weekly Dependabot; renderer dependencies excluded from ordinary group | renderer updates require manual lock/manifest/golden review |
| QAS-009 | accepted | generated/local paths ignored; binary/line-ending attributes preserved | none observed |
| QAS-010 | accepted | reusable source-manifest hygiene tool and workflow | hosted archive job unexecuted; release artifacts require later SBOM/provenance gate |

## Lot 1C task handoff

Owned files are the eight root community documents, six issue forms, PR
template, documentation checklist, and community tests. Before, these channels
and policies did not exist. After, contributors, security reporters,
translators, packagers, rendering reporters, and future theme authors have
actionable workflows without any supported-release claim.

| Task | State | Acceptance evidence | Unverified/risk and next dependency |
| --- | --- | --- | --- |
| OSS-001 | accepted | contributor setup, tests, review, translation and theme-proposal rules | theme package workflow waits for Lot 3C |
| OSS-002 | accepted | supported-version limits, private advisory route, safe fallback and response target | administrator must enable private reporting |
| OSS-003 | accepted | conduct, support and governance policies | repository owner reviews enforcement contacts |
| OSS-004 | accepted | bug, feature, packaging, rendering, translation, theme and PR templates | hosted labels/forms unverified |
| OSS-005 | accepted | changelog and SemVer policy distinguish pre-release/native claims | populate only with actual changes |
| OSS-006 | accepted | gate roadmap without dates | update only from accepted backlog state |
| OSS-007 | accepted | five-contract documentation sync checklist plus EN/FR/i18n checks | apply on later user-visible changes |
| OSS-008 | accepted | verifiable notice-generation/inventory plan; no blanket license claim | actual notices/SBOM wait for exact release payload |

## Lot 1D research handoff

Owned file is `G1_IDENTITY_RESEARCH.md` only. No code, documentation identity,
logo, asset, or `docs/brand/` work changed. ADR-008 remains authoritative.

| Task | State | Acceptance evidence | Unverified/risk and next dependency |
| --- | --- | --- | --- |
| BRD-001 | accepted research | eight candidates scored on six stated criteria | dated qualitative evidence, not clearance |
| BRD-002 | accepted research | historical shortlist includes LibreMark PDF, FolioDown PDF, SlateLeaf PDF | ADR-008 separately records owner decision |
| BRD-003 | active/partial | primary registry/index sources and collision leads recorded | authenticated package/domain/social and additional Linux registries |
| BRD-004 | active/partial | official INPI/EUIPO/USPTO/WIPO methods and caveat recorded | reproducible searches and professional legal review; LibreMark.org is a material lead |
| BRD-005 | active/research-only | three conceptual directions assessed at 16/32/128/512 | alternatives not generated; no 512 PNG; no authorization to alter accepted master |

## Commands and evidence

Unless stated, commands ran from `/shared/repos/LibreMarkPDF` on Linux x86_64.

| Command | Exit | Result |
| --- | ---: | --- |
| `git status --short --branch` (initial) | 0 | clean `main`; baseline remained ignored; no brand path entered scope |
| `python3 -c "import markdown"` | 1 | system CPython 3.12 lacks `markdown`, as expected |
| target `pip download` with Markdown 3.10.2 / Playwright 1.61.0 for CPython 3.9 | 1 | both rejected by `Requires-Python >=3.10` |
| target `pip download` with Markdown 3.9 / Playwright 1.60.0 and explicit Python 3.9/Windows marker dependencies | 0 | 19 archives, 66,858,086 bytes, hashes captured in release-candidate lock |
| hash-enforced pip install dry run targeting Windows x64 CPython 3.9 | 0 | all 19 locked archives resolved; no native execution claim |
| `python3 -m venv /tmp/libremark-g1-clean` and constrained editable `.[test]` install | 0 | clean CPython 3.12 Linux environment resolved exact candidate versions |
| final browser-free coverage command | 0 | 36 tests, OK; 31% total branch-aware coverage |
| Python `ast.parse(..., feature_version=(3, 9))` over 14 source/test/tool/probe files | 0 | Python 3.9 grammar accepted |
| `ruff check libremark_pdf tests tools spikes` | 0 | all focused checks passed |
| `python tools/check_source_hygiene.py` | 0 | proposed source manifest passed |
| target-revision `spikes/g1/renderer_probe.py` | 0 | Chromium 148.0.7778.96; local zero requests; hostile request aborted; script disabled |
| `PLAYWRIGHT_BROWSERS_PATH=/tmp/libremark-playwright-1223 ... unittest discover -s tests -v` | 0 | 39 tests, OK; required launch ran outside container syscall sandbox |
| `/tmp/libremark-g1-clean/bin/python -m libremark_pdf convert --help` | 0 | CLI help emitted normally |
| installed `/tmp/libremark-g1-clean/bin/libremark-pdf convert --help` | 0 | console entry point works in editable clean environment |
| temporary `pip wheel --no-deps --wheel-dir /tmp/libremark-g1-wheel .` | 0 | metadata wheel built; manifest confirms top-level runtime resources are absent, so QAS-001 stays partial |
| target-revision README JSON conversion | 0 | valid JSON, status `ok`, no reported error; 3-page PDF in `/tmp` |
| PyYAML parse of all `.github` YAML | 0 | 10 workflow/config/template files parsed |
| `file`, `stat`, `sha256sum dist/LibreMarkPDF.exe` | 0 | ignored PE32+ GUI x86-64 artifact observed only; not official evidence |
| `git diff --check` (pre-final review) | 0 after removing one trailing blank line | no whitespace errors |

Temporary evidence, never source-controlled:

- `/tmp/libremark-g1-renderer-probe.json`: 1,105 bytes, SHA-256
  `61fb72c14818eca9e4466d2050c0a6d89cf3af08ce958fee14d28b7567742dad`;
- `/tmp/libremark-g1-readme-1223.pdf`: 63,851 bytes, 3 pages, SHA-256
  `6ec50107de90ca107a7b40ac0635ec6559775c15b3f765c0e721bd188632fced`;
- observed ignored `dist/LibreMarkPDF.exe`: 373,253,524 bytes, SHA-256
  `a153272f7a6ce142c28817a0967bcf1ab107941092fe2cb43715472291d74f29`.

The Windows executable's origin environment and checklist are not tied to this
hash, so no Windows task is accepted from it. macOS, native Windows, Python 3.9,
hosted GitHub settings/workflows, cross-OS parity, font rendering, antivirus,
signing, offline native artifacts, and installed-wheel conversion remain
unverified.
