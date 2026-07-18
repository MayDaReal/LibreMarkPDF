# LibreMark PDF refactoring plan

Status: **proposed — implementation requires an explicit owner go**

Baseline commit: `105028c9b05df36f4b6c526f908eef153afa1086`

This document is the execution plan for modularizing the canonical rendering
engine and desktop adapter. It stops when the existing GUI is structurally
ready for a separate UI/UX improvement project. Visual redesign, new widgets,
new dialogs, and other user-experience changes are deliberately excluded.

## 1. Objectives

- Keep `libremark_pdf.core` as the stable public API used by the CLI, desktop
  application, agent skill, tests, and external callers.
- Move the implementation behind that facade into cohesive internal modules.
- Keep Chromium as the only production PDF renderer.
- Separate toolkit-independent desktop behavior from the Tk implementation.
- Make a future desktop technology experiment possible without copying
  conversion or rendering logic.
- Reduce file size and coupling without changing observable behavior.
- Perform the migration domain by domain, with a separately reviewable commit
  and evidence for every lot.

Indicative size targets, not reasons to split cohesive code artificially:

- `libremark_pdf/core.py`: approximately 100–200 lines;
- normal internal module: preferably no more than 350 lines;
- review required when a module exceeds 400 lines;
- one clear responsibility per module.

## 2. Explicitly out of scope

- UI/UX redesign, colors, spacing, typography, visual identity, or layout
  modernization;
- replacement of native Tk message boxes;
- new user-visible wording or workflows;
- a Qt, Toga, webview, Electron, or other alternate GUI implementation;
- a second PDF renderer or a public renderer plug-in system;
- rendering-profile, CSS, font, margin, pagination, or golden changes;
- CLI, JSON, skill, or manual contract changes;
- dependency additions;
- packaging or native-artifact redesign;
- golden regeneration;
- G2 remediation or closure;
- macOS or Linux distribution work;
- Windows artifact production, signing, upload, publication, or pushing.

The separate G2 `23-unicode` PDFium limitation remains a known cross-gate
limitation. This refactoring neither reopens nor resolves G2.

## 3. Immutable safeguards

- Python 3.9 syntax remains mandatory.
- Runtime conversion remains local-first and performs no download.
- Chromium remains pinned and is never fetched at runtime.
- Browser failures remain actionable.
- Network access, JavaScript, active HTML, CSS resources, traversal, resource
  limits, and trusted-static HTML retain their current policies.
- Batch conversion returns exactly one result per input and continues after
  independent failures.
- Existing output, collision, and atomic-publication policies remain unchanged.
- Every Tk call runs on the main thread.
- GUI startup continues to work without `tkinterdnd2`.
- Default rendering and `default@1` remain exactly compatible.
- Goldens never update as a normal test or refactoring side effect.
- `docs/project-reliability/BASELINE_AUDIT.md` is never edited or staged.
- `docs/project-reliability/archive/g1/` remains immutable.
- The unrelated deletion of
  `docs/project-reliability/G2_WINDOWS_EXECUTION_PROMPT.md` is preserved and
  never staged, restored, or included in a refactoring commit.
- No push is performed.

## 4. Architecture decision required before implementation

The current rule that conversion and rendering logic belongs only in
`libremark_pdf/core.py` must be interpreted as an API-boundary rule:

> `libremark_pdf/core.py` is the only public engine facade. The canonical
> implementation may live in the private `libremark_pdf/engine/` package.
> Adapters call the facade and never implement or select another renderer.

Owner approval of this plan is approval of that internal interpretation. It
does not authorize a second renderer or a change to public rendering behavior.

## 5. Target source layout

```text
libremark_pdf/
├── core.py                         # stable public engine facade
├── engine/
│   ├── __init__.py                 # private package marker; no public facade
│   ├── contracts.py                # errors and shared value objects
│   ├── resources.py                # paths, hashes, fonts, icons, local images
│   ├── document.py                 # Markdown, safe HTML, CSS, profile, templates
│   ├── themes.py                   # theme validation and atomic lifecycle
│   ├── chromium.py                 # locked Chromium session and atomic PDF
│   ├── jobs.py                     # single-file and batch use cases
│   └── preview.py                  # reusable preview and PDFium rasterization
├── gui.py                          # stable desktop entry point
├── i18n.py                         # compatibility facade if still required
└── desktop/
    ├── __init__.py
    ├── contracts.py                # toolkit-neutral requests/events/results
    ├── services.py                 # workers and native-path services
    ├── i18n.py                     # desktop translation and persistence logic
    └── tk/
        ├── __init__.py
        ├── app.py                  # lifecycle and main-thread dispatch
        ├── layout.py               # existing widget construction
        ├── inputs.py               # files and conversion options
        ├── preview.py              # existing preview interaction
        ├── conversion.py           # existing batch interaction
        └── dialogs.py              # existing dialog calls behind one boundary
```

