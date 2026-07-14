# Gate G1 integration decision

Decision date: 2026-07-14
Decision: **NOT PASSED — first cross-OS font candidate failed; Lot 2 is not authorized**
Integrator: repository integration owner
Integration base: `4107aea0d7d28a8bf9728d4a27854c5210393380`
Audited continuity identifier: `89f27f26c961b5b2776928e26b1f168ed2c87550`

The frozen baseline was read and was not edited. Production core, GUI, CLI,
i18n, skill, default CSS, fonts, margins, pagination, icons, and approved
identity are unchanged. New executable work is limited to non-production G1
spikes and a diagnostic portable packaging definition. Generated browsers,
fonts, builds, PDFs, PNGs, diffs, caches, and evidence archives remain outside
Git. Unrelated brand work was not staged, deleted, or incorporated.

## Acceptance decision

| G1 criterion | Decision | Evidence / remaining dependency |
| --- | --- | --- |
| Renderer/browser, fonts, resources, thresholds, and Windows format selected from measurements | pending replacement measurement | the first variable-font Windows/Linux pair failed ADR-002; a static Regular/SemiBold replacement repeats exactly on Linux and now requires native Windows measurement and owner review |
| Clean reproducible install and pure tests; dependency roles distinct; no renderer drift | pass | native Windows CPython 3.9 hash-locked install and clean Linux constrained install passed; roles are separated; engine/archive hashes and manual renderer-update policy prevent silent drift |
| Contributor/security policies actionable without private knowledge | pass | OSS-001..008 documents/templates exist and focused tests pass; administrator settings remain explicitly unverified with a documented reporting fallback |
| Locked target engine and font licenses recorded | pass | Playwright 1.60.0 / Chromium 1223 plus both the rejected variable set and seven-file static replacement have immutable commits, byte sizes, SHA-256 values, roles, and OFL records |
| Every unresolved architecture question has an owner | pass | Windows visual operator, renderer, packaging/core, QAS, administrator, integrator, and human-owner responsibilities are named |

The first native Windows archive was reviewed and is internally intact, but
its Windows/Linux comparison failed. The remaining G1 blocker is replacement
static-font Windows/Linux evidence and owner appearance review. A
windowed/signed release candidate, controlled
release performance, hosted workflow URLs/settings, installed-wheel resources,
SBOM/provenance, and production renderer enforcement remain owned later-gate
work and carry no completed claim here.

## Lot 1A task handoff

Owned files: `spikes/g1/`, `G1_RENDERER_SPIKE_REPORT.md`, the diagnostic
portable spec/script, and linked native evidence. Before/after observable
production behavior is unchanged.

| Task | State | Acceptance evidence | Unverified/risk and next gate dependency |
| --- | --- | --- | --- |
| SPIKE-REN-001 | accepted | Playwright 1.60.0, Chromium/headless shell 148.0.7778.96 rev 1223, FFmpeg 1011; native Windows/Linux executable hashes | production migration and golden review in Lot 2 |
| SPIKE-REN-002 | accepted research/revised candidate | rejected six-file variable set retained; seven-file static replacement totals 21,731,032 bytes with four unique OFL records | CJK is 75.6% of replacement payload; final bundled subset requires Lot 2 review |
| SPIKE-REN-003 | pending replacement | first native pair exists but failed; static candidate repeats exactly on Linux | execute the revised `run_windows_visual_evidence.ps1` and return its ZIP/hash |
| SPIKE-REN-004 | accepted feasibility | local data resources render; Linux/Windows probes record zero responses and hostile request abortion | full path/type/size/traversal corpus is Lot 2 implementation evidence |
| SPIKE-REN-005 | accepted feasibility | JavaScript disabled, service workers blocked, untrusted fragment literalized | trusted static HTML and CSS policy implementation remains Lot 2 |
| SPIKE-REN-006 | accepted locally/replacement pending | first cross-OS fingerprints matched despite render failure; static profile/HTML fingerprints repeat exactly on Linux | confirm the new fingerprints on native Windows |
| SPIKE-REN-007 | pending replacement | first pair failed at 4.2511%/5.8090% changed pixels and SSIM 0.57125/0.42945; static Linux repeat passes exactly | compare native Windows static pages without weakening ADR-002 |
| SPIKE-PKG-001 | direction accepted/task partial | native onefile/portable hashes, size, CLI/GUI/preview, offline, paths, Defender, extraction, and timings; ADR-007 selects portable ZIP | exact windowed/console release candidate and controlled performance belong later gates |
| SPIKE-PKG-002 | accepted | revision-1223 only-shell candidate built/exercised; 73,153,275 compressed bytes (38.2%) of obsolete full-browser payload quantified | verify final release-candidate contents later |

