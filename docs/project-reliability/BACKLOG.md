# High-reliability program backlog

Status: **ready for planning**
Baseline: [`BASELINE_AUDIT.md`](BASELINE_AUDIT.md), score **43/100**
Architecture: [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md)

## Operating rules

- One orchestrator owns integration and gates.
- Agents work in separate branches/worktrees. In a shared workspace, never run
  two writers against the same files.
- A task is complete only with implementation, focused tests, synchronized
  documentation, and recorded evidence.
- Do not change baseline weights or scores. Improvements appear only in the
  final audit.
- Do not advertise a platform until its native end-to-end release gate passes.
- Windows x64 is the first mandatory official target. Linux and macOS are
  independent gated expansions, not blockers for the first Windows release.
- Preserve the current public conversion contract unless an approved ADR
  explicitly changes it.
- The owner approved `LibreMark PDF`, its final logo, and the future
  compatibility policy in
  [`ADR-008-PRODUCT-IDENTITY.md`](ADR-008-PRODUCT-IDENTITY.md).

## Execution graph

```text
Lot 0: baseline and decisions (sequential)
  |
  +-- Lot 1A: renderer spike -------------------+
  +-- Lot 1B: package/quality foundations ------+--> Gate G1
  +-- Lot 1C: OSS/community foundations --------+
  +-- Lot 1D: identity availability research ---+
                                                    |
             Lot 2A: deterministic core -----------+
                                                    +--> Gate G2 (core API frozen)
             Lot 2B: visual test harness -----------+
                                                          |
  +-- Lot 3A: CLI contract ------------------------------+
  +-- Lot 3B: GUI/UX ------------------------------------+--> Gate G3
  +-- Lot 3C: theme system ------------------------------+
  +-- Lot 3D: Windows packaging -------------------------+
  +-- Lot 3E: Linux packaging (optional target) ---------+
  +-- Lot 3F: macOS packaging (future gated target) -----+
                                                          |
             Lot 4A: release/supply chain ----------------+
             Lot 4B: documentation/discoverability -------+--> Gate G4
             Lot 4C: approved product identity -----------+
                                                                  |
             Lot 5: independent final audit ----------------------+
```

Lots shown on the same level may run in parallel only when their file ownership
does not overlap. Cross-cutting core changes are integrated serially.

## Lot 0 — Freeze evidence and decisions

Owner: orchestrator
Execution: sequential
Exit gate: G0

- [x] `AUD-001` Freeze the dated baseline, fixed rubric, evidence, limitations,
  and score of 43/100.
- [x] `ADR-001` Record the target architecture and explain why a web rewrite or
  universal executable does not satisfy deterministic local PDF generation.
- [x] `ADR-002` Approve the visual-equivalence definition and initial metrics.
  Evidence: [`ADR-002-VISUAL-EQUIVALENCE.md`](ADR-002-VISUAL-EQUIVALENCE.md).
- [x] `ADR-003` Approve initial supported OS/architecture policy: Windows x64
  mandatory, Linux/macOS gated separately. Evidence:
  [`ADR-003-PLATFORM-POLICY.md`](ADR-003-PLATFORM-POLICY.md).
- [x] `ADR-004` Approve the Markdown trust model: raw HTML, JavaScript, local
  files, remote resources, and compatibility flags. Evidence:
  [`ADR-004-MARKDOWN-TRUST-MODEL.md`](ADR-004-MARKDOWN-TRUST-MODEL.md).
- [x] `ADR-005` Approve overwrite, output-collision, result-feedback, and
  user-controlled diagnostic-report behavior. Evidence:
  [`ADR-005-OUTPUT-INTEGRITY-AND-FEEDBACK.md`](ADR-005-OUTPUT-INTEGRITY-AND-FEEDBACK.md).
- [x] `ADR-006` Decide whether `{date}` is render-time local date, fixed profile
  date, document metadata, or explicit CLI option. Evidence:
  [`ADR-006-RENDER-DATE.md`](ADR-006-RENDER-DATE.md).
