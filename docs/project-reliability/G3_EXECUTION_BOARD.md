# Gate G3 Windows execution board

Status: **implementation complete — native Windows evidence pending**
Integration owner: **G3 integration owner**  
Starting commit: `7b147a027e18a93d15000ac5d43cb810eb03d9a2`

This board covers only mandatory Windows x64 Lots 3A through 3D. The owner
authorized this work while G2 remains independently open for the retained
`23-unicode` PDFium extraction difference. That limitation is cross-gate
context, not permission to alter G2 and not a blocker to implementing or
recording G3 work. macOS, optional Linux distribution, Lot 4, publication,
credentials, signing setup, uploads, and pushing are outside this board.

States are `open`, `in progress`, `implemented`, `evidence pending`, `blocked`,
or `accepted`. `Implemented` never substitutes for the native evidence required
for `accepted`.

## Current state ledger

The detailed rows below retain their pre-implementation planning state. This
ledger is the canonical current state and supersedes the original `open` cell:

| Tasks | Current state | Reason / next evidence |
| --- | --- | --- |
| `CLI-001`–`CLI-008` | implemented | Source subprocess, parser, schema, identity, doctor, alias, documentation, and browser-backed tests pass; exact frozen Windows CLI evidence remains under `WIN-005`. |
| `GUI-001`–`GUI-006` | implemented | Queue orchestration, durable core preview session, latest-request coalescing, debounce/stale rejection, progress/cancel/close, operation guards, result actions, and preflight choices have focused tests; native interaction remains under `WIN-005`. |
| `GUI-007` | evidence pending | Keyboard/layout markers and the native checklist exist; a named Windows accessibility/high-DPI review is mandatory. |
| `GUI-008` | implemented | Isolated imports pass with `tkinterdnd2` installed and deliberately unavailable; native DnD and fallback launch observations remain. |
| `GUI-009`–`GUI-010` | implemented | EN/FR key and placeholder parity and worker no-Tk boundaries pass; idiomatic/native inspection remains. |
| `STY-001`–`STY-006` | implemented | Shared-core schema, default alias, adversarial validation, atomic lifecycle, APIs, and CLI/GUI adapters pass focused tests. |
| `STY-007` | evidence pending | Contribution workflow and non-mutating fixture checks exist; the community preview still needs named human review and retained before/after images. |
| `STY-008` | evidence pending | The optional community theme is a test fixture only and default compatibility passes; it is not approved for distribution without `STY-007`. |
| `WIN-001`–`WIN-003` | implemented | Static packaging tests pass for distinct GUI, CLI, and diagnostic paths and frozen resources; native PyInstaller behavior is unverified. |
| `WIN-004`–`WIN-009` | evidence pending | The native runner, exact-artifact canonical harness, SPDX generator, guide, and checklists are ready; a clean native Windows x64 run is required. |