Selected directions are: Playwright/Chromium revision 1223; a static-weight
Noto candidate replacing the rejected variable-weight set; data-only local resources with deny-all network, JavaScript and
service-worker controls; unchanged ADR-002 thresholds; and zipped portable
Windows directory as primary format. The selection is architectural evidence,
not authorization to change the current default rendering.

## Lot 1B task handoff

Owned files: `pyproject.toml`, `requirements.txt`, `requirements/`, quality and
security workflows, Dependabot, hygiene/configuration files, and focused tests.
Before, lower-bound dependencies mixed roles and could drift. After, roles are
separate and the active Windows lane has exact archive hashes. Production
rendering remains unchanged.

| Task | State | Acceptance evidence | Unverified/risk and next gate dependency |
| --- | --- | --- | --- |
| QAS-001 | partial/non-blocking | Python >=3.9 metadata, dynamic version, entry point, and constrained editable clean installs work | ordinary wheel omits top-level resources; coordinate layout with `resource_path()` in Lot 2; no wheel claim |
| QAS-002 | accepted | runtime, GUI, build, test, and docs groups are distinct | keep synchronized with later specs/build scripts |
| QAS-003 | accepted active lane | 19-archive Windows x64 CPython 3.9 hash lock installed natively | add locks only for future active release lanes |
| QAS-004 | accepted G1 | configured Python 3.9/3.12 jobs; clean Linux 3.12 and native Windows 3.9 pure suites pass | retain hosted URLs after publication; no hosted-run claim yet |
| QAS-005 | accepted | Python 3.9 compile and Ruff syntax/undefined-name gate pass | no mass formatting |
| QAS-006 | accepted | branch-aware 31% product coverage and 30% floor | GUI/dispatch remain zero; raise with later tests |
| QAS-007 | accepted configuration | CodeQL, dependency review, and administrator checklist exist | hosted security settings/execution remain unverified |
| QAS-008 | accepted | weekly Dependabot with renderer dependencies excluded | renderer changes require manual lock/manifest/golden review |
| QAS-009 | accepted | generated/local paths ignored; line-ending/binary policy present | none observed |
| QAS-010 | accepted | source-manifest hygiene tool/workflow passes | release SBOM/provenance remains a later gate |

The current Linux run passed 47 browser-free tests, Ruff, compileall, and a
107-path hygiene manifest. The complete suite passed 50 tests using Chromium
1223. The earlier clean run retained 31% coverage. Native Windows evidence
predates the new spike tests and passed its then-current 36 pure and 39 complete
tests.

## Lot 1C and 1D handoff

OSS-001..008 remain accepted: contribution, security, conduct, support,
governance, issue/PR, changelog/versioning, roadmap, documentation-sync, and
license-inventory guidance exist without unsupported release claims. Hosted
labels, private reporting, and enforcement settings remain administrator
follow-ups with documented fallbacks.

BRD-001 and BRD-002 remain accepted historical research. BRD-003/004 remain
partial registry/legal research and BRD-005 remains research-only. ADR-008 is
authoritative; no code, documentation identity, logo, or `docs/brand/` work was
renamed, reopened, or incorporated.

