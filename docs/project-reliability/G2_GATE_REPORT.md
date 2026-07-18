# Gate G2 report

Status: **active — no decision**  
Baseline commit: `603acb34ca8ecc39e3d2c2a560fc367049b41ca7`

## Initial custody

- `git status --short --branch`: `## main`
- `git rev-parse HEAD`: `603acb34ca8ecc39e3d2c2a560fc367049b41ca7`
- The local immutable `BASELINE_AUDIT.md` was read and was not modified.
- `archive/g1/` was read as historical evidence and was not modified.

Subsequent sections record exact commands, exit codes, artifacts, and task
dispositions as implementation evidence is obtained.

## Phase 1 characterization

Environment: Ubuntu 24.04.4-compatible container, Linux
`6.17.0-35-generic`, x86_64, system and `venv-linux` CPython `3.12.3`.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest discover -s tests -v` | 1 | 54 tests ran; three renderer-dependent tests failed because `resource_path("browsers")` selected a repository payload without `chrome-headless-shell`. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v` | 1 | 54 tests ran; three renderer-dependent tests failed because locked Chromium revision 1223 terminated at `sandbox_host_linux.cc:41` with `Operation not permitted`. |

The failures are retained as environment/product limitations. They do not
justify skipping or weakening renderer, network, output-integrity, or visual
tests. Browser-free tests passed in both runs.

| Command | Exit | Result |
| --- | ---: | --- |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` (outside the container sandbox) | 0 | all 54 baseline tests passed with locked cached Chromium revision 1223. |

This establishes that the preceding cached-browser failure is a sandbox
restriction, not a baseline product failure.

The approved static font evidence is locally available outside the repository
at `/tmp/libremark-g1-font-static-5264143/fonts/`; its presence and hashes must
be independently verified before any production resource copy. No fonts,
browsers, PDFs, caches, or generated output were added to Git.

## In-progress core increment

The seven G1-approved static font files and their four retained OFL records
were copied only after a local SHA-256 comparison against
`spikes/g1/font_candidates_static.json`; all seven hashes match the accepted
manifest. The core now embeds those files as data URIs, fixes the G1 integer
font-positioning renderer flag, neutralizes raw HTML by default, validates the
approved trusted-static subset, embeds validated local images, and publishes
PDFs atomically. This increment has not yet completed its required packaging,
GUI/manual synchronization, canonical harness, or Windows evidence.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestMarkdownConversion tests.test_core.TestDeterministicCoreContract tests.test_core.TestResourcePolicy tests.test_cli -v` | 0 | 19 focused core/security/CLI tests passed. |
| `venv-linux/bin/python -m ruff check libremark_pdf tests` | 1 | the declared Linux virtual environment does not contain Ruff; no linter result is claimed. |
| `venv-linux/bin/python -m unittest tests.test_core tests.test_cli -v` | 1 | expected environment failure: incomplete repository browser payload selected without explicit compatible browser path. |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_convert_markdown_text_to_pdf_creates_a_file -v'` | 0 | real locked Chromium conversion passed after allowing validated `data:` resources through the deny-network route. |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_render_preview_png_returns_valid_png_bytes -v'` | 0 | real Chromium/PDFium preview conversion passed. |

Failed experiment: the first all-resource route aborted `data:` requests as
though they were network traffic. This prevented the embedded font faces from
loading and stalled rendering. The route now permits only already validated
`data:` URIs and records/aborts every other request. This is retained as a
security-design correction, not treated as network evidence by itself.

## Incremental evidence — deterministic resources and trust boundary

The render profile now has canonical sorted JSON and a SHA-256 fingerprint over
the locked renderer inputs, fixed date, locale/timezone, render flags, margins,
resource limits, raw-HTML/network policy, static-font/icon hashes, and the
effective CSS hash. The same profile data is injected into canonical renderer
HTML. Safe mode literalizes raw HTML. The ADR-004 trusted-static mode rejects
active elements, event handlers, refreshes, `srcset`, `file:`/network sources,
and CSS resource loaders. Image inputs are constrained to local PNG/JPEG/GIF/
SVG or validated data URIs, including symlink containment, type signatures,
per-item/count/total limits, and static SVG inspection.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m pip install 'ruff==0.14.2'` | 0 | Declared test pin installed from the locally available package cache after the prior absence check. |
| `venv-linux/bin/python -m ruff check libremark_pdf tests` | 0 | `All checks passed!` |
| `venv-linux/bin/python -m unittest tests.test_core.TestMarkdownConversion tests.test_core.TestDeterministicCoreContract tests.test_core.TestResourcePolicy -v` | 0 | 20 focused safe-mode/resource/output tests passed. |
| `venv-linux/bin/python -m unittest tests.test_core.TestDeterministicCoreContract tests.test_core.TestResourcePolicy -v` | 0 | 13 focused fingerprint, source/wheel/_MEIPASS resource, and resource-policy tests passed. |
| `venv-linux/bin/python -m ruff check libremark_pdf tests && git diff --check` | 0 | Ruff and whitespace validation passed. |
| isolated `pip wheel --no-deps` from a temporary source copy | 1 | Expected offline limitation: PEP 517 isolation tried to fetch locked `setuptools==82.0.1` and DNS was unavailable. |
| `pip wheel --no-build-isolation --no-deps` then temporary-prefix install | 0 | Wheel contains CSS, icons, assets, seven static fonts, and four license records. |
| temporary-prefix resource lookup outside source tree | 0 | Installed wheel resolved CSS/icons/fonts; `NotoSans-Regular.ttf` SHA-256 was `478c558ea716033cd60c03438f628dfa75694dcf6b5f6d505a2f05fd2b4f3823`. |

