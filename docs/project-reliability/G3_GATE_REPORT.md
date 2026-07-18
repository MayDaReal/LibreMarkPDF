# Gate G3 Windows report

Status: **WINDOWS G3 NOT YET PASSED — native evidence pending**
Starting commit: `7b147a027e18a93d15000ac5d43cb810eb03d9a2`  
Scope: mandatory Windows x64 Lots 3A, 3B, 3C, and 3D

## Initial custody

- `git status --short --branch` returned `## main` and the pre-existing deletion
  ` D docs/project-reliability/G2_WINDOWS_EXECUTION_PROMPT.md`.
- `git rev-parse HEAD` returned
  `7b147a027e18a93d15000ac5d43cb810eb03d9a2`.
- `git log -1 --show-signature` verified a good ED25519 signature for
  `maydareality@gmail.com`, key
  `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`, on commit
  `7b147a027e18a93d15000ac5d43cb810eb03d9a2` (`Record Unicode extraction
  limitation`).
- The local immutable `BASELINE_AUDIT.md` was read and was not modified,
  staged, or published.
- `docs/project-reliability/archive/g1/` is immutable and will not be changed.
- The pre-existing G2 prompt deletion is unrelated owner work and will not be
  edited, staged, restored, moved, or published.

## Authorization and exclusions

The owner explicitly authorized G3 implementation and evaluation while G2 is
open. This report does not reopen, alter, weaken, or claim closure of G2. macOS
tasks `MAC-001` through `MAC-005`, optional Linux distribution tasks `LNX-001`
through `LNX-005`, Lot 4, release publication, hosted settings, credentials,
signing setup, release upload, spending, pushing, and baseline/G1 changes are
excluded.

## Known cross-gate limitation

G2 retains fixture `23-unicode` and the pinned PDFium 5.11.0 extraction
difference: Linux reports `हि न्दी`, while retained native Windows evidence
reports `हिन्दी`. The owner directed that it not be normalized, ignored,
thresholded, removed, or treated as accepted. It remains a separate G2 blocker
and regression target. It does not block Lot 3 implementation or the recording
of native Windows G3 candidate evidence.

## Contract discrepancy found before implementation

ADR-006 names the canonical explicit render-date option `--date YYYY-MM-DD`.
The current CLI, README, both manuals, and `SKILL.md` expose
`--render-date YYYY-MM-DD`. G3 will preserve the shipped spelling as a legacy
alias while aligning the approved public contract; no renderer behavior or
date semantics will be changed silently.

## Environment

The integration workspace is Linux, not native Windows. Native Windows edition,
build, x64 architecture, exact artifact behavior, disconnected-network state,
AV observations, Authenticode status, GUI screenshots, and Windows performance
must come from a clean native Windows x64 execution of the exact candidate.
Until that evidence is returned and verified, Windows G3 cannot pass.

## Command log

