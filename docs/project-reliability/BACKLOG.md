# Active high-reliability backlog

Status: **Gate G1 passed on 2026-07-14; Gate G2 is next**
Historical G0/G1 state: [`archive/g1/BACKLOG.md`](archive/g1/BACKLOG.md)
Architecture: [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md)

This file is the canonical source for active task state, ownership,
dependencies, and gate criteria. Closed-gate commands and measurements belong
in the corresponding archive and must not be copied back here.

## Operating rules

- One integrator owns task acceptance and gates.
- Use separate worktrees for concurrent writers; serialize overlapping core,
  packaging, test, and documentation changes.
- A task is complete only with implementation, focused tests, synchronized
  documentation, and reproducible evidence.
- Preserve Python 3.9, the shared core, local-first runtime, and the accepted
  ADRs unless a superseding human-approved decision explicitly changes them.
- Do not change the frozen baseline or advertise an OS/architecture before its
  native artifact gate passes.
- Record detailed commands in a gate report; keep only state, owner, evidence
  link, risk, and next dependency here.

## Closed gates and carried work

G0 and G1 are closed. Their signed decision, negative renderer evidence,
Windows measurements, exact commands, manifests, and original program backlog
are indexed in [`archive/g1/`](archive/g1/README.md). The accepted G1 decisions
remain:

- Playwright 1.60.0 with Chromium/headless shell 148.0.7778.96 revision 1223;
- seven-file static Noto candidate and recorded OFL licenses;
- deny-all runtime network direction with local embedded resources;
- ADR-002 G1 thresholds plus the ADR-009 raster and ADR-010 PDFium-box G2
  amendments, and otherwise strict structural equality;
- zipped portable Windows directory as the primary distribution format.

These are architecture selections, not production implementation or official
artifact claims.

| Carried item | Owner | State / next dependency |
| --- | --- | --- |
| `QAS-001` installed-wheel resource layout | packaging + core | partial; resolve with `resource_path()` during Lot 2 and test source, wheel, and `sys._MEIPASS` |
| `SPIKE-PKG-001` exact windowed/console release candidate | Windows packaging | G1 direction accepted; complete under Lot 3D |
| Hosted CI/security URLs and repository settings | administrator + QAS | verify after publication; public security fallback already exists |
| `BRD-003`/`BRD-004` authoritative registry/legal research | identity owner + human adviser | incomplete; no approved identity change |
| `BRD-005` alternative multi-size icon evidence | identity owner | research-only and non-blocking; ADR-008 remains authoritative |

## Execution order

```text
Lot 2A deterministic core ─┐
                           ├─> G2 core contract freeze
Lot 2B comparison harness ─┘
                                  |
Lots 3A–3F product/platform work ─> G3 per-platform candidate
                                  |
Lots 4A–4C release readiness ─────> G4 per advertised platform
                                  |
Lot 5 independent audit
```

Parallel work is allowed only where file ownership does not overlap. Windows
x64 remains the first mandatory official lane; Linux and macOS are independent
future lanes.

## Lot 2A — Deterministic and safe core

Owner: renderer/core owner, serial owner of `libremark_pdf/core.py`

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
- [ ] `REN-012` Correct title entity handling and header/footer geometric
  centering.
- [ ] `REN-013` Restrict emoji substitution to text nodes and preserve
  accessible alternative text.
- [ ] `REN-014` Enable tagged PDFs and outlines when supported by the locked
  engine.
- [ ] `REN-015` Test malformed UTF-8, empty/large input, invalid CSS, missing
  resources, forbidden URLs, non-writable destinations, and cleanup.
- [ ] `REN-016` Document the supported Markdown dialect and compatibility
  policy.

Acceptance: all front ends consume one stable core API; batch output cannot
collide or leave partial files; default network-observation tests record zero
requests; the clean locked core suite passes.

## Lot 2B — Visual and structural regression harness

Owner: QA/render-comparison owner; tooling may develop separately and integrates
after the core profile exists.

- [ ] `VIS-001` Create at least 30 lightweight canonical Markdown fixtures.
- [ ] `VIS-002` Hash Markdown, CSS, fonts, images, and expected profile data.
- [ ] `VIS-003` Compare canonical pre-render HTML exactly.
- [ ] `VIS-004` Rasterize with pinned PDFium at 144 DPI.
- [ ] `VIS-005` Compare dimensions, pages, text, links, images, SSIM, changed
  pixels, and contiguous regions.
- [ ] `VIS-006` Generate actionable page-by-page diff reports.
- [ ] `VIS-007` Require an explicit reviewed golden update.
- [ ] `VIS-008` Run on native Windows and at least one second OS.
- [ ] `VIS-009` Extend the matrix only for candidate Linux/macOS artifacts.