The isolated-build failure is environment evidence only. A clean, offline build
environment preseeded with the locked build requirements remains required for
release evidence.

## Incremental evidence — batch browser lifecycle

`convert_batch()` now completes the destination preflight before publishing any
output, starts at most one locked browser process for renderable entries, opens
one fresh safe context per document, and always closes the shared process. A
failed item remains isolated and still produces one result record. During the
first real-batch attempt, `Page.pdf(timeout=...)` failed because Playwright
1.60's Python binding does not accept that parameter; the argument was removed
while the page-content timeout remains enforced. This is a compatibility defect
found by the real renderer test, not a waived test.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestDeterministicCoreContract tests.test_cli -v` | 0 | 14 focused batch lifecycle, output, profile, and CLI tests passed. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_convert_batch_reports_per_file_status -v` | 1 | Initial real batch exposed unsupported `Page.pdf(timeout=...)`; valid input reported an error. |
| same command after removing unsupported argument | 0 | Real locked-Chromium batch returned `ok` for the valid input and an independent error for the missing input. |
| two fresh `RenderProfile('2026-07-14').fingerprint` processes | 0 / 0 | Both emitted `e356cf02cc87a1a64b82f97e3e4f8fdadb6c0e413eeb15772365b94ccf8b4ff0`. |

## Incremental evidence — canonical comparison harness

The new comparison tool has no renderer implementation: it creates documents
only through `libremark_pdf.core`, then uses pinned PDFium 5.11.0 at the frozen
144 DPI to inspect page count, dimensions, text order hash, image inventory,
PDF URI inventory, and pixels. It compares canonical pre-render HTML and
profile fingerprints exactly; every semantic, pagination, structural, or
threshold mismatch fails and retains a page diff. The normal command has no
golden-update option. A separate writer requires a non-empty review ticket,
named human reviewer, and explanation before it can replace expected data.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestHeaderFooterConfig tests.test_core.TestTemplateBuilding tests.test_core.TestDeterministicCoreContract tests.test_g2_harness -v` | 0 | 26 focused core and harness tests passed. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tools/g2_visual_harness.py tools/update_g2_goldens.py tests/test_core.py tests/test_g2_harness.py` | 0 | Syntax/undefined-name policy passed. |
| `git diff --check` | 0 | No whitespace errors. |

## Incremental evidence — regenerated G2 baseline and ADR-009

The owner approved regeneration of the canonical G2 expected data from the
exact candidate `1822a7c538558622a088ef464f15ddee408eef1d` after review, and
approved a `0.10%` (rather than `0.05%`) maximum connected changed region for
G2. ADR-009 records the narrow amendment. It leaves SSIM, changed-pixel,
semantic, resource, pagination, and geometry requirements unchanged; the G1
archive remains historical immutable evidence.