| Command | Exit | Result |
| --- | ---: | --- |
| `git status --short --branch && git rev-parse HEAD && git log -1 --show-signature` | 0 | Initial custody recorded as above. |
| `rg --files` with generated/build/browser exclusions | 0 | Repository inputs inventoried; no generated artifacts searched. |
| Complete reads required by the owner and `AGENTS.md` | 0 | Contracts, reliability records, implementation, relevant tests, packaging inputs, locks, and Windows validation guide read before code changes. |
| `venv-linux/bin/python -m py_compile ...` plus JSON/TOML parsing | 0 | Changed Python modules compile; public JSON schema and `pyproject.toml` parse. |
| focused CLI/theme/GUI/i18n/packaging/harness/SBOM suite | 0 | 58 focused tests passed after correcting two mistyped test-class selectors. |
| `PYENV_VERSION=3.9.23 python -m py_compile ...` | 0 | Every changed runtime Python module and evidence Python tool is valid Python 3.9 syntax. |
| `venv-linux/bin/ruff check <changed Python files>` | 0 | No diagnostics. Ruff is supplementary, not an authoritative project-wide formatter. |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` | 0 | 152 tests passed in 97.490 seconds, including real Chromium PDF, preview, offline-resource, subprocess Unicode/space/CSS, and partial-batch checks. A final rerun after the last focused changes is recorded below. |
| `venv-linux/bin/python -m libremark_pdf --version` | 0 | `LibreMark PDF 1.0.0; render-profile default@1; Playwright 1.60.0; Chromium 148.0.7778.96 (revision 1223)`. |
| `venv-linux/bin/python -m libremark_pdf convert --help` | 0 | Approved options, canonical `--date`, retained `--render-date`, theme selection, deterministic JSON, headers/footers, overwrite, and trusted-static mode shown. |
| `venv-linux/bin/python -m libremark_pdf doctor --json` | 0 | Read-only resource probe reports CSS, seven fonts, icons, licence, default theme, and staged browser present. No browser was launched or downloaded. |
| `git diff --check` | 0 | No whitespace errors; Git reports only line-ending notices for pre-existing Windows-oriented spec/batch formats. |
| final `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` | 0 | 158 tests passed in 100.446 seconds on the exact pre-commit implementation state. |
| preview baseline timing with three independent `render_preview_png` calls | 0 | Profile resolution took 0.072 seconds; previews took 10.918, 10.116, and 10.699 seconds. |
| persistent-browser diagnostic with the existing full templates | 0 | Browser startup was 0.280 seconds; each conversion still took 9.802–9.905 seconds and PDFium rasterization took 0.002–0.015 seconds, isolating HTML/template ingestion rather than browser startup or rasterization. |
| persistent preview diagnostic before template payload reduction | 0 | First preview took 10.593 seconds; header-only changes still took 7.171 and 7.308 seconds because each header and footer template embedded the complete 29 MB font CSS. |
| optimized `PreviewSession` timing, Latin header changes | 0 | Session startup took 0.283 seconds; first preview took 3.168 seconds and subsequent header changes took 0.123 and 0.103 seconds. |
| final-PDF versus optimized-preview pixel comparison | 0 | Same raster dimensions; `ImageChops.difference(...).getbbox()` returned `None`, so every pixel matched for the retained Latin header/footer case. |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core tests.test_gui -v'` | 0 | 88 focused core/GUI tests passed in 66.981 seconds. |
| final `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` after preview optimization | 0 | 182 tests passed in 93.075 seconds; the final PDF remains tagged and retains its outline. |
| GUI architecture focused check: `venv-linux/bin/python -m unittest tests.test_gui tests.test_i18n -v` | 0 | 28 tests passed after splitting the 985-line Tk module; workers, optional DnD, queue transitions, injected desktop services, EN/FR parity, and native-path argument handling passed. |
| GUI architecture full check: `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` | 0 | 184 tests passed in 91.259 seconds on the final implementation, including real Chromium conversion and preview, CLI subprocess, themes, Linux/Windows packaging contracts, and offline resource policy. |

## Implemented observable contracts

### Lot 3A

- The CLI converts through the shared core only. Argument-parser failures honor
  `--json`, emit exactly one deterministic UTF-8 JSON document on stdout, leave
  stderr empty, and return `2`; conversion/validation failures return nonzero
  with one result per input.
- Subprocess coverage includes stdout, stderr, status, invalid options, missing
  Unicode-and-space paths, input/output collisions, duplicate batch
  destinations, unsafe CSS, missing resources, unavailable destinations, real
  Unicode/resource/custom-CSS conversion, and a real partial batch.
- `--version` reports the application, `default@1` render profile, Playwright
  1.60.0, Chromium 148.0.7778.96, and revision 1223.
- `doctor` is read-only and does not launch Chromium or mutate the browser
  cache. It reports the staged executable paths and required resources.
- ADR-006 `--date` is canonical. The previously documented `--render-date`
  spelling remains an equivalent legacy alias.
- The CLI exposes shared-core theme selection and local theme lifecycle
  commands. `--css` and `--theme` are mutually exclusive.
