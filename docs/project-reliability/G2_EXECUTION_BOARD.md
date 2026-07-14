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
| REN-001 | core owner | `libremark_pdf/core.py`, `tests/test_core.py` | G1 renderer lock | implicit render settings → versioned canonical profile/fingerprint | `python -m unittest tests.test_core` | two-process equal fingerprint | planned; renderer assets needed → REN-006 |
| REN-002 | core owner | core/tests | REN-001 | no explicit source base → stable conversion base | focused core tests | relative-resource proof | planned → REN-003 |
| REN-003 | core owner | core/tests | REN-002 | browser resolves unchecked URLs → validated embedded images | focused security tests | type/limit/traversal tests | planned → REN-004 |
| REN-004 | core owner | core/tests | REN-003 | requests unconstrained → zero observed requests | browser security tests | route/request log | planned → REN-005 |
| REN-005 | core owner | core/tests | ADR-004 | raw/active HTML passes → safe literal or approved static subset | focused security tests | active-content rejection tests | planned; public UI/CLI wording follows only as compatibility adaptation → REN-016 |
| REN-006 | core owner | core, resources, tests | approved G1 font evidence | system fonts → approved, hashed static fonts | resource/profile tests | font hashes and render evidence | blocked pending approved files being available locally → REN-007 |
| REN-007 | core owner | core/tests | REN-001, REN-006 | renderer defaults vary → profile-controlled settings/timeouts | profile tests | deterministic profile | planned → REN-016 |
| REN-008 | core owner | core/tests | core API | collisions overwrite → preflight per-input results | output-plan tests | duplicate/identity proof | planned → REN-009 |
| REN-009 | core owner | core/tests | REN-008 | direct write → atomic destination commit | atomic failure tests | no partial/temporary outputs | planned → REN-010 |
| REN-010 | core owner | core/tests | REN-009 | browser per input → safe batch reuse/cleanup | mocked/browser batch tests | lifecycle proof | planned → REN-011 |
| REN-011 | core owner | core/tests | REN-008 | ad hoc strings → stable core error codes | error tests | actionable code/message cases | planned → REN-015 |
| REN-012 | core owner | core/tests | core API | entity/title and flex centering defects → decoded title and 3-column centering | pure HTML tests | exact template/title tests | planned → REN-013 |
| REN-013 | core owner | core/tests | core API | HTML-wide emoji replacement → text-node-only replacement with alt | pure HTML tests | code/alt tests | planned → REN-014 |
| REN-014 | core owner | core/tests | locked Chromium | unverified accessibility → measured tagged/outline disposition | browser/PDF tests | engine measurement | planned; may remain incomplete only with measured limitation → REN-015 |
| REN-015 | core owner | core/tests | REN-003–011 | edge cases untested → bounded, coded failures | focused core tests | malformed/limit/permission tests | planned → REN-016 |
| REN-016 | core + docs owner | core, README/manuals/SKILL as needed | REN-001–015 | undocumented dialect/profile policy → frozen documented core contract | documentation + core tests | synchronized public wording | planned → G2 review |
| VIS-001 | comparison owner | `tests/fixtures/g2`, comparison tooling | core profile | no corpus → 30+ orthogonal fixtures | harness fixture test | manifest count/categories | planned → VIS-002 |
| VIS-002 | comparison owner | harness/manifest/tests | VIS-001, REN-006 | unhashed inputs → immutable manifest hashes | manifest validation | file/hash report | planned → VIS-003 |
| VIS-003 | comparison owner | harness/tests | REN-001 | no canonical HTML check → exact comparison | harness unit test | HTML mismatch failure | planned → VIS-004 |
| VIS-004 | comparison owner | harness/tests | pinned PDFium | ad hoc rasterization → 144-DPI PDFium | harness test | inspector version/DPI report | planned → VIS-005 |
| VIS-005 | comparison owner | harness/tests | VIS-003/004 | no structural metrics → strict structure plus frozen raster thresholds | harness metric tests | page report/diff | planned → VIS-006 |
| VIS-006 | comparison owner | harness/tests | VIS-005 | opaque failures → retained page diagnostics | failure-report test | report/diff paths | planned → VIS-007 |
| VIS-007 | comparison owner | update script/docs/tests | VIS-002 | tests can mutate expectations → explicit reviewed update only | no-mutation test | separate-command guard | planned → VIS-008 |
| VIS-008 | Windows + integration owner | evidence prompt/manifest/report | VIS-001–007 | G1 spike only → same-commit native corpus evidence | native Windows prompt | reviewed Windows archive | awaiting native environment → G2 decision |
| VIS-009 | platform owner | platform evidence | VIS-008 | optional platform matrix undefined → candidate-only extension | platform-specific | native candidate record | not applicable before candidate lanes |

Gate decision remains **not passed** until every mandatory row is accepted and
native Windows evidence for the exact candidate is reviewed.