The final filenames may be adjusted during a lot when the dependency analysis
shows a clearer boundary. Such a change must be recorded in this document
before implementation.

No empty `desktop/qt/`, `desktop/webview/`, or experimental implementation is
created. A future technology spike may add one only when it has a concrete
owner and acceptance criteria.

## 6. Dependency direction

```text
engine.contracts
      ↓
engine.resources ─────────────┐
      ↓                       │
engine.themes                 │
      ↓                       │
engine.document               │
      ↓                       │
engine.chromium               │
      ↓                       │
engine.jobs / engine.preview ─┘
      ↓
core facade
      ↓
desktop.services
      ↓
desktop.tk
      ↓
gui entry point
```

Rules:

- Internal engine modules may not import CLI, GUI, desktop, or i18n modules.
- Desktop services import only the public `core` facade, not `engine`.
- Tk modules import desktop contracts/services and public core value objects
  only where translating user input requires them.
- CLI continues to import only `core`.
- `core.py` performs no toolkit work.
- `engine/__init__.py` does not become an alternate public API.
- Circular imports are not accepted; shared value objects move downward into
  `engine.contracts`.
- Test doubles are internal injection seams, not alternate production
  renderers.

## 7. Public compatibility inventory

Before moving implementation, the following current non-private names must be
classified and locked by tests. Names used by adapters or documented behavior
remain available from `libremark_pdf.core` with compatible signatures and
semantics:

- `ConversionError`;
- `HeaderFooterConfig`;
- `RenderProfile`;
- `RenderDocument`;
- `BatchPlan`;
- `DEFAULT_PROFILE_VERSION`;
- `DEFAULT_THEME_ID`;
- `DEFAULT_CSS_PATH`;
- `FONTS_DIR`, `ICONS_DIR`, and `BROWSERS_DIR`;
- `resource_path`;
- `renderer_identity`;
- `error_code`;
- `markdown_to_html`;
- `embed_local_resources`;
- `extract_title`;
- `build_header_template`;
- `build_footer_template`;
- `build_full_html`;
- `resolve_render_date`;
- `prepare_render_document`;
- `render_profile_for_options`;
- `convert_markdown_text_to_pdf`;
- `convert_markdown_to_pdf`;
- `plan_batch_outputs`;
- `convert_batch`;
- `PreviewSession`;
- `render_preview_png`;
- `ThemeInfo`;
- `validate_theme_package`;
- `list_themes`;
- `show_theme`;
- `install_theme`;
- `remove_theme`;
- `resolve_theme_css`.

Private names currently patched by tests, including `_BrowserRenderer`,
`_render_pdf`, font helpers, and module imports such as `core.os`, are not
automatically public contracts. Their tests must be redirected to the owning
internal module or replaced with an explicit internal injection seam. Public
behavior must remain covered throughout that cleanup.

Class re-exports must preserve object identity. Exception handling must not
create two different `ConversionError` classes.

## 8. Execution protocol for every lot

Each implementation lot follows this sequence:

1. Confirm `git status --short --branch` and `git rev-parse HEAD`.
2. Confirm the unrelated deleted file is still the only unrelated state.
3. Mark the lot `in progress` in this file.
4. State the exact owned files and observable no-change criteria.
5. Add or adjust characterization tests before moving behavior where needed.
6. Move one domain without opportunistic cleanup.
7. Run the focused tests.
8. Run Python 3.9 compilation checks.
9. Run the full suite when the focused tests pass.
10. Run `git diff --check`.
11. Inspect the diff for rendering inputs, resource hashes, translations,
    packaging collection, generated files, and accidental golden changes.
12. Record commands, exit codes, risks, and any unverified item.
13. Create one small signed commit only if the configured signing identity
    succeeds.
14. Stop for review when a public behavior, renderer input, or dependency
    discrepancy is found.