Acceptance: semantic or pagination differences always fail; frozen visual
thresholds fail CI when exceeded; golden regeneration is never a test side
effect.

## Gate G2 — Core contract freeze

G2 passes when the deterministic core, offline security, output integrity, and
comparison harness are green. The integrator then versions and freezes the core
API consumed by CLI, GUI, themes, and packaging.

## Lot 3 — Product and native candidates

Lots 3A–3F may run in parallel only after G2 and with separate file ownership.

### 3A — CLI and agent contract

Owner: CLI/skill owner

- [ ] `CLI-001` Add subprocess tests for stdout, stderr, JSON, and exit status.
- [ ] `CLI-002` Return clean JSON for validation and conversion errors.
- [ ] `CLI-003` Cover partial batches, collisions, Unicode/spaces, resources,
  CSS, and permission failures.
- [ ] `CLI-004` Add `--version` with application and renderer/profile versions.
- [ ] `CLI-005` Expose only approved header/footer, theme, overwrite, and
  compatibility controls.
- [ ] `CLI-006` Evaluate a read-only bundled-resource/browser `doctor` command.
- [ ] `CLI-007` Synchronize `SKILL.md`, help, JSON schema, and manuals.
- [ ] `CLI-008` Preserve any approved legacy command alias.

Acceptance: every CLI path is non-interactive and machine-parseable; exit `0`
means complete success; the exact console artifact passes the same contract.

### 3B — Desktop UX, accessibility, and i18n

Owner: GUI/i18n owner

- [ ] `GUI-001` Make layout and preview responsive, scrollable, and zoomable.
- [ ] `GUI-002` Debounce preview and discard stale results.
- [ ] `GUI-003` Add progress, cancellation, and safe close.
- [ ] `GUI-004` Prevent incompatible operations and preserve localized status.
- [ ] `GUI-005` Add open-PDF/open-folder actions after success.
- [ ] `GUI-006` Present collision/overwrite decisions before conversion.
- [ ] `GUI-007` Review keyboard access, focus, labels, contrast, and high DPI.
- [ ] `GUI-008` Test with and without `tkinterdnd2`.
- [ ] `GUI-009` Test exact EN/FR keys and formatting placeholders.
- [ ] `GUI-010` Keep every Tk operation on the main thread.

Acceptance: the event loop stays responsive; large batches and previews remain
operable at minimum size; the nominal select/preview/convert workflow passes.

### 3C — Community theme system

Owner: theme owner

- [ ] `STY-001` Define the versioned manifest and hashes.
- [ ] `STY-002` Preserve the approved default as `default@1` or an exact alias.
- [ ] `STY-003` Reject scripts, remote URLs, traversal, missing licenses, and
  incompatible profiles.
- [ ] `STY-004` Install, update, and remove local themes atomically.
- [ ] `STY-005` Add core list/show/select behavior.
- [ ] `STY-006` Add GUI cards/previews and CLI selection through their owners.
- [ ] `STY-007` Add theme fixtures, goldens, and contribution checks.
- [ ] `STY-008` Seed additional themes only after default compatibility passes.

Acceptance: themes cannot access the network or escape their package; every
distributed theme has licenses and reproducible previews.

### 3D — Official Windows x64 artifact

Owner: Windows packaging owner; mandatory first release lane

- [ ] `WIN-001` Prove reliable GUI/no-console and CLI/stdout entry points.
- [ ] `WIN-002` Bundle exact browser, fonts, themes, icons, and native data.
- [ ] `WIN-003` Provide authoritative release and diagnostic builds.
- [ ] `WIN-004` Build on a clean native Windows runner.
- [ ] `WIN-005` Test GUI, preview, CLI JSON, batch, and themes outside the repo
  from Unicode and space-containing paths.
- [ ] `WIN-006` Repeat without Python, cache, or network.
- [ ] `WIN-007` Run the canonical golden corpus.
- [ ] `WIN-008` Sign with Authenticode when credentials exist; label unsigned
  candidates accurately.
- [ ] `WIN-009` Record size, performance, AV observations, hashes, SBOM, and logs.

Acceptance: the exact candidate needs no Python/browser installation and passes
both GUI and CLI contracts; unsigned candidates are not called official signed
releases.

### 3E/3F — Optional native lanes

Owner: native packaging owner for each explicitly activated lane

- [ ] `LNX-001` Define supported distributions, versions, architectures, and
  system-library baseline.