- [x] `ADR-007` Decide one-file versus portable-directory release criteria based
  on startup, size, antivirus, and user-friction measurements. Evidence:
  [`ADR-007-WINDOWS-ARTIFACT-FORMAT.md`](ADR-007-WINDOWS-ARTIFACT-FORMAT.md).
- [ ] `AUD-002` Record a source archive identifier or Git commit when repository
  metadata becomes available.

G0 acceptance:

- The owner has approved ADR-002 through ADR-007.
- Every later task links to a baseline deduction or an approved target.
- The baseline remains immutable.

## Lot 1A — Renderer and distribution feasibility spike

Owner: renderer architect
Execution: parallel with Lots 1B–1D after G0
Files: spike code/fixtures and ADR evidence; no production rewrite yet

- [ ] `SPIKE-REN-001` Identify and lock a Playwright/Chromium pair and record
  the exact browser revision and payload used by headless rendering.
- [ ] `SPIKE-REN-002` Select redistributable proportional, semibold, monospace,
  and Unicode fallback font candidates; record licenses and size impact.
- [ ] `SPIKE-REN-003` Render representative current-style fixtures on Windows
  and one second OS with candidate embedded fonts.
- [ ] `SPIKE-REN-004` Prototype local relative-image embedding and total network
  denial.
- [ ] `SPIKE-REN-005` Prototype JavaScript/service-worker disablement and the
  approved raw HTML policy.
- [ ] `SPIKE-REN-006` Produce canonical HTML and asset fingerprints.
- [ ] `SPIKE-REN-007` Measure visual variance and validate or amend the proposed
  SSIM/pixel thresholds once, with evidence.
- [ ] `SPIKE-PKG-001` Compare Windows one-file and portable-directory artifacts:
  compressed size, cold/warm startup, conversion time, extraction, and AV scan.
- [ ] `SPIKE-PKG-002` Confirm that only the required Chromium headless payload is
  bundled and quantify the reduction.

Acceptance:

- A written spike report chooses renderer, fonts, resource policy, thresholds,
  and primary Windows artifact format.
- Zero runtime network requests are observed in the offline prototype.
- The chosen direction preserves the approved default-theme appearance within
  the reviewed tolerance.

## Lot 1B — Package and quality foundations

Owner: quality/supply-chain agent
Execution: parallel with Lots 1A, 1C, and 1D
Files: `pyproject.toml`, constraints/locks, CI scaffolding, quality configuration

- [ ] `QAS-001` Add `pyproject.toml` with Python 3.9-compatible metadata,
  application version source, package data, and console entry point.
- [ ] `QAS-002` Separate runtime, GUI, build, test, and documentation dependency
  groups/extras.
- [ ] `QAS-003` Implement a reproducible lock/constraints strategy with hashes
  for release environments.
- [ ] `QAS-004` Add a clean-environment unit-test workflow on supported Python
  versions.
- [ ] `QAS-005` Add focused static checks appropriate to the current codebase,
  without unrelated mass formatting.
- [ ] `QAS-006` Add coverage reporting by subsystem and document the initial
  threshold.
- [ ] `QAS-007` Configure dependency, secret, and code scanning.
- [ ] `QAS-008` Add Dependabot or Renovate with controlled Playwright/browser
  update handling.
- [ ] `QAS-009` Add `.gitignore` and `.gitattributes`; exclude generated builds,
  browsers, venvs, caches, PDFs, and local configuration.
- [ ] `QAS-010` Define source-archive and release-artifact hygiene checks.

Acceptance:

- A clean checkout can install and run pure tests using documented commands.
- Runtime and build dependencies are distinguishable.
- Dependency resolution is repeatable and renderer updates cannot drift silently.

## Lot 1C — Open-source foundations

Owner: community/documentation agent
Execution: parallel with Lots 1A, 1B, and 1D
Files: community health documents and issue/PR templates

- [ ] `OSS-001` Add `CONTRIBUTING.md` with development, test, review, translation,
  and theme contribution workflows.