No failed signed commit is replaced with an unsigned commit without owner
approval.

## 9. Lot tracker

States: `not started`, `in progress`, `blocked`, `completed`.

| Lot | Domain | State | Dependency |
| --- | --- | --- | --- |
| R00 | Baseline and characterization | not started | owner go |
| R01 | Engine package and contracts | not started | R00 |
| R02 | Theme domain | not started | R01 |
| R03 | Resource domain | not started | R02 |
| R04 | Document and render-profile domain | not started | R03 |
| R05 | Chromium and atomic-output domain | not started | R04 |
| R06 | Conversion jobs and batch domain | not started | R05 |
| R07 | Preview domain | not started | R06 |
| R08 | Core facade stabilization | not started | R07 |
| R09 | Desktop contracts and services | not started | R08 |
| R10 | Tk package migration | not started | R09 |
| R11 | Dialog boundary and desktop cleanup | not started | R10 |
| R12 | Final refactoring validation | not started | R11 |

## 10. Engine lots

### R00 — Baseline and characterization

Owner: integration/core owner

Owned files:

- `refactoring.md`;
- focused contract tests only.

Purpose:

- Freeze the public API surface before relocating implementation.
- Record representative deterministic outputs for comparison without updating
  approved goldens.
- Identify current private monkeypatch points and packaging discovery behavior.

Before/after observable behavior:

- No production behavior or source layout changes.

Required checks:

- public symbol presence and signature inspection;
- `RenderProfile.canonical_json()` and fingerprint equality for fixed inputs;
- exact `prepare_render_document()` HTML equality for fixed inputs;
- default theme alias equality;
- error-code and batch-result schema equality;
- import and launch-path checks with and without optional drag-and-drop;
- existing preview-session reuse tests.

Evidence:

- initial commit and status;
- focused and full-suite commands with exit codes;
- Python, Playwright, Chromium, and render-profile identities;
- list of private patch points that need migration.

Exit criterion:

- Characterization is sufficient to detect a facade, rendering-input, error,
  batch, preview, or packaging regression in later lots.

Residual risk:

- Characterization cannot replace native Windows candidate validation.

Next dependency: R01.

### R01 — Engine package and contracts

Owner: core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/__init__.py`;
- `libremark_pdf/engine/contracts.py`;
- contract tests.

Purpose:

- Create the private engine boundary.
- Move only shared exceptions and value objects needed to prevent later import
  cycles.

Before behavior:

- Value objects and exceptions are defined directly in `core.py`.

After behavior:

- They are defined once in `engine.contracts` and re-exported by `core`.
- Existing `core` imports, construction, equality, and exception catches work
  unchanged.

Required checks:

- public class identity;
- dataclass defaults and mutability;
- header/footer default and `none()` behavior;
- result/error-code compatibility;
- Python 3.9 compilation.

Forbidden in this lot:

- theme, Markdown, renderer, batch, or preview moves;
- signature or default-value changes.

Exit criterion:

- One canonical definition exists for each shared contract and no circular
  import is introduced.

Next dependency: R02.

### R02 — Theme domain

Owner: theme/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/themes.py`;
- `tests/test_themes.py`;
- theme-related contract tests.

Purpose:

- Extract manifest validation, local registry behavior, and atomic theme
  lifecycle as the first complete functional domain.

Before behavior:

- Theme implementation occupies the middle of `core.py`.

After behavior:

- `engine.themes` owns implementation.
- `core` exposes the same theme API.

Required checks:

- `default@1` exact alias;
- manifest hashes and licences;
- remote URL, script, traversal, symbolic-link, undeclared-file, and profile
  rejection;
- atomic install/update/remove and failed-update restoration;
- Unicode and space-containing theme paths;
- no user theme directory is touched by tests.

Forbidden in this lot:

- CSS rendering changes;
- manifest schema changes;
- new themes or golden updates.

Exit criterion:

- Theme tests and the full suite pass with identical default inputs.

Next dependency: R03.

### R03 — Resource domain