The signed local tag `g2-golden-regeneration-2026-07-18` verifies for
`maydareality@gmail.com`, ED25519 `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`,
and resolves to the exact candidate commit. The writer used a complete
checkpoint corpus extracted from retained Linux evidence; it did not render or
download anything while replacing the approved manifest and PNGs.

| Command | Exit | Result |
| --- | ---: | --- |
| `git tag -v g2-golden-regeneration-2026-07-18` | 0 | Signed tag verified on `1822a7c538558622a088ef464f15ddee408eef1d`. |
| `/tmp/libremark-g2-linux-venv/bin/python tools/update_g2_goldens.py --manifest tests/fixtures/g2/manifest.json --expected tests/goldens/g2/expected.json --actual-dir /tmp/libremark-g2-linux-1822a7c-regenerated/actual --candidate-commit 1822a7c538558622a088ef464f15ddee408eef1d --review-tag g2-golden-regeneration-2026-07-18 --review-ticket G2-GOLDEN-REGEN-1822a7c --reviewer maydareal ...` | 0 | Regenerated manifest and 34 reviewed PNGs from complete evidence. |
| `/tmp/libremark-g2-linux-venv/bin/python tools/g2_visual_harness.py ... --actual-dir /tmp/libremark-g2-linux-1822a7c-regenerated/actual --collect-only` | 0 | Linux-to-regenerated-golden comparison passed all 31 fixtures. |
| `/tmp/libremark-g2-linux-venv/bin/python -X faulthandler tools/g2_visual_harness.py ... --actual-dir /tmp/libremark-g2-windows-1822a7c/actual --collect-only` | 1 | Windows comparison has identical non-raster inputs and passes all raster thresholds, but fails strict PDFium text-geometry equality for all 31 fixtures. |

Evidence hashes:

- reviewed Linux candidate evidence: `/tmp/libremark-g2-linux-1822a7c-regenerated/actual/evidence.json`, SHA-256 `116b65d0153b018d20613356c26a028467a625df8abdb65f2085e510f53ba146`;
- regenerated expected manifest: `tests/goldens/g2/expected.json`, SHA-256 `dd32efe4bb7728f80a4e9d7c47d77d7f136c3b54e6de37ddaa8184c08c277464`;
- Linux comparison report: `/tmp/libremark-g2-linux-1822a7c-regenerated/regenerated-linux-report.json`, SHA-256 `9e4207be6b8fe8dc5cd68b8177324168cb415fa854297e189013b1c257e61ab5`;
- Windows comparison report: `/tmp/libremark-g2-linux-1822a7c-regenerated/regenerated-windows-report.json`, SHA-256 `a06363f4d65cb50326cedc2946ae45b90b7ce668289b0a31bcaa7050ab6e3b44`.

For `09-inline-code`, the Windows/Linux metrics are SSIM `0.7036256698`,
changed pixels `0.3705008479%`, and largest connected region `0.0608047322%`;
all pass ADR-009. Its and every other fixture's `text_geometry_sha256`
nevertheless differs between platforms (for example, `01-headings` Linux
`4f44d875...70e021`, Windows `7774a979...00d861`). This is a strict structural
failure under ADR-002 and the target architecture, not an antialiasing metric
failure. G2 therefore remains open pending an owner decision: preserve strict
geometry and correct the cross-platform rendering discrepancy, or explicitly
supersede that structural contract with a separately reviewed tolerance policy.

## Incremental decision — ADR-010 PDFium box tolerance

The owner approved ADR-010 after direct measurement of the retained exact
Linux/Windows candidate PDFs. For pages with exact extracted text/order, the
maximum per-coordinate difference for a visible character box is `1.8553619385
pt`; ADR-010 therefore permits at most `2.00 pt`. Whitespace and control boxes
are excluded because they are PDFium advance/control artifacts, but text,
order, pagination, dimensions, links, images, and raster checks remain exact
or frozen as applicable.

This decision does not accept the `23-unicode` extracted-text mismatch: Linux
extracts `हि न्दी` while Windows extracts `हिन्दी`. The harness implementation,
its boundary tests, regenerated reports, and correction of that text mismatch
remain required before G2 can pass.

## Failed experiment — pinned Devanagari webfont