- [ ] `OSS-002` Add `SECURITY.md` with supported versions and private reporting.
- [ ] `OSS-003` Add a code of conduct, support policy, and lightweight governance.
- [ ] `OSS-004` Add bug, feature, packaging, rendering, translation, and theme
  issue templates plus a pull request template.
- [ ] `OSS-005` Add changelog and semantic-versioning policy.
- [ ] `OSS-006` Add a roadmap that links to this backlog without promising dates.
- [ ] `OSS-007` Add a documentation synchronization checklist for README,
  English manual, French manual, CLI help, and skill.
- [ ] `OSS-008` Replace unverified blanket dependency-license claims with a
  verifiable notice-generation plan.

Acceptance:

- A new contributor can reproduce development setup and understand acceptance
  requirements without private knowledge.
- Security reports and theme contributions have clear channels.

## Lot 1D — Product identity availability research

Owner: identity research agent
Execution: research can run after G0; no product identity decision before human gate
Files: research report only

- [ ] `BRD-001` Score 5–10 candidates for distinction, clarity, EN/FR speech,
  CLI suitability, search intent, and community fit.
- [ ] `BRD-002` Include `LibreMark PDF` in a shortlist of three, not as an
  automatically approved choice.
- [ ] `BRD-003` Check web/search, GitHub, PyPI, winget, Scoop, Homebrew, Linux
  package registries, relevant domains, and social handles.
- [ ] `BRD-004` Perform preliminary INPI/EUIPO/USPTO collision research and state
  that it is not legal advice.
- [ ] `BRD-005` Present three icon directions at 16, 32, 128, and 512 pixels.
- [x] `BRD-006` Define a future compatibility policy for command aliases,
  configuration, package, binary, skill, resource paths, documentation, and
  redirects. Evidence:
  [`ADR-008-PRODUCT-IDENTITY.md`](ADR-008-PRODUCT-IDENTITY.md).

Human gate G-Brand:

- The owner explicitly approves a name, icon direction, and identity plan.
- No identity decision is merged merely because automated searches found no
  collision.

## Gate G1 — Foundation approval

G1 passes when:

- the renderer spike decisions are approved;
- clean dependency installation and pure CI tests work;
- community/security policies exist;
- the locked target engine and font licenses are recorded;
- unresolved architecture questions have explicit owners.

## Lot 2A — Deterministic and safe core

Owner: renderer/core agent
Execution: serial owner of `libremark_pdf/core.py`
Files: core, core tests, renderer fixtures

- [ ] `REN-001` Add a versioned `RenderProfile` and deterministic fingerprint.
- [ ] `REN-002` Pass a file base directory through the public conversion API.
- [ ] `REN-003` Resolve, validate, and embed supported local resources.
- [ ] `REN-004` Deny external network requests and block service workers.
- [ ] `REN-005` Enforce the approved raw HTML/JavaScript policy.
- [ ] `REN-006` Bundle and await approved fonts in content and header/footer.
- [ ] `REN-007` Fix locale, time zone, media mode, paper settings, and renderer
  timeouts through the profile.
- [ ] `REN-008` Preflight batch output plans; reject duplicate destinations and
  input/output equality.
- [ ] `REN-009` Write PDFs atomically and clean temporary output on failure.
- [ ] `REN-010` Reuse Playwright/browser resources safely across a batch.
- [ ] `REN-011` Preserve actionable underlying browser/resource errors and add
  stable error codes.
- [ ] `REN-012` Correct title entity handling and header/footer geometric centering.
- [ ] `REN-013` Restrict emoji substitution to text nodes and preserve accessible
  alternative text.
- [ ] `REN-014` Enable tagged PDFs and outlines when supported by the locked engine.
- [ ] `REN-015` Test malformed UTF-8, empty/large input, invalid CSS, missing
  resources, forbidden URLs, non-writable destinations, and cleanup.
- [ ] `REN-016` Document the supported Markdown dialect and compatibility policy.

Acceptance:

- The core test suite covers every task above and passes in a clean locked
  environment.
- A batch cannot overwrite another planned output or leave a partial PDF.
- Network-observation tests record zero runtime requests by default.
- All front ends can consume the same stable public core API.