Owner: resource-security/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/resources.py`;
- resource-policy tests.

Purpose:

- Extract frozen resource resolution, renderer identities, hashes, fonts,
  icons, image validation, and local-resource embedding.

Before/after observable behavior:

- Source, installed-wheel, and `sys._MEIPASS` resolution remain identical.
- Browser-path environment preference remains identical.
- Accepted resources produce the same data URIs.
- Rejected resources retain stable codes and actionable messages.

Required checks:

- resource resolution in all three layouts;
- exact font/icon/CSS hashes;
- MIME signatures and size/count/total limits;
- data URI validation;
- traversal, symlink, missing file, active SVG, URL, and malformed image
  rejection;
- emoji substitution remains unchanged;
- zero network observation in real rendering tests.

Special review:

- Import-time `PLAYWRIGHT_BROWSERS_PATH` behavior must not move to a point where
  it executes later or differently.
- Caches must remain process-local and must not introduce mutable cross-job
  state beyond the current behavior.

Exit criterion:

- Frozen and source resource behavior is unchanged and packaging tests discover
  all required modules/resources.

Next dependency: R04.

### R04 — Document and render-profile domain

Owner: deterministic-document/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/document.py`;
- Markdown, template, profile, and deterministic-core tests.

Purpose:

- Extract Markdown conversion, safe/trusted-static policy, CSS resolution,
  render date, templates, full HTML, profile construction, and document
  preparation.

Before/after observable behavior:

- Fixed inputs produce exact canonical JSON, fingerprint, and full HTML.
- Header/footer templates remain byte-for-byte equal for fixed inputs.

Required checks:

- Markdown extensions;
- raw HTML and CSS security;
- title extraction and entity handling;
- supported header/footer tokens and escaping;
- fixed-date and invalid-date behavior;
- default/custom/theme CSS resolution;
- exact margins and profile payload;
- exact prepared HTML and fingerprint;
- canonical fixtures compared without regenerating expectations.

Forbidden in this lot:

- renderer launch or PDF-output changes;
- formatting or template cleanup that changes bytes;
- security-policy changes.

Exit criterion:

- The deterministic pre-render boundary is exactly equivalent.

Next dependency: R05.

### R05 — Chromium and atomic-output domain

Owner: renderer/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/chromium.py`;
- renderer and atomic-output tests.

Purpose:

- Extract the single locked Chromium implementation and atomic PDF publication.

Before/after observable behavior:

- Same browser launch flags, context, locale, timezone, color scheme, media,
  A4 settings, margins, headers/footers, tagging, outline, timeout, and
  network-denial behavior.
- Existing output remains protected on every failure.

Required checks:

- missing dependency/browser actionable errors;
- exact browser launch arguments;
- JavaScript/service-worker restrictions;
- request interception and zero observed requests;
- PDF options;
- isolated context closure;
- atomic temporary creation, validation, replacement, cleanup, and previous
  output preservation;
- real Chromium focused conversion.

Design restriction:

- A narrow internal renderer-session protocol or factory may support tests and
  reuse, but Chromium remains the only production implementation.
- No public renderer selection option is introduced.

Exit criterion:

- Real conversions pass and renderer inputs are unchanged.

Next dependency: R06.

### R06 — Conversion jobs and batch domain

Owner: conversion/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/jobs.py`;
- conversion and batch tests.

Purpose:

- Extract text conversion, file input, output planning, single conversion, and
  batch orchestration.

Before/after observable behavior:

- Public signatures, defaults, paths, errors, cancellation, progress, and
  result dictionaries remain compatible.

Required checks:

- UTF-8 and size validation;
- missing/unreadable input;
- default and explicit outputs;
- input/output identity;
- duplicate destinations and existing outputs;
- per-item continuation;
- one resolved date per batch;
- one browser session per eligible batch;
- cancellation before launch and between items;
- presentation callback failures cannot change results;
- clean deterministic CLI JSON subprocess tests.

Exit criterion:

- CLI and GUI services continue to consume only `core`, and batch invariants
  pass unchanged.

Next dependency: R07.

### R07 — Preview domain

Owner: preview/core owner

Owned files:

- `libremark_pdf/core.py`;
- `libremark_pdf/engine/preview.py`;
- preview tests and existing performance evidence.

Purpose:

- Extract PDFium rasterization and the reusable preview session.

Before/after observable behavior:

- Same PNG content for fixed same-platform inputs.
- Header/footer-only changes continue to reuse the loaded page.
- Failed pages are not retained as trusted reusable state.

Required checks:

- PNG signature and dimensions;
- page reload only when visual document content changes;
- header/footer template updates without unnecessary `set_content`;
- required preview-template fonts;
- session/context cleanup;
- missing PDFium actionable error;
- measured initial and repeated preview timings;
- pixel comparison for representative fixed inputs.