The proposed static `NotoSansDevanagari-Regular.ttf` was downloaded only to
`/tmp` from the same pinned Noto distribution revision as the G1 Noto Sans
faces (`11caf4e14799c87eadf02026f2bd17eec5d50adb`). Its SHA-256 was
`306b53ecfb182a504dd8a7446093c316387d2fd8dc350d0792ed1753fe0996cd`; the
existing Noto Distribution OFL record matched.

In a local locked-Chromium experiment the font was embedded as a data URI and
CDP reported `Noto Sans Devanagari`, `isCustomFont: true`, and `glyphCount: 9`.
PDFium nevertheless extracted `भा षा` and `हि न्दी`, rather than `भाषा` and
`हिन्दी`. The failure therefore persists even without a system-font fallback;
it is a Chromium PDF text/ToUnicode behavior for this complex script, not an
uncontrolled resource selection. CSS ligature and kerning variants were also
explored outside the repository and did not yield accepted evidence.

The font, CSS/profile changes, test, and proposed ADR-011 were discarded. No
new font or licence file entered Git. Do not retry this exact face as a G2
fix without a different PDF text-extraction strategy and focused evidence.

## Failed experiment — PDF `ActualText` post-processing

The locked Chromium produced a tagged PDF with `/StructTreeRoot` and a
`/ToUnicode` table for Devanagari. Poppler `pdftotext` extracted `भाषा` and
`हिन्दी` correctly from that temporary PDF, while pinned PDFium extracted
`भा षा` and `हि न्दी`. The difference is therefore PDFium's complex-script
text interpretation, rather than a missing PDF semantic mapping.

Static trusted HTML with `aria-label="हिन्दी"` was also rendered as a temporary
probe. It did not create PDFium-visible `ActualText`; PDFium retained the same
inserted space. The locked environment provides no PDF writer dependency
(`pypdf`, `PyPDF2`, `pikepdf`, and `fitz` are absent). Adding one, then editing
tagged content streams and structure trees after Chromium, would introduce an
untested second PDF implementation and risks corrupting tags, links, outlines,
or atomic output semantics.

This post-processing route is rejected for G2. The safe choices are to retain
the strict PDFium extraction requirement and mark Devanagari unsupported for
the locked renderer, or to revise the semantic-text inspector through a new
owner-approved architecture decision that is validated independently of
PDFium's synthesized spacing.

## Owner disposition — retain the Unicode limitation

The owner directs that `23-unicode` remain in the canonical corpus. The
observed Linux PDFium extraction of Devanagari (`हि न्दी`) versus native Windows
(`हिन्दी`) is retained as an explicit known limitation and regression target.
It must not be normalized, ignored, thresholded away, or removed from the
fixture. Work to resolve it resumes only when a deterministic and independently
validated strategy is available.

This is not an acceptance of the mismatch and does not close VIS-008, REN-014,
or G2. The next owner is the integration/rendering owner; the required next
evidence is a candidate fix that preserves exact Unicode text on both native
platforms while retaining the locked renderer, local-first policy, tagged PDF,
and all existing structural and visual checks.

## Incremental evidence — resumable Linux candidate generation

The interactive executor terminated the initial all-fixture candidate run after
three PDFs and before it could publish `evidence.json`. The harness now writes
each finished fixture entry as an atomic checkpoint under an external
`actual/entries/` directory. Candidate generation can select repeatable
`--fixture` IDs, and `--collect-only` refuses to publish a complete manifest
unless every ID in the source manifest has a checkpoint. The normal comparison
path remains immutable; `--generate-only` produces no expected data.