- README, EN/FR manuals, CLI help, `SKILL.md`, and
  `docs/CLI_JSON_SCHEMA.json` describe the same public contract.

### Lot 3B

- The Tk adapter uses scrollable file/body/preview canvases and 50–200% preview
  zoom. Preview requests debounce and carry a monotonically increasing
  generation; stale results are discarded.
- The previous 985-line Tk module is separated by responsibility. `gui.py`
  owns lifecycle, localization, and main-thread queue dispatch; `gui_layout.py`
  owns widget construction; `gui_inputs.py`, `gui_preview.py`, and
  `gui_conversion.py` own their respective interactions. No resulting GUI
  module exceeds 285 lines.
- `desktop_services.py` contains no Tk or Pillow import and provides an
  injectable service boundary for preview workers, batch conversion, and
  native path opening. A future UI technology can reuse this boundary and the
  shared core without copying rendering logic; Tk remains the authoritative
  current desktop entry point.
- One durable preview worker owns one core `PreviewSession` on one background
  thread. It coalesces queued edits to the newest request, while the refresh
  action remains available and every Tk call remains on the main thread.
- The core retains one network-denied Chromium page for visually identical
  content. Header/footer-only changes reuse that loaded page. Preview templates
  embed only font families selected by their actual text; final PDF templates
  and their accessibility settings are unchanged.
- On the Linux development host, Latin header edits improved from about
  7.2 seconds to 0.10–0.12 seconds after the first preview. The optimized
  preview and final-PDF raster were pixel-identical for the measured case.
  Native Windows timing and non-Latin visual evidence remain required.
- Workers call only shared-core functions and queue immutable messages. Every
  Tk mutation, dialog, and result action remains on the main thread.
- Batch conversion exposes per-item progress, cooperative cancellation, and
  deferred safe close. A close request suppresses completion/error dialogs and
  waits for the active worker result before destroying Tk.
- Operation controls and theme cards are disabled during incompatible work.
  The current status is stored as a translation key and arguments, so an
  EN/FR switch preserves its meaning.
- Core preflight exposes collisions and existing outputs before any worker
  starts. Declining the choice does not resolve render options or launch a
  worker.
- Open-PDF/open-folder actions receive successful results only.
- Imports work with `tkinterdnd2` installed and with its import deliberately
  blocked. EN and FR tables have identical keys and exact placeholder parity.
- Native keyboard order, screen-reader labels, contrast, DnD interaction, and
  100/150/200% high-DPI behavior remain mandatory human evidence.

### Lot 3C

- Schema-1 local theme manifests declare stable ID/version, EN/FR names,
  `default@1` compatibility, CSS, licences, preview roles, and a lowercase
  SHA-256 for every package file.
- `default@1` is an immutable, byte-exact public alias of the approved root
  `style.css`; explicit and implicit default preparation produce identical
  canonical profiles, fingerprints, and full HTML.
- Validation rejects traversal, backslashes, symlinks, undeclared/unsupported
  files, missing/empty licences, malformed or mismatched hashes, incompatible
  profiles, scripts, network/file URLs, CSS loaders, unsafe preview Markdown,
  and active/external SVG content in every declared asset.
- Shared-core list/show/resolve/install/update/remove/select behavior precedes
  CLI and GUI adapters. Install/update uses atomic sibling publication and
  restores the old theme if publication fails; removal uses an atomic rename.
  A hidden cleanup directory may remain if Windows delays deletion, but no
  partial theme becomes selectable.
- The `community-blue@1` fixture is validation evidence only. It is not an
  approved distributed extra theme because named visual review and retained
  before/after previews are still pending. No golden updates occur during
  tests.

### Lot 3D implementation

- The portable spec builds a single analysis into distinct
  `LibreMarkPDF.exe` (GUI/no console), `LibreMarkPDF-cli.exe` (authoritative
  console streams), and `LibreMarkPDF-debug.exe` (diagnostic GUI console).
