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