## Lot 3A — CLI and agent contract

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CLI-001` | CLI/skill owner | `tests/test_cli.py`, subprocess fixtures | shared core API | In-process mocks only / real subprocess stdout, stderr, JSON, and exit status are asserted | `python -m unittest tests.test_cli -v` | subprocess transcript and exit codes | open | frozen console can differ from source | `WIN-001` exact console run |
| `CLI-002` | CLI/skill owner | `libremark_pdf/cli.py`, `tests/test_cli.py` | `CLI-001` | parser/validation shapes vary / every error is clean deterministic JSON with a stable code | `python -m unittest tests.test_cli -v` | JSON parse proof with empty stderr | open | argparse may emit non-JSON before dispatch | exact artifact contract |
| `CLI-003` | CLI/skill owner | `tests/test_cli.py`, fixtures | core collision/resource/output policies | narrow happy/error tests / partial batches, collision, Unicode/space, resource, CSS, and permission cases covered | `python -m unittest tests.test_cli -v` | per-case stdout/stderr/exit record | open | real Windows ACL differs from mocks | native ACL case |
| `CLI-004` | CLI/skill owner | `libremark_pdf/cli.py`, package version tests | render profile and locked browser identity | no version command / application, profile, Playwright, Chromium revision and executable identity reported | `python -m libremark_pdf --version` | deterministic human and JSON identity output | open | installed browser product version needs native executable | `WIN-002` staged browser |
| `CLI-005` | CLI/skill owner | `libremark_pdf/cli.py`, docs | approved core options, theme API | no theme and ADR-006 spelling mismatch / only approved conversion controls are exposed | `python -m libremark_pdf convert --help` | reviewed option inventory and adapter test | open | legacy compatibility ambiguity | `CLI-008`, `STY-005` |
| `CLI-006` | CLI/skill owner | `libremark_pdf/cli.py`, tests, docs | resource and browser identity helpers | no doctor / read-only diagnostics, or a recorded rejection if side-effect freedom cannot be guaranteed | `python -m libremark_pdf doctor --json` | before/after resource hashes and no-write proof | open | browser probing could launch or mutate cache | design review |
| `CLI-007` | docs + CLI owner | `README.md`, manuals, `SKILL.md`, CLI help | `CLI-002` through `CLI-006` | public descriptions omit G3 additions / five public contracts and JSON schema agree | `python -m unittest tests.test_cli tests.test_community -v` | documentation matrix and help capture | open | translation drift | Lot 3A feature freeze |
| `CLI-008` | CLI/skill owner | `libremark_pdf/cli.py`, tests, docs | historical CLI contract | `--render-date` only / approved legacy spelling remains functional alongside canonical ADR spelling | `python -m unittest tests.test_cli -v` | both spellings produce identical core arguments | open | aliases can outlive intended deprecation | owner policy at G4 |

## Lot 3B — Desktop UX, accessibility, and i18n

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GUI-001` | GUI/i18n owner | `libremark_pdf/gui.py`, `desktop/tk/layout.py`, GUI tests | core preview API | fixed page and non-scroll file list / minimum-size UI, file list, and preview scroll; preview zoom controls | `python -m unittest tests.test_gui -v` | layout assertions plus native screenshots/checklist | open | Tk geometry is platform-specific | `WIN-005` |
| `GUI-002` | GUI/i18n owner | `gui.py`, `desktop/tk/preview.py`, `desktop_services.py`, `core.py`, GUI/core tests | preview worker queue | every edit launches a browser and disables refresh for 10–11 seconds / one durable core session coalesces stale requests, reuses unchanged page content, and keeps refresh available; measured Latin header edits complete in 0.10–0.12 seconds after the first preview | `python -m unittest tests.test_gui tests.test_core -v` | deterministic coalescing/session tests, Linux timings, pixel comparison | implemented | CJK header templates necessarily retain the large CJK font; native Windows timing remains unverified | native stress run |
| `GUI-003` | GUI/i18n owner | `gui.py`, `desktop/tk/conversion.py`, `desktop_services.py`, `core.py`, GUI/core tests | cancellable batch boundary | no progress/cancel/safe close / per-item progress, cooperative cancellation, and deferred safe close | `python -m unittest tests.test_gui tests.test_core -v` | result counts and close/cancel state transitions | open | active render cannot be force-killed safely | native large batch |
| `GUI-004` | GUI/i18n owner | `gui.py`, `desktop/tk/inputs.py`, `desktop/tk/conversion.py`, `i18n.py`, tests | operation state machine | preview and generation overlap; language resets status / incompatible actions disabled and status retranslated in place | `python -m unittest tests.test_gui tests.test_i18n -v` | state/translation transition tests | open | unexpected window-manager close | `GUI-003` |
| `GUI-005` | GUI/i18n owner | `desktop/tk/conversion.py`, `desktop_services.py`, `i18n.py`, tests | successful result paths | no result actions / open-PDF and open-folder appear only for successful outputs | `python -m unittest tests.test_gui tests.test_i18n -v` | mocked OS-open calls and visibility test | open | shell associations vary | native Windows check |
| `GUI-006` | GUI/i18n owner | `desktop/tk/inputs.py`, `desktop/tk/conversion.py`, `i18n.py`, tests | core preflight/collision policy | conversion begins before choice / complete overwrite and collision decision occurs before workers start | `python -m unittest tests.test_gui -v` | no-render-on-decline and explicit-overwrite tests | open | batch-level UX complexity | native collision flow |
| `GUI-007` | GUI/i18n owner | `gui.py`, `desktop/tk/layout.py`, docs, tests | stable layout | accessibility unreviewed / keyboard order, focus, text labels, contrast, and DPI behavior documented and exercised | `python -m unittest tests.test_gui -v` | focus/binding assertions and native checklist | open | screen-reader semantics need native inspection | `WIN-005` human review |
| `GUI-008` | GUI/i18n owner | `gui.py`, `desktop/tk/layout.py`, GUI tests | optional dependency import | fallback documented but untested / import and launch construction work with and without `tkinterdnd2` | `python -m unittest tests.test_gui -v` | isolated import tests for both modes | open | native DnD behavior | Windows smoke |
| `GUI-009` | GUI/i18n owner | `libremark_pdf/i18n.py`, tests | all new GUI strings | key parity only / exact EN/FR keys and format placeholders match | `python -m unittest tests.test_i18n -v` | key and placeholder parity report | open | idiomatic quality needs human review | bilingual review |
| `GUI-010` | GUI/i18n owner | `gui.py`, `desktop/tk/`, `desktop_services.py`, GUI tests | queue architecture | intended main-thread Tk boundary is incomplete to test / toolkit-neutral workers contain no Tk calls and every widget mutation and dialog stays in Tk queue handlers | `python -m unittest tests.test_gui -v` | worker-thread guard and injectable-service boundary tests | open | third-party Tk callbacks | native stress run |