- [ ] `LNX-002` Compare AppImage and portable tarball behavior.
- [ ] `LNX-003` Bundle renderer resources and document required host libraries.
- [ ] `LNX-004` Run external-path, no-Python, cache-empty, offline, GUI/CLI, and
  golden tests on the declared matrix.
- [ ] `LNX-005` Record FUSE and Chromium sandbox/dependency behavior accurately.
- [ ] `MAC-001` Define the minimum macOS version and arm64/x86_64 strategy.
- [ ] `MAC-002` Build autonomous `.app` bundles with CLI access and all renderer
  resources.
- [ ] `MAC-003` Add minimal entitlements, hardened runtime, nested Chromium
  signing, Developer ID signature, notarization, and stapling.
- [ ] `MAC-004` Test each advertised architecture on clean Macs without Python,
  cache, or network.
- [ ] `MAC-005` Run Gatekeeper, GUI, CLI, preview, batch, and golden validation.

Acceptance: advertise only the exact distributions/architectures whose native
gate passes. These lanes do not block the first Windows release.

## Gate G3 — Product candidate

G3 passes per platform. A candidate must pass native end-to-end, offline,
artifact-integrity, and visual-equivalence checks. Windows G3 is mandatory
first.

## Lot 4 — Official release readiness

### 4A — Release and supply chain

Owner: release/security owner

- [ ] `REL-001` Build candidates from immutable tags on native runners.
- [ ] `REL-002` Generate checksums, SPDX/CycloneDX SBOM, dependency/font
  notices, and build provenance.
- [ ] `REL-003` Verify signatures and notarization where applicable.
- [ ] `REL-004` Attach test, performance, offline, and visual reports.
- [ ] `REL-005` Publish direct artifacts and a machine-readable manifest.
- [ ] `REL-006` Define rollback, compromised-release, and urgent Chromium-update
  procedures.
- [ ] `REL-007` Protect release workflows and credentials with least privilege.

### 4B — Documentation and discoverability

Owner: documentation/discovery owner; requires a passing platform candidate

- [ ] `DOC-001` Lead onboarding with direct platform downloads; keep source
  builds for contributors.
- [ ] `DOC-002` Synchronize README, EN/FR manuals, CLI help, skill, limitations,
  and privacy/resource policies.
- [ ] `DOC-003` Add reviewed screenshots, a short workflow demo, and samples.
- [ ] `DOC-004` Publish only factual, measurable comparison claims.
- [ ] `DSC-001` Configure repository description and relevant topics.
- [ ] `DSC-002` Publish a fast static landing page with direct downloads, no
  mandatory tracking, canonical metadata, sitemap, and structured data.
- [ ] `DSC-003` Add factual pages for offline/private, Windows, batch, CLI, and
  agent workflows.
- [ ] `DSC-004` State no-upload/account/paywall/watermark/network and platform
  claims only after their technical gates prove them.

### 4C — Approved product identity

Owner: identity/integration owner; keep separate from renderer changes

- [ ] `BRD-101` Maintain original editable assets and documented rights.
- [ ] `BRD-102` Keep package, binary, configuration, documentation, and resource
  paths aligned with ADR-008.
- [ ] `BRD-103` Document and test compatibility for any future identity change.
- [ ] `BRD-104` Update agent-skill discovery and direct-download metadata.
- [ ] `BRD-105` Test clean installation, launch, and supported upgrade paths.

## Gate G4 — Official release readiness

For each advertised platform, all mandatory checks must pass on the exact
artifact; the canonical workflow needs no Python, browser install, cache,
account, or runtime network; checksums, SBOM, provenance, signatures, and
evidence are published; direct-download documentation is accurate; visual
equivalence passes; and no P0/P1 blocker remains.

## Lot 5 — Independent final audit

Owner: auditor who did not implement the audited changes

- [ ] `AUD-101` Pin the audited commit/tag, environments, locks, renderer,
  fonts, fixtures, and artifact hashes.
- [ ] `AUD-102` Re-run the exact baseline breakdown without changing weights or
  historical points.
- [ ] `AUD-103` Run clean installation, unit, integration, subprocess CLI, GUI,
  i18n, security, offline, packaging, and visual checks.
- [ ] `AUD-104` Exercise every advertised artifact outside the repository from
  Unicode/space paths without Python, cache, or network.
- [ ] `AUD-105` Publish baseline, final score, delta, evidence, failures,
  unverified items, and residual risks.
- [ ] `AUD-106` Convert every remaining gap into a versioned follow-up backlog.

Final acceptance requires an independently reproducible audit. A numeric score
cannot override a failed mandatory release gate.
