# Gate G2 execution board

Status: **active**  
Integrator: **G2 integration owner**  
Baseline: `603acb34ca8ecc39e3d2c2a560fc367049b41ca7`  
Scope: Lot 2A deterministic/safe core and Lot 2B canonical regression harness.

This board is the active ownership record. Detailed commands, environment
facts, and results are recorded in `G2_GATE_REPORT.md`. G0/G1 are closed and
their archive is immutable.

| Task | Accountable owner | Owned files/directories | Dependencies | Before → after observable behavior | Focused command | Required evidence | State / risk / next dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REN-001 | core owner | `libremark_pdf/core.py`, `tests/test_core.py` | G1 renderer lock | implicit render settings → versioned canonical profile/fingerprint | `python -m unittest tests.test_core` | two-process equal fingerprint | in progress; equal two-process proof recorded, pending canonical harness → REN-006 |
| REN-002 | core owner | core/tests | REN-001 | no explicit source base → stable conversion base | focused core tests | relative-resource proof | in progress; source/wheel/_MEIPASS proof recorded → REN-003 |
| REN-003 | core owner | core/tests | REN-002 | browser resolves unchecked URLs → validated embedded images | focused security tests | type/limit/traversal tests | in progress; standard static SVG, SVG/data/link-escape and inline-CSS/fetch-attribute coverage recorded → REN-004 |
| REN-004 | core owner | core/tests | REN-003 | requests unconstrained → zero observed requests | browser security tests | route/request log | in progress; Linux locked-browser proof records zero safe/trusted-static requests; native Windows pending → REN-005 |
| REN-005 | core owner | core/tests | ADR-004 | raw/active HTML passes → safe literal or approved static subset | focused security tests | active-content rejection tests | in progress; inline CSS and fetch-capable attributes now rejected; public CLI/skill wording synchronized → REN-016 |
| REN-006 | core owner | core, resources, tests | approved G1 font evidence | system fonts → approved, hashed static fonts | resource/profile tests | font hashes and render evidence | in progress; exact G1 files/hashes embedded and packaged → REN-007 |
| REN-007 | core owner | core/tests | REN-001, REN-006 | renderer defaults vary → profile-controlled settings/timeouts | profile tests | deterministic profile | in progress; fixed locale/timezone/media/settings, browser PDF timeout limitation recorded → REN-016 |
| REN-008 | core owner | core/tests | core API | collisions overwrite → preflight per-input results | output-plan tests | duplicate/identity proof | in progress; duplicate/default overwrite coverage recorded → REN-009 |
| REN-009 | core owner | core/tests | REN-008 | direct write → atomic destination commit | atomic failure tests | no partial/temporary outputs | in progress; render, temporary-creation and replacement-failure cleanup/preservation proofs recorded; native permission coverage pending → REN-010 |
| REN-010 | core owner | core/tests | REN-009 | browser per input → safe batch reuse/cleanup | mocked/browser batch tests | lifecycle proof | in progress; one-browser mocked and real-batch evidence recorded → REN-011 |
| REN-011 | core owner | core/tests | REN-008 | ad hoc strings → stable core error codes | error tests | actionable code/message cases | in progress; renderer, temporary-output and replacement failures have stable codes; full edge-case matrix pending → REN-015 |
| REN-012 | core owner | core/tests | core API | entity/title and flex centering defects → decoded title and 3-column centering | pure HTML tests | exact template/title tests | in progress; title test exists, geometric rendering proof pending → REN-013 |
| REN-013 | core owner | core/tests | core API | HTML-wide emoji replacement → text-node-only replacement with alt | pure HTML tests | code/alt tests | in progress; code-literal and alternative-text proofs exist; native visual evidence remains → REN-014 |
| REN-014 | core owner | core/tests | locked Chromium | unverified accessibility → tagged PDF and outline requested and measured | browser/PDF test | `/StructTreeRoot` and `/Outlines` evidence | in progress; Linux locked-engine proof exists, native Windows confirmation remains → REN-015 |
| REN-015 | core owner | core/tests | REN-003–011 | edge cases untested → bounded, coded failures | focused core tests | malformed/limit/permission tests | in progress; Linux UTF-8/empty/limit/CSS and simulated destination proof recorded; native permission/browser failure cases remain → REN-016 |
| REN-016 | core + docs owner | core, README/manuals/SKILL as needed | REN-001–015 | undocumented dialect/profile policy → frozen documented core contract | documentation + core tests | synchronized public wording | in progress; current public contracts synchronized, final dialect disposition pending → G2 review |
| VIS-001 | comparison owner | `tests/fixtures/g2`, comparison tooling | core profile | no corpus → 31 orthogonal fixtures | `python -m unittest tests.test_g2_harness -v` | manifest count and category review | accepted on Linux; corpus includes multipage, PNG/JPEG/GIF, SVG, spaces/Unicode and duplicate-stem paths → VIS-008 |
| VIS-002 | comparison owner | harness/manifest/tests | VIS-001, REN-006 | unhashed inputs → immutable manifest hashes | harness unit test | Markdown/PDF/profile/hash report | accepted on Linux; approved expected data records Markdown, embedded-image, profile, CSS/font/icon and PDF hashes → VIS-008 |
| VIS-003 | comparison owner | harness/tests | REN-001 | no canonical HTML check → exact comparison | harness comparison test | HTML mismatch failure | accepted on Linux; reviewed expected canonical-HTML hashes compare exactly → VIS-008 |
| VIS-004 | comparison owner | harness/tests | pinned PDFium | ad hoc rasterization → 144-DPI PDFium | harness unit test | inspector version/DPI report | accepted on Linux; PDFium 5.11.0, 144 DPI and 34 reference rasters → VIS-008 |
| VIS-005 | comparison owner | harness/tests | VIS-003/004, ADR-009 | no structural metrics → strict structure plus owner-approved G2 raster thresholds | harness metric tests | page report/diff | approved `0.10%` connected-region ceiling recorded; regenerated expected data and same-commit cross-platform rerun pending → VIS-008 |
| VIS-006 | comparison owner | harness/tests | VIS-005 | opaque failures → retained page diagnostics | harness comparison test | report/diff paths | accepted on Linux; page-level report and retained failure diffs implemented → VIS-008 |
| VIS-007 | comparison owner | update script/docs/tests | VIS-002 | tests can mutate expectations → explicit reviewed update only | no-mutation test | separate-command guard | accepted on Linux; tag-backed MayDaReal review, source-evidence hash and separate writer verified → VIS-008 |
| VIS-008 | Windows + integration owner | Windows bundle, golden manifest, harness | VIS-001–007, ADR-009 | G1 spike only → same-commit native corpus evidence | canonical harness against reviewed goldens | Windows report/diffs | native Windows evidence received for `1822a7c`; raster metrics pass under ADR-009 but all 31 fixtures fail strict PDFium text-geometry equality → owner disposition required |
| VIS-009 | platform owner | platform evidence | VIS-008 | optional platform matrix undefined → candidate-only extension | platform-specific | native candidate record | not applicable before candidate lanes |

Gate decision remains **not passed** until every mandatory row is accepted and
native Windows evidence for the exact candidate is reviewed.