## Lot 3C — Community theme system

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `STY-001` | theme/core owner | `libremark_pdf/core.py`, theme schema/docs/tests | render profile `default@1` | arbitrary CSS path only / versioned manifest identifies files, hashes, licences, and compatible profile | `python -m unittest tests.test_themes -v` | valid/invalid manifest fixtures and hashes | open | schema evolution | contribution policy |
| `STY-002` | theme/core owner | `themes/default`, packaging, core tests | approved `style.css` | bundled CSS unnamed / `default@1` resolves to byte-exact approved CSS | `python -m unittest tests.test_themes -v` | byte/hash equality with `style.css` | open | packaging duplication drift | `WIN-002` |
| `STY-003` | theme/core owner | `libremark_pdf/core.py`, theme fixtures/tests | ADR-004 and render profile | custom CSS blocks loaders only / packages reject scripts, URLs, traversal, missing licences, hash mismatch, and incompatible profile | `python -m unittest tests.test_themes -v` | adversarial fixture matrix | open | CSS parser uses conservative lexical policy | security review |
| `STY-004` | theme/core owner | `libremark_pdf/core.py`, theme tests | validated manifest | no package lifecycle / user-space install, update, and remove publish atomically | `python -m unittest tests.test_themes -v` | interruption/failure cleanup and preservation proof | open | Windows file locking | native lifecycle run |
| `STY-005` | theme/core owner | `libremark_pdf/core.py`, tests | `STY-001` through `STY-004` | no theme API / shared core list, show, resolve, install, remove, and selection API | `python -m unittest tests.test_themes -v` | API result schema and error codes | open | user theme directory permissions | CLI/GUI adapters |
| `STY-006` | CLI + GUI owners | `cli.py`, `gui.py`, `i18n.py`, adapter tests | `STY-005` | custom CSS chooser only / CLI selection and GUI cards/previews use the shared core | `python -m unittest tests.test_cli tests.test_gui -v` | adapter call and selection persistence evidence | open | preview performance | `WIN-005` |
| `STY-007` | theme + QA owner | fixtures, theme docs/tests, approved goldens | stable theme schema | no contribution gate / fixtures, explicit preview workflow, hashes, licence and validation checks | `python -m unittest tests.test_themes tests.test_g2_harness -v` | non-mutating golden/contribution checks | open | visual approval remains human | reviewed preview |
| `STY-008` | theme owner | optional theme packages | default compatibility | no extra theme / extras only after byte-exact default and reviewed preview pass | `python -m unittest tests.test_themes -v` | default gate result and per-theme evidence | open | aesthetic scope creep | explicit owner review |