| Command | Exit | Result |
| --- | ---: | --- |
| original 31-fixture `--generate-only` run | incomplete | Executor ended after `01`–`03`; partial PDFs remained only in `/tmp` and no evidence manifest was published. |
| `venv-linux/bin/python -m unittest tests.test_g2_harness -v` | 0 | 9 harness tests passed, including incomplete-checkpoint rejection. |
| `/tmp/libremark-python39-venv/bin/python -m py_compile tools/g2_visual_harness.py tests/test_g2_harness.py` | 0 | Resume/checkpoint implementation compiles under Python 3.9.23. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python tools/g2_visual_harness.py ... --generate-only --fixture 01-headings` | 0 | One locked-browser fixture produced a checkpoint and a one-fixture candidate manifest under `/tmp/libremark-g2-linux-resume`; no expected data was written. |
| `venv-linux/bin/python -m ruff check tools/g2_visual_harness.py tests/test_g2_harness.py && git diff --check` | 0 | Ruff and whitespace checks passed. |

The full Linux corpus remains open until all 31 checkpoints are collected in an
uninterrupted or segmented execution and are submitted for human golden review.
| first `/tmp` corpus invocation | 1 | Direct execution initially failed before rendering: `tools/g2_visual_harness.py` did not place the repository root on `sys.path`. Corrected without changing rendering behavior. |
| corrected `/tmp` corpus invocation | incomplete | Four fixtures rendered through the shared core before the interactive command window ended; no `evidence.json`, report, expected manifest, or repository PDF was created. This is an execution-window limit, not accepted full-corpus evidence. |

No expected data or raster golden is committed. A full Linux run must use an
uninterrupted worker, write its artifacts outside the repository, and then be
submitted with before/after images and a named human appearance review before
the explicit golden writer is permitted. The harness and corpus therefore
remain in progress, and G2 remains open.

## Incremental evidence — tagged PDF and outline

Inspection of the locked Playwright 1.60 `Page.pdf()` signature confirmed that
both `tagged` and `outline` are available. The core requests both options for
every document. This is not inferred from API presence alone: the emitted PDF
was inspected for `/StructTreeRoot` and `/Outlines`.

| Command | Exit | Result |
| --- | ---: | --- |
| locked-engine `Page.pdf(tagged=True, outline=True)` probe | 0 | `/StructTreeRoot=True`, `/Outlines=True`; 12,532-byte probe PDF under `/tmp`. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_locked_engine_emits_tagged_pdf_and_outline -v` | 0 | Core-produced PDF contained both required structural markers. |

This is Linux evidence only. The same structural test is mandatory in the
native Windows candidate run before REN-014 or G2 is accepted.

## Incremental evidence — renderer diagnostic code

An unexpected browser operation exception is now translated at the renderer
boundary to `RENDER_FAILED: <underlying diagnostic>`. Existing typed conversion
errors pass through unchanged. The context is still closed in the `finally`
path.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestDeterministicCoreContract -v` | 0 | 13 tests passed, including stable renderer-code/message and context-cleanup proof. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tests/test_core.py` | 0 | Syntax/undefined-name policy passed. |

## Incremental evidence — Python 3.9 and trusted-static closure

Python 3.9.23 is now available in the external validation environment at
`/tmp/libremark-python39-venv`; it is not part of the repository or an
application runtime dependency. The core, front ends, and G2 tooling compile
under that interpreter. The trusted-static filter now also rejects CSS resource
loaders hidden in inline `style` attributes and fetch-capable `poster`,
`background`, `data`, and `formaction` attributes. SVG acceptance requires an
actual SVG root in addition to the existing active-content inspection.

| Command | Exit | Result |
| --- | ---: | --- |
| `/tmp/libremark-python39-venv/bin/python --version` | 0 | `Python 3.9.23`. |
| `/tmp/libremark-python39-venv/bin/python -m py_compile libremark_pdf/core.py libremark_pdf/cli.py libremark_pdf/gui.py libremark_pdf/i18n.py libremark_pdf/__main__.py tools/g2_visual_harness.py tools/update_g2_goldens.py` | 0 | Python 3.9 syntax validation passed. |
| `venv-linux/bin/python -m unittest tests.test_core.TestMarkdownConversion tests.test_core.TestResourcePolicy tests.test_core.TestDeterministicCoreContract -v` | 0 | 29 focused trust, resource, atomic-output, and deterministic-profile tests passed. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tests/test_core.py && git diff --check` | 0 | Ruff and whitespace checks passed. |

The Pyenv-managed interpreter is not on the non-interactive shell `PATH`; G2
commands must use the explicit venv path above. Browser network observation and
the full canonical corpus remain open gate evidence.

## Incremental evidence — observed network isolation

`_BrowserRenderer` now retains the observed, non-`data:` route requests from
the most recent document solely for verification. Any such request is aborted
and fails the conversion as `NETWORK_BLOCKED`. The locked browser integration
test rendered one safe document and one approved trusted-static document in the
same browser process and asserted an empty observation list after each render.

| Command | Exit | Result |
| --- | ---: | --- |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_safe_and_trusted_static_rendering_observe_zero_requests -v` | 0 | Locked Chromium completed both modes; each recorded `[]` observed non-data requests. |