## Lot 2B — Visual and structural regression harness

Owner: QA/render-comparison agent
Execution: may develop fixture tooling in parallel; integrate after core profile

- [ ] `VIS-001` Create at least 30 lightweight canonical Markdown fixtures.
- [ ] `VIS-002` Store hashes for Markdown, CSS, fonts, images, and expected
  render-profile fingerprints.
- [ ] `VIS-003` Compare canonical pre-render HTML exactly.
- [ ] `VIS-004` Rasterize with a pinned PDFium version at 144 DPI.
- [ ] `VIS-005` Compare page dimensions, count, text, links, images, SSIM, changed
  pixels, and contiguous changed regions.
- [ ] `VIS-006` Generate human-readable page-by-page diff reports.
- [ ] `VIS-007` Require explicit reviewed golden updates.
- [ ] `VIS-008` Run the harness on native Windows and at least one second OS.
- [ ] `VIS-009` Extend the matrix only when Linux/macOS artifacts become candidates.

Acceptance:

- CI fails above frozen thresholds and retains actionable diff artifacts.
- Semantic/pagination differences fail even when raster metrics pass.
- Golden regeneration cannot happen as an incidental test side effect.

## Gate G2 — Core contract freeze

G2 passes when deterministic core, offline security, output integrity, and the
comparison harness are green. The orchestrator then versions and freezes the
core API required by CLI, GUI, themes, and packaging.

## Lot 3A — CLI and agent contract

Owner: CLI agent
Execution: parallel with Lots 3B–3F after G2
Files: CLI, package dispatch, skill, CLI tests

- [ ] `CLI-001` Add real subprocess tests for stdout, stderr, JSON, and exit code.
- [ ] `CLI-002` Make validation errors JSON when `--json` is requested, with no
  stray stdout noise.
- [ ] `CLI-003` Cover partial batch failures, collision errors, spaces, Unicode,
  missing CSS/resources, and non-writable output.
- [ ] `CLI-004` Add `--version` with application, profile, Playwright, and Chromium.
- [ ] `CLI-005` Add documented explicit controls for no header/footer, theme,
  safe compatibility modes, and overwrite policy as approved.
- [ ] `CLI-006` Evaluate a read-only `doctor` command for bundled-resource and
  browser diagnostics.
- [ ] `CLI-007` Keep `SKILL.md`, CLI help, JSON schema, and manuals synchronized.
- [ ] `CLI-008` Preserve the old command alias through any approved rename window.

Acceptance:

- All CLI paths are non-interactive and machine-parseable as documented.
- Exit 0 occurs only on complete requested success.
- The official console artifact passes the same tests outside the repository.

## Lot 3B — Desktop UX, accessibility, and i18n

Owner: GUI agent
Execution: parallel after G2
Files: GUI, i18n, GUI/i18n tests

- [ ] `GUI-001` Make the window and file list scroll/resize correctly; fit and
  zoom preview within available space.
- [ ] `GUI-002` Add debounced preview generation and discard stale results.
- [ ] `GUI-003` Add per-file progress, current item, cancellation, and safe close.
- [ ] `GUI-004` Prevent incompatible concurrent operations and preserve status
  across language switching.
- [ ] `GUI-005` Add open-PDF/open-folder actions after success.
- [ ] `GUI-006` Present collision/overwrite decisions before conversion.
- [ ] `GUI-007` Add keyboard navigation, focus visibility, accessible labels,
  contrast review, and high-DPI tests where Tk permits.
- [ ] `GUI-008` Test import/launch with and without `tkinterdnd2`.
- [ ] `GUI-009` Test exact EN/FR key parity and `.format()` placeholders.
- [ ] `GUI-010` Keep every Tk operation on the main thread.

Acceptance:

- The nominal workflow is file drop/select, optional preview/theme, then convert.
- Long work never blocks the event loop.
- Large batches and previews remain operable at the minimum window size.

## Lot 3C — Community theme system

Owner: themes agent
Execution: parallel after G2
Files: theme package/validator, bundled themes, theme docs/tests