- The onedir candidate includes the exact browser tree, fonts, themes/docs,
  icons/assets, project and third-party notices, font licences, PDFium and
  frozen dependency resources. The build script enforces CPython 3.9 and
  PyInstaller 6.21.0 and performs no installation or download.
- `tools/run_g3_windows_candidate.ps1` rejects non-native/non-AMD64 execution
  and dirty source, records OS/source/dependency/resource identities, runs the
  full suite and build, copies the complete candidate to an external
  Unicode-and-space path, removes Python and Playwright cache discovery from
  the isolated environment, verifies physical adapters are down before and
  after runtime tests, exercises CLI success/error/partial/collision/theme/ACL
  cases, smokes both GUIs, runs the exact candidate corpus, produces the SBOM,
  records Authenticode/Defender/size/performance, and creates hashed candidate
  and evidence ZIPs.
- The exact-artifact corpus harness invokes only `LibreMarkPDF-cli.exe` for
  conversion, reuses the frozen G2 semantic/visual comparison functions, keeps
  resumable checkpoints and diffs, and has no expected-data writer.
- The SPDX 2.3 generator inventories every artifact file with SHA-1/SHA-256,
  file licence/copyright assertions, a package verification code, and every
  exact locked dependency. Candidate notices accurately defer publication
  review to excluded Lot 4.

## Environment and retained identities

The development evidence host reports:

- `Linux forge-ai-core 6.17.0-35-generic`, x86_64;
- CPython 3.12.3 test environment;
- Python 3.9.23 syntax interpreter;
- Markdown 3.10.2, Pillow 12.3.0, Playwright 1.60.0, pypdfium2 5.11.0,
  PyInstaller 6.21.0, tkinterdnd2 0.6.2.

This is implementation evidence only, not a Linux distribution lane and not a
substitute for native Windows x64 evidence.

| Input | SHA-256 |
| --- | --- |
| `style.css` / `default@1` source | `abd57a32108e78e204706eb8d437d8c0b94c333245d3e5ce83cc31aec4d550a9` |
| Windows x64 CPython 3.9 lock | `cfb6b7de3d272bd57eac79c38e68fad3c6836f1930353cd789dad9251fd87c9d` |
| canonical fixture manifest | `3118048f16c6d047efaf4bfe779c808fccac17ffbfade1192498b07b7434ecdb` |
| immutable expected data | `dd32efe4bb7728f80a4e9d7c47d77d7f136c3b54e6de37ddaa8184c08c277464` |
| community theme manifest | `cedafbb3e8025099c45f146d2241c5df31a20fca0ad52e148edb0cdd74ef45da` |
| community CSS | `81b0804d4d15e816aaad4307948160880113bbd5c89475e4fdd5a69ceab79a00` |
| community licence | `4b50962e452c45b58d5aa3287d4074ae2c4c99a2ca2230c59bdc78da40dfa14d` |
| community preview Markdown | `e568e21c4458cca377e008170fa82cf9b40ffb46ecace242bab4f88b00103536` |
| CLI JSON schema | `db27aca1c83d7f0e35aaacd8b597e3eda96655f9682e97ac442cfb7d918ee979` |
| native runner | `1048e6c6fc9d03bbf6e9c1cace6926189041d4cc06ed209fb10e2bf32c47785a` |
| exact-artifact harness | `5a10cf0512e3ebd3aa2128a037151cfb7490d04bc8663715875617767b6a045c` |
| SPDX generator | `ebc5b7d749c1e4ceeb84492eebb4701360d69243640fa3ee3a79a4a816b2f1f4` |

Font and icon SHA-256 values remain those frozen in the canonical render
profile and are emitted again by the native runner in
`logs/source-input-hashes.json`.

## Failed experiments and limitations

- The first local Chromium timing command ran inside the filesystem sandbox and
  failed with `BROWSER_UNAVAILABLE` after Chromium reported
  `sandbox_host_linux.cc:41 ... Operation not permitted`. The same read-only
  diagnostic outside that sandbox completed; this was an execution-environment
  restriction, not an application failure.
