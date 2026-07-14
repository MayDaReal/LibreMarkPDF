# Gate G1 package and quality evidence

Status: **G1 acceptance supported; wheel and hosted-setting follow-ups remain**
Evidence date: 2026-07-14
Environment: Ubuntu 24.04.4, Linux 6.17 x86_64, system CPython 3.12.3
Source HEAD before changes: `b2c194d31d08a3e8befae15941db8c4a1f2d0060`

## Dependency decision

`pyproject.toml` is the metadata source and derives version `1.0.0` from
`libremark_pdf.__version__`. Runtime, GUI/preview, build, test, and documentation
groups are distinct. `requirements/constraints.txt` fixes cross-platform
development resolution. `requirements/locks/windows-x64-py39.txt` records one
hash for every archive in the resolved Windows x64 CPython 3.9 build/test set.

Target resolution rejected the installed-environment candidates:

```text
Markdown==3.10.2: Requires-Python >=3.10
playwright==1.61.0: Requires-Python >=3.10
```

Resolution succeeded after selecting Markdown `3.9`, Playwright `1.60.0`,
Pillow `11.3.0`, and compatible transitives. The Playwright wheel manifest fixes
Chromium/headless shell `148.0.7778.96` revision `1223` and FFmpeg `1011`.
This prevents silent renderer drift. A native Windows CPython 3.9 environment
subsequently installed the complete 19-archive lock with `--require-hashes`,
ran 36 then-current pure tests and 39 then-current complete target-browser
tests, and launched the exact revision-1223 payload. The linked native report
records commands, hashes, environment, and limitations.

The production onefile build script and its legacy `requirements.txt` input
were not changed to consume the candidate lock, because that would change the
effective renderer before golden review. The diagnostic portable spike instead
requires the pre-installed lock and pre-staged browser and performs no download.
Production build migration is an owned implementation dependency, not a claim
that the current legacy build is reproducible.

## Clean Linux development check

A new `/tmp/libremark-g1-clean` CPython 3.12 virtual environment installed the
checkout with:

```bash
python3 -m venv /tmp/libremark-g1-clean
/tmp/libremark-g1-clean/bin/python -m pip install \
  -c requirements/constraints.txt -e '.[test]'
```

Exit `0`. The build-isolation requirement is pinned to setuptools `82.0.1`.
This proves metadata resolution on this Linux/Python combination. The separate
native Windows evidence proves the active Python 3.9 release-lane lock; neither
result is an installed-wheel or official frozen-artifact claim.

A hash-enforced pip dry run targeting Windows x64 CPython 3.9 resolved all 19
locked archives and exited `0`. PyInstaller's Windows-only `pefile` and
`pywin32-ctypes` plus Python 3.9 `importlib-metadata`/`zipp` requirements were
added explicitly after wheel-metadata review. The native installation later
resolved the same lock with exit `0`.

After the G1 visual-spike tests were added, the clean target-version Linux
command ran 45 browser-free tests and exited `0`. Branch-aware coverage remained
31% overall (CLI 79%, core 64%, i18n 36%, GUI 0%, dispatch 0%), preserving the
30% initial non-regression floor. Ruff's focused syntax/undefined-name rules,
`compileall`, and the 106-path hygiene check passed. The complete target-browser
suite ran 48 tests and exited `0` with Chromium revision 1223.

System `python3 -m unittest discover -s tests -v` remains expected to exit `1`
because system Python lacks `markdown`; no test was weakened to hide that clean
dependency failure. The ignored `venv-linux` is historical evidence, not the
new clean environment.

## CI and supply-chain configuration

The quality workflow defines Python 3.9/3.12 pure jobs, a pinned-renderer browser
job, coverage artifacts, source-hygiene checks, and the browser-free G1 spike
tests. Security configuration adds CodeQL and dependency review. Dependabot updates ordinary Python and action
dependencies but excludes Playwright, Markdown, and PDFium from automatic
renderer updates. `.github/SECURITY_SETTINGS.md` records hosted settings that an
administrator must enable: private vulnerability reporting, secret scanning
with push protection, alerts, and branch protection.

The source-hygiene tool rejects virtual environments, caches, browser payloads,
builds, distributions, executables, and PDFs. `.gitignore` retains the immutable
local baseline exclusion. `.gitattributes` preserves Windows batch endings and
binary resources.

## Task states

| Task | State | Evidence / limitation |
| --- | --- | --- |
| QAS-001 | partial | metadata/version/entry point exist; ordinary installed-wheel resource lookup is not accepted |
| QAS-002 | accepted | runtime, GUI, build, test, docs groups are distinct |
| QAS-003 | accepted for active lane | Windows CPython 3.9 hash lock installed natively with `--require-hashes`; renderer/browser updates remain manual |
| QAS-004 | accepted for G1 | workflow exists; clean Linux 3.12 and native Windows 3.9 pure runs pass; hosted execution remains unclaimed |
| QAS-005 | accepted locally | focused Ruff and compile checks exit 0 |
| QAS-006 | accepted locally | per-module report and measured 30% floor recorded |
| QAS-007 | accepted as configuration | CodeQL/dependency review and administrator checklist exist; hosted execution and settings remain unclaimed |
| QAS-008 | accepted as configuration | controlled renderer exclusions and weekly updates recorded |
| QAS-009 | accepted | ignore/attribute rules cover generated/local/binary paths |
| QAS-010 | accepted locally | reusable hygiene check exits 0; hosted archive job unexecuted |

`resource_path()` expects top-level source/PyInstaller resources. A normal wheel
cannot be claimed runtime-complete until a coordinated resource-layout decision
and installed-wheel conversion test occur. A temporary wheel build exited 0
(18,502 bytes, SHA-256
`211ca5e9422430c5b067fcc5b72db8cd960d600fd0b238bd7ec8c2343cbfc3d0`),
and its 12-member manifest confirmed that `style.css`, icons, and assets are not
included. That work may touch production core and therefore was not smuggled
into G1.

## G1 acceptance assessment

| Acceptance requirement | Decision | Evidence / limitation |
| --- | --- | --- |
| A clean checkout can install and run pure tests | pass | clean Linux constrained editable install and native Windows hash-locked Python 3.9 install both passed; ordinary wheel conversion remains unclaimed |
| Runtime and build dependencies are distinguishable | pass | metadata and input files separate runtime, GUI, build, test, and documentation roles |
| Dependency resolution is repeatable and renderer updates cannot drift silently | pass | active Windows lane has archive hashes; Playwright is exact, browser revision is recorded, and Dependabot excludes renderer changes |

QAS-001 remains task-level partial because the ordinary wheel omits top-level
runtime resources. G1 requires a reproducible clean-checkout development and
spike workflow, which is proven; it does not authorize publishing that wheel.
The resource-layout change must be coordinated with `resource_path()` in Lot 2
and tested from source, an installed wheel, and `sys._MEIPASS` before any wheel
claim. Hosted workflow URLs and repository settings are likewise operational
evidence to collect after publication, not substitutes for the native clean
environment evidence already recorded.

## Remaining owners and risks

- QAS owner: retain CI/scanner URLs after publication and add release-platform
  locks only as lanes become active.
- Packaging/core owners: decide and test wheel resource layout without breaking
  source or `sys._MEIPASS` resolution.
- Repository administrator: enable the hosted security settings and branch
  protection.
- Renderer owner: golden-review the Markdown/Playwright target before it replaces
  any production build evidence.

The clean Linux environment used network only during installation. Runtime
downloads remain forbidden.