This is reproducible Linux evidence for REN-004. It must be repeated from the
exact candidate commit on native Windows; no network observation may be inferred
from this Linux run.

## Incremental evidence — bounded inputs and actionable edge failures

The canonical profile now includes the 10 MiB Markdown input limit. Empty
Markdown remains a valid document. File and in-memory input reject invalid
UTF-8-compatible text and size overflow with stable codes. CSS decode/null-byte
failures and destination-directory creation failures are normalized at the core
boundary without hiding their original exception cause.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestDeterministicCoreContract -v` | 0 | 17 focused deterministic/output/edge-case tests passed. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tests/test_core.py` | 0 | `All checks passed!` |
| `/tmp/libremark-python39-venv/bin/python -m py_compile libremark_pdf/core.py tests/test_core.py` | 0 | Changed core and tests compile under Python 3.9.23. |

Permission behavior is simulated at the core boundary because the Linux test
process has elevated group capabilities; native Windows still needs the real
unwritable-destination case in its candidate evidence.

## Incremental evidence — segmented Linux suite

The interactive executor stops a monolithic browser suite before its final
summary (while a Chromium test is still running), and leaves no process behind.
That result is recorded as incomplete rather than as a passing full suite. The
browser-free portion was rerun as one deterministic segment and completed.

| Command | Exit | Result |
| --- | ---: | --- |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v` | incomplete | Interactive window ended during `test_locked_engine_emits_tagged_pdf_and_outline`; no test failure or surviving process was reported. |
| `venv-linux/bin/python -m unittest tests.test_cli tests.test_community tests.test_g2_harness tests.test_core.TestHeaderFooterConfig tests.test_core.TestMarkdownConversion tests.test_core.TestDeterministicCoreContract tests.test_core.TestResourcePolicy -v` | 0 | 51 browser-free CLI, community, harness, core, and resource tests passed. |

The individual locked-Chromium tests recorded earlier remain valid; a complete
uninterrupted full-suite execution is still required before G2 closure.

## Incremental evidence — canonical corpus strengthening and static SVG

The corpus now has 31 fixtures. It contains a genuinely multi-page table,
embedded PNG/JPEG/GIF coverage, a local static SVG, and inputs whose actual
paths include spaces, Unicode, and duplicate Markdown stems. The comparison
manifest now records ordered hashes of embedded image payloads, a canonical
profile JSON hash, renderer CSS/font/icon hashes, and a PDFium character-box
geometry hash in addition to the pre-existing HTML, text, page, link, image,
pagination, and raster checks. A geometry mismatch is an unconditional
structural failure in the harness unit test.

Characterization found that the SVG filter rejected the standard
`xmlns="http://www.w3.org/2000/svg"` declaration because it treated every HTTP
string as a network capability. The narrow correction permits XML namespaces
but continues to reject external `href`/`src`/`xlink:href`, scripts, event
handlers, `@import`, and CSS `url()` content. The locked browser then rendered
that standard static SVG with no observed non-data request.

| Command | Exit | Result |
| --- | ---: | --- |
| initial canonical preparation of all fixtures | 1 | Revealed the standard SVG namespace false positive and the out-of-root PNG fixture; no PDF, expected data, or golden was written. |
| `venv-linux/bin/python -m unittest tests.test_core.TestResourcePolicy tests.test_g2_harness -v` | 0 | 13 SVG/resource and harness checks passed after the narrow SVG correction. |
| canonical preparation loop over `tests/fixtures/g2/manifest.json` | 0 | All 31 fixtures prepared through the core with fixed inputs and profile fingerprints. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_standard_static_svg_renders_offline -v` | 0 | Locked Chromium rendered a standard static SVG and observed `[]` non-data requests. |
| `venv-linux/bin/python -m unittest tests.test_core.TestMarkdownConversion tests.test_core.TestResourcePolicy tests.test_g2_harness -v` | 0 | 25 core/resource/harness checks passed, including alternative-text and geometry-failure assertions. |
| `/tmp/libremark-python39-venv/bin/python -m py_compile libremark_pdf/core.py tests/test_core.py tools/g2_visual_harness.py tests/test_g2_harness.py` | 0 | Changed code compiles with Python 3.9.23. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tests/test_core.py tools/g2_visual_harness.py tests/test_g2_harness.py` | 0 | `All checks passed!` |
| `git diff --check` | 0 | No whitespace errors. |

This does not create or approve goldens. A full uninterrupted Linux corpus run,
explicit human golden review, and the matching native Windows run remain
required before any VIS item is accepted.

## Incremental evidence — approved Linux canonical baseline

The full 31-fixture Linux candidate evidence was completed outside the
repository from candidate commit `90d7dafd282dfbac4cf1692e523f9410cb8a588d`.
`maydareal` approved the initial canonical baseline under review identity
`G2-GOLDEN-INITIAL-90d7daf`.  The signed local tag
`g2-golden-initial-2026-07-14` resolves to that exact commit and verifies with
the configured ED25519 signing key.  The writer was strengthened before use:
when given reviewed evidence it requires a complete checkpoint set and rejects
an `evidence.json` that differs from those checkpoints.  It therefore did not
re-render or alter the reviewed candidate.

| Command | Exit | Result |
| --- | ---: | --- |
| `git tag -v g2-golden-initial-2026-07-14` | 0 | Signed tag creation on `90d7dafd282dfbac4cf1692e523f9410cb8a588d` verified for `maydareality@gmail.com`, ED25519 `SHA256:/uZzs39mv1QxR2FXYN9ewOlf4FqeNZXzcYD5lKIievM`. |
| `venv-linux/bin/python -m unittest tests.test_g2_harness -v` | 0 | 10 harness tests passed, including reviewed-evidence guard coverage. |
| `venv-linux/bin/python tools/update_g2_goldens.py --manifest tests/fixtures/g2/manifest.json --expected tests/goldens/g2/expected.json --actual-dir /tmp/libremark-g2-linux-resume/actual --candidate-commit 90d7dafd282dfbac4cf1692e523f9410cb8a588d --review-tag g2-golden-initial-2026-07-14 --review-ticket G2-GOLDEN-INITIAL-90d7daf --reviewer maydareal --explanation "Initial G2 canonical baseline approved by maydareal for commit 90d7dafd282dfbac4cf1692e523f9410cb8a588d, using the locked renderer, approved fonts, fixed render date, and 31-fixture corpus; no prior G2 golden data exists."` | 0 | Wrote approved expected manifest and 34 required 144-DPI PNG reference rasters, without rendering. |
| `venv-linux/bin/python tools/g2_visual_harness.py --manifest tests/fixtures/g2/manifest.json --expected tests/goldens/g2/expected.json --actual-dir /tmp/libremark-g2-linux-resume/actual --report /tmp/libremark-g2-linux-resume/approved-compare-report.json --diff-dir /tmp/libremark-g2-linux-resume/approved-diff --collect-only` | 0 | Strict comparison passed: 31 fixtures, 34 pages, no semantic, pagination, geometry, or raster difference. |
| `venv-linux/bin/python -m ruff check tools/g2_visual_harness.py tools/update_g2_goldens.py tests/test_g2_harness.py` | 0 | `All checks passed!` |
| `/tmp/libremark-python39-venv/bin/python -m py_compile tools/g2_visual_harness.py tools/update_g2_goldens.py tests/test_g2_harness.py` | 0 | Python 3.9.23 syntax validation passed. |

Evidence hashes:

- reviewed Linux candidate evidence: `/tmp/libremark-g2-linux-resume/actual/evidence.json`, SHA-256 `a34fab2fd4f122b7722dd3e3b167c39703b7acf091a430c5fbf1f95be3aa992f`;
- approved expected manifest: `tests/goldens/g2/expected.json`, SHA-256 `2cdd297d108f6a8a0bd15593f7b81b2a3b545ff2795b74e4c94a4ae7735fd4b5`;
- strict comparison report: `/tmp/libremark-g2-linux-resume/approved-compare-report.json`, SHA-256 `9cead242bba7fddd6d9380a0cd47f75e34cf30e7b8db814344ae92ecf1f197f0`.

The committed expected data is 1.4 MiB (one JSON manifest plus 34 PNGs).  The
rasters are necessary approved inputs for the frozen visual metric, while PDFs,
temporary candidate rasters, browser payloads, and diff output remain outside
source control.  VIS-001 through VIS-007 are accepted for Linux.  VIS-008 and
the G2 decision remain open pending the same-commit native Windows evidence.

The exact execution and return-bundle specification for that remaining lane is
[`G2_WINDOWS_EXECUTION_PROMPT.md`](G2_WINDOWS_EXECUTION_PROMPT.md).  It targets
commit `1822a7c538558622a088ef464f15ddee408eef1d`, the first candidate that
contains the approved expected data.  The native agent must not replace its
locked browser payload or download a browser while executing the offline lane.

## Incremental evidence — exact Linux/Windows candidate pair

The canonical corpus was recaptured from the exact Windows candidate commit
`1822a7c538558622a088ef464f15ddee408eef1d`, with candidate PDFs, checkpoints,
and report retained only under `/tmp/libremark-g2-linux-1822a7c`.  The first
long renderer process was interrupted by the interactive executor after four
checkpoints.  Resumable fixture invocations completed the remaining entries;
`--collect-only` then required all 31 before comparison.  This is a runner
window limitation, not a test skip or a partial accepted corpus.

| Command | Exit | Result |
| --- | ---: | --- |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python tools/g2_visual_harness.py --manifest tests/fixtures/g2/manifest.json --actual-dir /tmp/libremark-g2-linux-1822a7c/actual --report /tmp/libremark-g2-linux-1822a7c/generate-report.json --diff-dir /tmp/libremark-g2-linux-1822a7c/diff --generate-only` | incomplete | First attempt published checkpoints `01`–`04` only before the executor window ended. |
| resumable `tools/g2_visual_harness.py --generate-only --fixture <remaining-ID>` invocations using the same command inputs | 0 | Completed all 31 expected checkpoint entries without writing expected data. |
| `venv-linux/bin/python tools/g2_visual_harness.py --manifest tests/fixtures/g2/manifest.json --expected tests/goldens/g2/expected.json --actual-dir /tmp/libremark-g2-linux-1822a7c/actual --report /tmp/libremark-g2-linux-1822a7c/comparison-report.json --diff-dir /tmp/libremark-g2-linux-1822a7c/diff --collect-only` | 0 | Strict comparison passed for 31 fixtures and 34 pages. |