- Browser-process reuse alone did not improve preview latency: it retained
  9.8-second conversions. A second diagnostic showed `page.pdf()` and PDFium
  were fast, leading to the 29 MB document and duplicated 58 MB header/footer
  font payloads. The intermediate persistent implementation improved repeat
  latency only to 7.2 seconds and was not accepted as the final correction.
- Two focused invocations used nonexistent unittest class selectors
  `tests.test_cli.TestCliContract` and `tests.test_cli.TestCli`; each returned
  exit `1` with `AttributeError`. The corrected
  `tests.test_cli.TestConvertCommand` invocation passed.
- The first dependency-version probe accessed nonexistent
  `pypdfium2.__version__` and printed an `AttributeError`; the shell sequence
  continued and ended `0`. A corrected `importlib.metadata.version` probe
  reports pypdfium2 5.11.0.
- The first Python 3.9 command used the inactive pyenv shim and returned `127`.
  `PYENV_VERSION=3.9.23 python ...` then compiled all changed Python sources
  successfully.
- PowerShell is unavailable on this Linux host. The native runner has static
  coverage but its PowerShell parsing, Windows ACL behavior, PyInstaller
  multi-entry output, Authenticode query, and complete execution are unverified.
- The Linux development environment uses Markdown 3.10.2, while the Windows
  candidate lock pins Markdown 3.9. Therefore its development profile
  fingerprint is not the frozen Windows expected fingerprint. The native
  harness deliberately runs source preparation and the artifact under the same
  hash-locked Python 3.9 environment; exact fingerprint/evidence comparison is
  still mandatory and unverified.
- No Windows edition/build, AMD64 observation, exact ZIP, ZIP size/SHA-256,
  disconnected physical-adapter proof, empty-cache/no-Python artifact run,
  native GUI evidence, canonical report/diffs, native SBOM, AV result, or
  Authenticode status exists yet.
- No named human has approved the community theme preview or the Windows
  accessibility/high-DPI checklist.

## Exact remaining G3 work

| Remaining work | Owner | Required command or decision | Classification |
| --- | --- | --- | --- |
| Build and collect the exact native candidate evidence from a clean signed commit | native Windows x64 owner | `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_g3_windows_candidate.ps1 -EvidenceRoot "C:\G3 Evidence\LibreMark PDF – Windows x64" -Python "$PWD\venv\Scripts\python.exe" -RequireOffline` | G3 blocker (`WIN-004`–`WIN-009`) |
| Review the generated canonical report and retained diffs; reject any change beyond the separately known `23-unicode` result | G3 integration owner | inspect `canonical-report.json`, `canonical-diff\`, and exact artifact JSON/checkpoints | G3 blocker |
| Complete and sign the generated GUI/accessibility review against the exact candidate | named Windows reviewer | complete `manual-gui-review.md` with screenshots/video at 100/150/200% scale, EN/FR, DnD/fallback, preview, cancellation, collisions, themes | G3 blocker (`GUI-007`, `WIN-005`) |
| Review the optional community theme preview and contribution evidence | named theme reviewer | retain before/after images, licence provenance, hashes, profile identity, and explicit PASS/FAIL | G3 blocker for `STY-007`/`STY-008`; removing the optional fixture from distribution scope is an owner alternative |
| Resolve PDFium fixture `23-unicode` independently | G2 owner | separate G2 evidence and decision only; no G3 normalization | known separate G2 blocker, not a G3 implementation blocker |

Detailed implementation, failed experiments, command outputs, hashes, native
environment data, evidence paths, limitations, and final decision will be
appended as work proceeds. Task state is maintained in
[`G3_EXECUTION_BOARD.md`](G3_EXECUTION_BOARD.md).

## Current decision

**WINDOWS G3 NOT YET PASSED**

Reason: implementation is complete, but exact native Windows x64 candidate,
manual GUI/accessibility/theme review, artifact archive, SBOM, and canonical
comparison evidence do not yet exist. This is a G3 status, separate from the
known G2 blocker.