## Lot 3D — Official Windows x64 artifact candidate

| Task | Owner | Owned files | Dependencies | Before / after observable behavior | Focused command | Required evidence | State | Residual risk | Next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WIN-001` | Windows packaging owner | specs, entry points, build scripts/tests | Lot 3A contract | one executable mode chosen at build time / authoritative GUI no-console and CLI console entry paths coexist | `python -m unittest tests.test_packaging -v` | exact frozen GUI/CLI stream evidence | open | PyInstaller subsystem behavior | native builds |
| `WIN-002` | Windows packaging owner | portable spec, resources, packaging tests | themes and locked G2 resources | portable spec omits fonts/licences and themes / exact browser, fonts, themes, icons, licences, PDFium, and data bundled | `python -m unittest tests.test_packaging -v` | artifact inventory and hashes | open | hidden native dependency | native inventory |
| `WIN-003` | Windows packaging owner | build scripts/specs/docs | `WIN-001` | console flag mutates one name / authoritative release GUI and diagnostic/CLI builds have distinct paths | `build_portable.bat` | build logs and entry-point identity | open | user may launch wrong executable | external-path test |
| `WIN-004` | native Windows owner | external evidence archive | completed candidate source | no G3 native build / clean native Windows x64 build from exact commit | `.\build_portable.bat` | OS/build/arch, clean status, lock, full logs | open | no Windows runner in current Linux workspace | native execution |
| `WIN-005` | native Windows owner | external evidence archive | `WIN-004`, Lots 3A–3C | no exact G3 artifact UX evidence / GUI, preview, CLI JSON, batch, collisions, and themes pass from Unicode/space path | G3 Windows harness plus manual GUI checklist | screenshots, transcripts, result files | open | manual UX evidence | native execution |
| `WIN-006` | native Windows owner | external evidence archive | `WIN-005` | no G3 isolation evidence / exact candidate repeats without Python, user cache, or network | G3 offline harness | cache/network/PATH before-after evidence | open | firewall policy may need user rights | native execution |
| `WIN-007` | native Windows owner | external canonical evidence | `WIN-004`, frozen G2 harness | no G3 candidate corpus / exact candidate runs canonical corpus without changing goldens | `python tools\g2_visual_harness.py ...` | full report and retained diffs | open | known G2 `23-unicode` difference disclosed separately | native execution |
| `WIN-008` | Windows owner | report only | candidate built | signing unavailable/unverified / candidate accurately labelled unsigned unless credentials already exist | `Get-AuthenticodeSignature <exe>` | signature status for both entry points | open | unsigned reputation warnings | owner release decision, not credential setup |
| `WIN-009` | Windows packaging owner | evidence tools/docs/archive | exact candidate | no G3 candidate archive / ZIP, size/performance/AV, SHA-256, SBOM, notices, logs and evidence manifest retained | G3 packaging harness | archive and manifest hashes | open | SBOM completeness and AV variance | G3 integration decision |

## Gate rule

Use `WINDOWS G3 PASSED — pending separate G2 closure for release progression`
only after every row above is `accepted` with reproducible native Windows x64
evidence for the exact candidate. Otherwise the gate conclusion is
`WINDOWS G3 NOT YET PASSED`, with each remaining G3 blocker separated from the
known G2 blocker.