- [ ] `STY-001` Define manifest fields: identifier, version, name, author,
  SPDX license, renderer compatibility, CSS, assets, fonts, and hashes.
- [ ] `STY-002` Convert the approved existing default CSS to a stable `default@1`
  package or compatibility alias without silent visual change.
- [ ] `STY-003` Reject scripts, external URLs, path traversal, missing licenses,
  unsupported resources, and incompatible profiles.
- [ ] `STY-004` Install/update/remove local themes atomically without touching the
  default.
- [ ] `STY-005` Add theme list/show/select behavior to the shared core contract.
- [ ] `STY-006` Add GUI cards/previews and CLI selection through their owners.
- [ ] `STY-007` Add theme golden fixtures and contribution checks.
- [ ] `STY-008` Seed `github-clean`, `minimal`, `academic`, `business`,
  `print-economy`, and `accessible-large` only after default compatibility passes.

Acceptance:

- A third-party theme cannot trigger network access or escape its package.
- Every bundled/community theme has licenses and reproducible previews.

## Lot 3D — Official Windows x64 artifact

Owner: Windows packaging agent
Execution: parallel after G2; mandatory release lane
Files: Windows specs/scripts/workflows/validation docs

- [ ] `WIN-001` Resolve GUI/no-console versus CLI/stdout with separate reliable
  entry points or another proven design.
- [ ] `WIN-002` Bundle the exact browser, fonts, themes, icons, and native data.
- [ ] `WIN-003` Implement release and console-diagnostic build paths from the
  authoritative spec/configuration.
- [ ] `WIN-004` Build on a clean native Windows runner.
- [ ] `WIN-005` Test GUI, preview, CLI JSON, batch, and theme selection outside
  the repository in a path with spaces and Unicode.
- [ ] `WIN-006` Repeat with no Python, no Playwright cache, and network blocked.
- [ ] `WIN-007` Run the golden corpus and compare to the canonical baseline.
- [ ] `WIN-008` Sign with Authenticode when credentials are available; document
  a non-official unsigned candidate separately.
- [ ] `WIN-009` Record size, startup/conversion performance, AV observations,
  SHA-256, SBOM, and logs.

Acceptance:

- A user downloads and launches without installing Python or a browser.
- GUI and CLI contracts both pass on the exact candidate artifact.
- Unsigned artifacts are not called official signed releases.

## Lot 3E — Linux artifact (independent optional lane)

Owner: Linux packaging agent
Execution: parallel after G2; not a Windows release blocker

- [ ] `LNX-001` Define supported distributions, versions, CPU architectures, and
  system-library baseline.
- [ ] `LNX-002` Compare AppImage and portable tarball behavior.
- [ ] `LNX-003` Bundle renderer resources and document unavoidable host libraries.
- [ ] `LNX-004` Run external-path, no-Python, cache-empty, offline, GUI/CLI, and
  golden tests on the declared matrix.
- [ ] `LNX-005` Record FUSE and Chromium sandbox/dependency behavior honestly.

Acceptance:

- Only passing distributions are advertised.
- The user path and remaining system prerequisites are explicit.

## Lot 3F — macOS artifacts (future independent lane)

Owner: macOS packaging agent
Execution: after G2 and only with native build/test capacity

- [ ] `MAC-001` Define minimum macOS version and arm64/x86_64 strategy.
- [ ] `MAC-002` Build autonomous `.app` bundles with CLI access and all renderer
  resources.
- [ ] `MAC-003` Add icon, minimal entitlements, hardened runtime, nested Chromium
  signing, Developer ID signature, notarization, and stapling.
- [ ] `MAC-004` Test both architectures or an approved universal2 artifact on
  clean Macs without Python/cache/network.
- [ ] `MAC-005` Run Gatekeeper, GUI, CLI, preview, batch, and golden validation.

Acceptance:

- macOS is not listed as supported until clean-machine, signature, notarization,
  and render-equivalence evidence all pass.

## Gate G3 — Product candidate

