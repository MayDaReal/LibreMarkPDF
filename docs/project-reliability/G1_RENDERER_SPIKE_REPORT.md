# Gate G1 renderer and packaging spike report

Status: **candidate direction selected; mandatory evidence incomplete**
Evidence date: 2026-07-13
Environment: Ubuntu 24.04.4, Linux 6.17 x86_64, CPython 3.12.3
Source HEAD: `b2c194d31d08a3e8befae15941db8c4a1f2d0060`

## Decision summary

The Python 3.9-compatible target candidate is Playwright `1.60.0`, whose wheel
manifest selects Chromium/Chrome for Testing and headless shell
`148.0.7778.96`, revision `1223`, plus FFmpeg revision `1011`. The Windows x64
CPython 3.9 wheel is locked by hash in
`requirements/locks/windows-x64-py39.txt`.

The installed Linux evidence environment instead uses Playwright `1.61.0`,
Chromium `149.0.7827.55` revision `1228`, and driver package
`1.61.1-beta-1782139630000`. Playwright `1.61.0` and Markdown `3.10.2` both
reject Python 3.9 during target resolution, so that environment cannot define
the supported G1 lock. It remains historical G0 evidence only.

Playwright documents that every library version is coupled to browser binaries,
supports an isolated `PLAYWRIGHT_BROWSERS_PATH`, and supports headless-shell-only
installation with `--only-shell`: <https://playwright.dev/python/docs/browsers>.

## Renderer and resource direction

The non-production probe in `spikes/g1/renderer_probe.py` defines the measured
direction:

- deterministic, sorted UTF-8 JSON fingerprints with domain separators;
- JavaScript disabled and service workers blocked at context creation;
- context-wide abort routes for HTTP and HTTPS;
- accepted resources embedded as data URIs before content reaches Chromium;
- raw HTML represented literally in safe mode.

Production work in Lot 2 must resolve local resources against the Markdown
parent, prevent traversal and symlink escape, validate types and limits, embed
accepted content, reject remote/file/CSS imports, and provide the separately
approved static trusted-HTML mode. Playwright's official APIs cover request
abortion and the required context controls:
<https://playwright.dev/python/docs/network> and
<https://playwright.dev/python/docs/api/class-browser>.

Python-Markdown removed its former `safe_mode` because it was not safe. Lot 2
must use explicit raw-HTML neutralization rather than relying on that removed
option: <https://python-markdown.github.io/changelog/>.

The candidate probe ran with Playwright `1.60.0` and the isolated Linux
headless-shell revision `1223` (270,938,012 bytes) plus FFmpeg revision `1011`
(5,127,582 bytes). It exited 0. The local fixture made zero HTTP/HTTPS attempts,
received zero external responses, rendered the embedded PNG at natural width
121 pixels, and did not execute the literalized script. The hostile fixture's
single `https://example.invalid/blocked.png` attempt was intercepted and aborted,
received no response, and rendered at zero natural width. The profile fingerprint
was `bc545f04fd2b19f804e6f9d7cef7a29957259a2b2a0e2002aa3e145a107f7316`.
Generated evidence `/tmp/libremark-g1-renderer-probe.json` is 1,105 bytes with
SHA-256 `61fb72c14818eca9e4466d2050c0a6d89cf3af08ce958fee14d28b7567742dad`;
it is intentionally outside source control.

## Font candidates and license record

The visual bake-off candidates are:

| Role | Candidate | Approximate upstream size | License evidence |
| --- | --- | ---: | --- |
| proportional regular/semibold | Noto Sans variable 400/600 | 1.95 MB | [binary](https://github.com/google/fonts/blob/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf), [SIL OFL](https://github.com/google/fonts/blob/main/ofl/notosans/OFL.txt) |
| monospace | Noto Sans Mono variable | 1.63 MB | [binary](https://github.com/google/fonts/blob/main/ofl/notosansmono/NotoSansMono%5Bwdth%2Cwght%5D.ttf), [SIL OFL](https://github.com/google/fonts/blob/main/ofl/notosansmono/OFL.txt) |
| symbols | Noto Sans Symbols 2 | 0.64 MB | [binary](https://github.com/google/fonts/blob/main/ofl/notosanssymbols2/NotoSansSymbols2-Regular.ttf), [SIL OFL](https://github.com/google/fonts/blob/main/ofl/notosanssymbols2/OFL.txt) |
| emoji research | monochrome Noto Emoji | not locked | [repository/license](https://github.com/googlefonts/noto-emoji) |

The first three add about 4.22 MB before compression. These upstream display
sizes are research, not a release lock. Exact commits, files, byte sizes,
SHA-256 values, font metadata, license texts, CJK/RTL coverage, and visual review
are still required. Existing status PNG icons remain compatibility-sensitive.

## Visual threshold decision

ADR-002 remains unchanged: 144-DPI pinned PDFium, SSIM at least `0.995`, no more
than `0.10%` of pixels exceeding any RGB-channel delta of `16`, no connected
changed region larger than `0.50%` of a page, and unconditional failure for any
semantic, geometry, resource, or pagination difference. No cross-OS evidence
exists to justify the one permitted amendment.

## Windows artifact direction

The inspected `dist/LibreMarkPDF.exe` is an unvalidated PE32+ GUI x86-64
PyInstaller artifact, 373,253,524 bytes, SHA-256
`a153272f7a6ce142c28817a0967bcf1ab107941092fe2cb43715472291d74f29`.
It is not the previously documented 373,231,113-byte artifact and inherits none
of that artifact's reported checks.

Its archive contains both full Chromium and headless shell. Measured compressed
payload is 191,650,285 bytes for full Chromium, 118,497,010 bytes for headless
shell, 1,406,905 bytes for FFmpeg, and 131,807 bytes for WinLDD. The default
launch trace selected headless shell. The next native candidate should therefore
install and bundle `--only-shell chromium`; only its rebuilt artifact may claim
the actual size reduction.

ADR-007 makes a zipped portable directory the guaranteed fallback and primary
direction until a one-file candidate passes native comparison. No portable
directory candidate, Defender result, startup/conversion timings, extraction
cleanup, concurrency, disk-pressure, or long/Unicode-path evidence exists.

## Task state and blockers

| Task | State | Evidence / blocker |
| --- | --- | --- |
| SPIKE-REN-001 | partial | Python 3.9 wheel/browser candidate and hash recorded; clean native install pending |
| SPIKE-REN-002 | research complete | candidate licenses recorded; exact font binary locks and coverage pending |
| SPIKE-REN-003 | blocked | no embedded-font render on Windows and a second OS |
| SPIKE-REN-004 | partial | target-revision isolated prototype records zero requests for local content and blocks a hostile attempt; full resource corpus pending |
| SPIKE-REN-005 | partial | target-revision browser controls/literal safe-mode probe passes; trusted-HTML sanitizer corpus pending |
| SPIKE-REN-006 | partial | fingerprint algorithm/probe exists; two-clean-build equality pending |
| SPIKE-REN-007 | blocked | no cross-OS page pairs or metric report |
| SPIKE-PKG-001 | blocked | native one-file/portable-directory comparison absent |
| SPIKE-PKG-002 | partial | current waste quantified; rebuilt only-shell candidate absent |

Named owners: renderer-spike owner for fonts, safe-resource prototype and visual
metrics; Windows package-spike owner for native artifact comparison; QAS owner
for clean Python 3.9 locks/CI; security/core owner for trusted-HTML and SVG/GIF/
custom-CSS policy; integrator and repository owner for any ADR amendment and G1.