## Commands and evidence

Unless stated, commands ran from `/shared/repos/LibreMarkPDF` on Linux x86_64.
Exact renderer/font/visual commands and temporary hashes are in
`G1_RENDERER_SPIKE_REPORT.md`; native commands and artifact hashes are in
`G1_WINDOWS_NATIVE_EVIDENCE.md`.

| Command | Exit | Result |
| --- | ---: | --- |
| initial `git status --short --branch` | 0 | only the four integrator-owned G1 document updates were present; no brand work entered scope |
| official upstream font revision queries and six font/license downloads to `/tmp` | 0 | immutable commits, sizes, and SHA-256 values verified |
| system `python3 -m unittest tests.test_g1_spikes -v` | 1 | expected: system Python lacks `markdown`; no test weakened |
| clean target-version Linux venv install | 0 | Markdown 3.9, Playwright 1.60.0, Pillow 11.3.0, PDFium 5.11.0, coverage 7.10.7, Ruff 0.14.2 |
| Playwright `install --only-shell chromium` into `/tmp` | 0 | Chromium 148.0.7778.96 rev 1223 and FFmpeg 1011 |
| first container-sandboxed visual launch | 1 | known syscall restriction; Chromium reported `sandbox_host_linux` operation not permitted |
| current, candidate, and repeated-candidate visual probes outside that syscall restriction | 0 each | two pages each; zero network attempts/responses; candidate fonts loaded |
| candidate/repeat `cross-os` comparator self-check | 0 | SSIM 1.0, zero changed pixels/region, exact structure and fingerprints |
| current/candidate `appearance` comparator | 0 | deliberate typography difference recorded with `review` result |
| native Windows variable-font archive, SHA-256 `f2e5e636c3e5676f38b270b5e970d2c38ddded0ae9933d234ea15691e0b63014` | 0 | commit `4107aea`, clean status, exact engine/dependencies, zero network requests, exact Windows repeat; internal hashes match despite malformed `ea/` path prefixes |
| variable-font Windows/Linux `cross-os` comparator | 1 | expected gate rejection: 4.2511%/5.8090% changed pixels, SSIM 0.57125/0.42945, and differing extracted text |
| static candidate fetch and two Linux probes | 0 each | seven fonts/four licenses verified; zero network requests during render; all glyphs custom |
| static Linux repeat comparator | 0 | SSIM 1.0, zero changed pixels/region, exact text and fingerprints |
| compileall and `ruff check libremark_pdf tests tools spikes` | 0 | Python 3.9-targeted focused checks pass |
| 47-test browser-free command | 0 | all pass; earlier clean run retained 31% branch-aware product coverage |
| `python tools/check_source_hygiene.py` | 0 | 107 source paths accepted |
| full target-browser `unittest discover -s tests -v` | 0 | 50 tests pass with Chromium 1223 |
| `python -m libremark_pdf convert --help` | 0 | CLI contract available |
| target-browser README JSON conversion | 0 | valid JSON, three-page temporary PDF, SHA-256 `62b526e7d0a3929001601814904dacb994d6c02942b1fdbde53bdbc8c527fa34` |
| `git diff --check` | 0 | no whitespace errors at the recorded review point |

## Current risk and next dependency

G1 must remain **not passed** until the replacement static-font native Windows
ZIP is reviewed. The first ZIP proved that the variable fonts are interpreted
differently: Windows embedded Regular and SemiBold instances while Linux
embedded only the Regular instance, changing line wrapping and extracted text.
The Windows operator must use the exact new source commit, CPython 3.9 locked
versions, the existing revision-1223 browser payload, and a new evidence
directory outside the repository. Font preparation occurs
before network disconnection; `Run` performs verification and rendering without
dependency or browser downloads. The integrator then compares Windows candidate
pages against the retained Linux candidate evidence and presents the
current-versus-candidate images for explicit owner approval. Only that reviewed
result can change this report to **PASSED** and authorize Lot 2.