G3 passes per platform, not globally. Windows G3 is mandatory first. A platform
candidate must pass its native end-to-end, offline, artifact-integrity, and
visual-equivalence checks.

## Lot 4A — Release and supply-chain automation

Owner: release/security agent

- [ ] `REL-001` Build candidates from immutable tags on native runners.
- [ ] `REL-002` Generate checksums, SPDX/CycloneDX SBOM, dependency/font notices,
  and build provenance.
- [ ] `REL-003` Verify signatures and notarization where applicable.
- [ ] `REL-004` Attach test, performance, offline, and visual-comparison reports.
- [ ] `REL-005` Publish direct artifacts and a machine-readable release manifest.
- [ ] `REL-006` Define rollback, compromised-release, and urgent Chromium-update
  procedures.
- [ ] `REL-007` Protect release workflows and credentials with least privilege.

## Lot 4B — User documentation and discoverability

Owner: documentation/discovery agent
Dependency: at least one passing official platform candidate

- [ ] `DOC-001` Replace source-build-first onboarding with direct platform
  downloads; keep source builds for contributors.
- [ ] `DOC-002` Synchronize README, EN/FR manuals, CLI help, skill, limitations,
  and privacy/resource policies.
- [ ] `DOC-003` Add screenshots, a short workflow demo, and representative PDFs.
- [ ] `DOC-004` Add a factual competitor/feature matrix and measurable claims.
- [ ] `DSC-001` Set repository description and topics for Markdown-to-PDF,
  offline, privacy, desktop, CLI, Python, and Playwright.
- [ ] `DSC-002` Publish a fast static landing page with direct downloads, no
  mandatory tracking, Open Graph, canonical URL, sitemap, and
  `SoftwareApplication` structured data.
- [ ] `DSC-003` Publish pages targeting README-to-PDF, offline/private conversion,
  Windows Markdown-to-PDF, batch conversion, CLI, and agent use.
- [ ] `DSC-004` State only verified claims: no upload, no account, no paywall, no
  watermark, offline runtime, supported platforms, and release signatures.

## Lot 4C — Approved product identity

Owner: identity/integration agents
Dependency: human G-Brand; keep separate from renderer changes

- [ ] `BRD-101` Produce an original vector master and PNG/ICO/ICNS assets with
  documented rights.
- [ ] `BRD-102` Keep package, binaries, configuration, documentation, and
  resources aligned with the approved identity ADR.
- [ ] `BRD-103` Document and test the compatibility policy for any future
  public identity change.
- [ ] `BRD-104` Update agent skill discovery and direct download metadata.
- [ ] `BRD-105` Test clean installation, launch, and supported upgrade paths.

## Gate G4 — Official release readiness

For each advertised platform:

- all mandatory automated and manual checks pass on the exact signed artifact;
- no Python, browser install, user cache, account, email, or runtime network is
  required for the canonical workflow;
- checksums, SBOM, provenance, signatures, and evidence are published;
- direct-download documentation is correct;
- rendering equivalence passes the frozen contract;
- no P0/P1 release blocker remains open.

## Lot 5 — Independent final audit

Owner: auditor who did not implement the backlog
Execution: sequential after G4

- [ ] `AUD-101` Pin the audited commit/tag, environment, locks, renderer, fonts,
  fixture hashes, and artifact hashes.
- [ ] `AUD-102` Re-run the exact baseline scoring breakdown without changing
  weights or retroactively changing baseline points.
- [ ] `AUD-103` Run clean installation, unit, integration, subprocess CLI, GUI,
  i18n, security, offline, packaging, and visual-equivalence checks.
- [ ] `AUD-104` Exercise every advertised artifact outside the repository, from
  paths with spaces/Unicode, without Python/cache/network.
- [ ] `AUD-105` Publish baseline, final score, delta per criterion, evidence,
  failures, unverified items, and residual risks.
- [ ] `AUD-106` Convert every remaining gap into a versioned follow-up backlog.

Final acceptance:

- The audit is independently reproducible.
- A high score does not override a failed mandatory release gate.
- The unchanged baseline remains available beside the final report.