Performance guard:

- No material regression from the retained repeated-preview measurements.
- A slowdown requires diagnosis; it is not accepted as a refactoring cost.

Exit criterion:

- Preview correctness, reuse, cleanup, and performance are preserved.

Next dependency: R08.

### R08 — Core facade stabilization

Owner: integration/core owner

Owned files:

- `libremark_pdf/core.py`;
- engine package exports;
- core contract tests;
- architecture documentation.

Purpose:

- Reduce `core.py` to the authoritative documented facade.
- Remove obsolete compatibility aliases only when they are private, unused,
  and covered through the owning module.

Before/after observable behavior:

- All classified public imports and calls remain compatible.

Required checks:

- `core` public inventory;
- signatures and defaults;
- no adapter imports `engine`;
- no internal engine import points upward;
- no duplicate exception/value-object definitions;
- wheel and PyInstaller module discovery;
- CLI, GUI, theme, preview, and full suites.

Exit criterion:

- `core.py` is a small stable facade and every engine domain has one owner.

Next dependency: R09.

## 11. Desktop lots

### R09 — Desktop contracts and services

Owner: desktop architecture owner

Owned files:

- `libremark_pdf/desktop_services.py`;
- `libremark_pdf/desktop/__init__.py`;
- `libremark_pdf/desktop/contracts.py`;
- `libremark_pdf/desktop/services.py`;
- desktop service tests.

Purpose:

- Move toolkit-independent work behind the `desktop` package.
- Replace unstructured worker tuples with typed internal requests/events where
  this can be done without changing visible behavior.

Before behavior:

- Desktop services live at package root and queues carry positional tuples.

After behavior:

- `desktop.services` owns preview, conversion, and native-path operations.
- A temporary root compatibility facade may re-export existing service names.
- Services contain no Tk or Pillow UI objects.

Required checks:

- service module imports without Tk;
- worker uses only public `core`;
- latest-preview request coalescing;
- conversion progress and terminal events;
- worker exception isolation;
- native path commands;
- injectable services remain usable by test and future adapters;
- no background thread invokes Tk.

Exit criterion:

- Desktop work can be exercised without constructing a Tk root.

Next dependency: R10.

### R10 — Tk package migration

Owner: Tk desktop owner

Owned files:

- `libremark_pdf/gui.py`;
- current `gui_*.py` modules;
- `libremark_pdf/desktop/tk/`;
- GUI tests.

Purpose:

- Move the existing Tk implementation into one technology-specific package
  without changing its appearance or workflow.

Mapping:

- `gui.py` lifecycle → `desktop/tk/app.py`;
- `gui_layout.py` → `desktop/tk/layout.py`;
- `gui_inputs.py` → `desktop/tk/inputs.py`;
- `gui_preview.py` → `desktop/tk/preview.py`;
- `gui_conversion.py` → `desktop/tk/conversion.py`;
- root `gui.py` becomes the stable launch facade.

Before/after observable behavior:

- Same window, widgets, ordering, labels, keyboard bindings, preview,
  conversion, cancellation, close behavior, and optional drag-and-drop.

Required checks:

- import and startup with/without `tkinterdnd2`;
- injected desktop services;
- main-thread Tk enforcement;
- queue polling and stale preview discard;
- safe close while idle, previewing, and converting;
- operation-control disabling/restoration;
- EN/FR retranslation;
- packaging entry-point imports.

Forbidden in this lot:

- widget replacement;
- layout, spacing, color, font, or message changes;
- accessibility redesign beyond preserving existing behavior.

Exit criterion:

- Root GUI modules are facades or removed safely, and the Tk implementation is
  isolated under `desktop/tk`.

Next dependency: R11.

### R11 — Dialog boundary and desktop cleanup

Owner: Tk desktop owner

Owned files:

- `libremark_pdf/desktop/tk/dialogs.py`;
- Tk modules that currently call `messagebox` or file dialogs;
- focused GUI tests.

Purpose:

- Centralize existing dialogs behind an injectable Tk dialog boundary.
- Prepare, but do not implement, the later modern-dialog/UI/UX project.

Before behavior:

- Message-box calls are distributed across lifecycle and conversion modules.

After behavior:

- Existing native dialogs are invoked through one boundary.
- Their titles, messages, decisions, and visible formatting remain unchanged.

Required checks:

- no-files error;
- invalid options;
- collision continuation;
- overwrite yes/no/cancel mapping;
- conversion failure details;
- open-path errors;
- all EN/FR placeholders;
- test operation without showing real dialogs.

Forbidden in this lot:

- custom modal windows;
- message rewriting or new formatting;
- new notification components;
- altered decision semantics.

Exit criterion:

- The later UI/UX project can replace dialog presentation without modifying
  conversion, desktop services, or operation state.

Next dependency: R12.

### R12 — Final refactoring validation

Owner: integration owner

Owned files:

- tests and architecture/refactoring documentation only;
- production fixes only when a validation defect is directly attributable to
  the refactoring.

Purpose:

- Prove that the complete modular layout preserves the accepted behavior and is
  ready for native Windows candidate work and a separate UI/UX phase.

Required validation:

- focused engine-domain suites;
- focused desktop/i18n suites;
- full `unittest` suite;
- Python 3.9 compilation;
- CLI help, version, JSON success, JSON error, and partial batch;
- GUI import/startup smoke with and without optional drag-and-drop;
- preview correctness and repeated-preview performance;
- real conversion and zero observed network requests;
- canonical corpus comparison without golden updates;
- packaging collection tests;
- `git diff --check`;
- exact final status and commit identity.

Review checklist:

- no renderer/profile/resource hash drift;
- no semantic, visual, pagination, or output-policy drift;
- no new dependency;
- no adapter imports `engine`;
- no Tk in desktop services;
- no generated artifacts or caches staged;
- baseline and G1 archive untouched;
- unrelated deletion preserved;
- macOS/Linux distribution work not started;
- no push.

Exit criterion:

- Every lot is reproducible and green.
- Remaining unverified native behavior is reported accurately.
- The source tree is ready for the separately approved UI/UX project.

## 12. Standard validation commands

Use the repository `venv-linux`; do not create repeated temporary virtual
environments when the existing environment is clean and compatible.

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
```

```bash
PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" \
venv-linux/bin/python -m unittest tests.test_core tests.test_themes -v
```

```bash
PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" \
venv-linux/bin/python -m unittest tests.test_gui tests.test_i18n -v
```

```bash
PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" \
venv-linux/bin/python -m unittest discover -s tests -v
```

```bash
venv-linux/bin/python -m libremark_pdf convert --help
venv-linux/bin/python -m libremark_pdf --version
```

The exact focused test module names will evolve with the domain split and must
be updated here in the lot that creates them.

Python 3.9 verification uses the already configured local Python 3.9
interpreter. It must compile every changed Python module without introducing a
new environment.

Native Windows validation is still required later for the exact Windows
candidate. Passing Linux source tests does not establish Windows G3.

## 13. Commit sequence

Expected commit subjects:

1. `Characterize the core facade`
2. `Extract core contracts`
3. `Extract the theme engine`
4. `Extract renderer resources`
5. `Extract document preparation`
6. `Extract the Chromium backend`
7. `Extract conversion jobs`
8. `Extract preview rendering`
9. `Stabilize the core facade`
10. `Extract desktop services`
11. `Move the Tk desktop adapter`
12. `Centralize desktop dialogs`
13. `Validate the modular architecture`

Subjects may be combined only when a lot is too small to remain independently
meaningful. Unrelated domains must not be combined.

## 14. Stop conditions

Stop the current lot and request an owner decision if:

- exact prepared HTML, profile fingerprint, resource hash, or default output
  changes;
- a visual or semantic comparison changes;
- a public signature/default must change;
- an additional dependency appears necessary;
- packaging requires a new strategy rather than module discovery metadata;
- an alternate renderer becomes necessary;
- a security or atomic-output test conflicts with the proposed boundary;
- Python 3.9 compatibility cannot be preserved;
- unrelated working-tree changes overlap an owned file;
- signed commit creation fails.

## 15. Handoff into the future UI/UX phase

This plan ends after R12. The next project may then evaluate:

- modern visual hierarchy and responsive layout;
- spacing, typography, colors, contrast, and high-DPI presentation;
- readable custom dialogs and expandable technical details;
- improved progress, notifications, empty states, and result presentation;
- formal keyboard, focus, and screen-reader review;
- comparative prototypes using another desktop toolkit.

None of those changes is authorized by this plan. They require separate
acceptance criteria, EN/FR review, screenshots or interaction evidence, and an
explicit owner go.