- exact-candidate Linux evidence: `/tmp/libremark-g2-linux-1822a7c/actual/evidence.json`, SHA-256 `f042289deae91377d28e243f7e871a87cb3178a03d542f8750dc785b828b6812`;
- exact-candidate Linux comparison: `/tmp/libremark-g2-linux-1822a7c/comparison-report.json`, SHA-256 `9cead242bba7fddd6d9380a0cd47f75e34cf30e7b8db814344ae92ecf1f197f0`.

The final monolithic Linux `unittest discover` attempt again reached the
locked tagged-PDF integration test after the browser-free and earlier browser
tests reported `ok`, but the interactive executor ended before the suite
summary.  It is recorded as incomplete, not as a full-suite pass.  The two
remaining targeted locked-engine checks completed independently:

| Command | Exit | Result |
| --- | ---: | --- |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v` | incomplete | Executor ended during `test_locked_engine_emits_tagged_pdf_and_outline`; no final summary was produced. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest tests.test_core.TestEndToEndConversion.test_locked_engine_emits_tagged_pdf_and_outline tests.test_core.TestEndToEndConversion.test_render_preview_png_returns_valid_png_bytes -v` | 0 | Both locked Chromium checks passed in 24.069 seconds. |

## Incremental evidence — atomic output publication failures

Temporary output creation and final atomic replacement are now normalized at
the core boundary as `OUTPUT_UNAVAILABLE` and `OUTPUT_REPLACE_FAILED`.
Characterization tests simulate each operating-system failure after an existing
destination has been created. Both retain the old destination bytes and leave
no `.libremark-*.pdf` temporary file. This is additional Linux-independent
contract evidence; a real native Windows unwritable-destination case remains
part of the candidate evidence bundle.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest tests.test_core.TestDeterministicCoreContract -v` | 0 | 19 deterministic, batch, output, and edge-condition tests passed. |
| `/tmp/libremark-python39-venv/bin/python -m py_compile libremark_pdf/core.py tests/test_core.py` | 0 | Changed output path compiles with Python 3.9.23. |
| `venv-linux/bin/python -m ruff check libremark_pdf/core.py tests/test_core.py` | 0 | `All checks passed!` |
| `git diff --check` | 0 | No whitespace errors. |
