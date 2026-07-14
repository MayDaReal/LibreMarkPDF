# Gate G1 renderer and packaging spike report

Status: **direction selected; native Windows visual comparison pending**
Evidence date: 2026-07-14
Linux environment: Ubuntu 24.04.4, Linux 6.17 x86_64, CPython 3.12.3
Windows evidence source: commit `50f134121366e4922774bd67c6e5e7554108d09b`

Production rendering, default CSS, fonts, margins, pagination, icons, GUI, CLI,
and skill behavior are unchanged. All new executable code is confined to
`spikes/g1/` and generated browsers, fonts, PDFs, PNGs, diffs, and JSON reports
remain outside the repository.

## G1 selections

| Decision | Selected direction | Evidence status |
| --- | --- | --- |
| Renderer/browser | Python 3.9-compatible Playwright 1.60.0, Chromium/headless shell 148.0.7778.96 revision 1223, FFmpeg 1011 | native Windows and Linux launch evidence exists |
| Fonts | the six-file Noto set locked below | exact files, commits, hashes, sizes, roles, and OFL records exist; Windows visual run pending |
| Resources/network | embed accepted local resources before rendering; deny HTTP/HTTPS; disable JavaScript and service workers; literal safe HTML by default | Linux and Windows feasibility probes observed zero responses; production implementation is Lot 2 |
| Visual thresholds | ADR-002 unchanged: 144 DPI, SSIM >= 0.995, changed pixels <= 0.10% at RGB delta 16, largest changed region <= 0.50%, plus strict structural equality | Linux repeat passes exactly; native Windows/Linux pair pending |
| Windows primary format | zipped portable directory | selected under ADR-007 from native onefile/portable measurements; this is not an official artifact claim |

## Renderer lock

Playwright `1.60.0` is the latest evaluated release in this program that
supports Python 3.9. Its driver manifest selects Chromium and headless shell
`148.0.7778.96` revision `1223` and FFmpeg revision `1011`. The complete native
Windows CPython 3.9 dependency set is hash-locked in
`requirements/locks/windows-x64-py39.txt` and installed successfully in the
Windows evidence lane.

The clean Linux visual environment used the same Markdown `3.9`, Playwright
`1.60.0`, Pillow `11.3.0`, PDFium `5.11.0`, and isolated revision-1223 headless
shell. The Linux executable was 188,087,520 bytes, SHA-256
`7b8e92dca0acf9c24b5974507b3031d6bd18cc009cd431c2595e521430ea747a`.
The native Windows headless shell was 201,396,224 bytes, SHA-256
`2d8f2abad1a0f2998aaf861967c374d4aad6a104916b8794318760ed35db772f`.

## Locked font candidates and licenses

`spikes/g1/font_candidates.json` is the machine-readable authority. Google
Fonts is pinned to commit `ec0464b978de222073645d6d3366f3fdf03376d8` and
Noto CJK to commit `f8d157532fbfaeda587e826d4cd5b21a49186f7c`.

| Role | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| proportional regular/semibold | `NotoSans.ttf` | 2,049,096 | `bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d` |
| monospace | `NotoSansMono.ttf` | 1,708,408 | `2cb2adb378a8f574213e23df697050b83c54c27df465a2015552740b2769a081` |
| Arabic/RTL fallback | `NotoSansArabic.ttf` | 844,676 | `63111b5b2e074dd48cc67692e0a2726d86ee94c1c37fe8598257b7b4e87e869e` |
| CJK fallback | `NotoSansCJKsc-Regular.otf` | 16,437,364 | `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b` |
| symbols fallback | `NotoSansSymbols2-Regular.ttf` | 1,233,128 | `7d5fb73b7ca67a6798101741f5d280a3d016a56a197afcd4199dbb57b4b82a21` |
| monochrome emoji fallback | `NotoEmoji.ttf` | 1,982,596 | `de6c18832938afc99caf132b39d6a30a19bac7f2e812e28db2535b4608d27551` |

The set totals 24,255,268 bytes before packaging. The CJK fallback accounts
for 67.8% of that total and remains the main size risk. Every file is licensed
under SIL Open Font License 1.1. The manifest pins each corresponding license
URL, byte size, and SHA-256; the six verified license records total 26,188
bytes. Actual redistribution notices are produced only when Lot 2 chooses the
final bundled subset.

## Resource and network policy evidence

The non-production probes create contexts with JavaScript disabled, service
workers blocked, and abort routes for HTTP and HTTPS. Accepted fixture assets
and all candidate fonts are data URIs before Chromium receives the document.

The original target-revision Linux probe observed zero requests/responses for
local content, blocked the single hostile HTTPS attempt before response,
rendered the embedded PNG at width 121, and did not execute the literal script.
The independent native Windows probe recorded the same results. The new Linux
current-font, candidate-font, and repeated-candidate visual renders each
recorded empty attempt and response lists.

These are feasibility results for ADR-004. They do not claim that the current
production core enforces the policy. Relative-path validation, traversal and
symlink defense, media limits, trusted static HTML, and custom-CSS validation
remain owned Lot 2 implementation work.

## Visual evidence

The representative fixture covers current theme geometry, headings, status
icons, accents, Arabic/RTL, CJK, emoji/symbols, lists, code, tables, wrapping,
and a two-page transition. `visual_probe.py` uses the unchanged current CSS and
either the current system stack or the embedded candidate set. PDFium 5.11.0
rasterizes every page at 144 DPI. `visual_compare.py` records structural checks,
global grayscale population SSIM, RGB delta counts, and the largest
eight-connected changed region.

Chrome's platform-font inspection attributed every exercised candidate glyph to
one of the six custom embedded fonts: Noto Sans, Mono, Arabic, CJK SC, Symbols
2, and Emoji. No body glyph used a system fallback.

Two candidate renders in the clean Linux environment produced identical
profile fingerprint
`9cd36bcbed17c103ab562ed70967e3b6d378e13f870d7bc55fbb46563d9046aa`,
identical logical HTML fingerprint
`d6786fbad42251050002f0a6b972c95283175149daea595af6745d38464e6635`,
and identical page PNG hashes. Both pages had SSIM `1.0`, `0%` changed pixels,
`0%` largest changed region, identical extracted-text hashes, page count, and
dimensions. The PDF hashes differed, as ADR-002 permits:

- first candidate PDF:
  `6a95959765ac035d9d894c1e1f396ed3bb99b24cfd1ece012fa1e3a1595519cc`;
- repeated candidate PDF:
  `2169efb4bc78f36d5a849f441e53a95fa645ad5e47052601c2848e5add3bb512`.

The informational Linux current-versus-candidate comparison retained two
pages but changed `5.4497%` and `6.5663%` of pixels. SSIM was `0.42034` and
`0.37398`; the largest regions were `0.18983%` and `0.12554%`. One page's
extracted-text hash changed because the font metrics changed line wrapping.
This comparison is deliberately marked `review`, not evaluated as cross-OS
equivalence. It demonstrates that adopting fixed fonts will create a new
canonical baseline and therefore requires the owner's visual approval before
Lot 2 changes production defaults.

The frozen ADR-002 thresholds are not amended. A native Windows run of the same
immutable fixture, font manifest, probe, Chromium revision, and PDFium version
is the only missing measurement needed to validate them across two operating
systems.

## Windows artifact selection

The native report compares diagnostic onefile and portable-directory builds
from the same source, Python 3.9 lock, PyInstaller 6.21.0, and revision-1223
headless shell. The portable ZIP is 178,091,360 bytes; the onefile executable
is 177,256,363 bytes. The 834,997-byte download difference is only 0.47%.

Portable median CLI help was 1,016 ms versus 4,033 ms for onefile. Portable
conversion was 2,017 ms versus 7,040 ms. Onefile GUI observations were 3.995
and 3.893 seconds, above ADR-007's absolute two-second condition. Onefile also
extracts about 432.5 MB per launch and received the stronger simulated
download-origin warning. Defender reported no threat for either diagnostic
candidate under the recorded single-definition test; this is not a reputation
or signing claim.

ADR-007 states that onefile becomes primary only after it proves every extra
criterion. It has not done so, while the portable direction passed the recorded
CLI, GUI, preview, conversion, empty-cache, offline, external Unicode/space
path, and standard-user checks. G1 therefore selects a zipped portable
directory as the primary Windows format. Separate windowed GUI and console CLI
entry points, controlled cold/concurrency/disk-pressure tests, signing,
SmartScreen reputation, and an exact release-candidate rerun remain later
packaging/release gates; their absence does not reopen the G1 format choice.

Bundling only the headless shell is also selected. The earlier inspected
archive carried 191,650,285 compressed bytes of full Chromium and 118,497,010
bytes of headless shell, a measured 73,153,275-byte (38.2%) removable payload.
The native portable candidate then staged and exercised only revision 1223.

## Task decisions

| Task | G1 state | Evidence / next dependency |
| --- | --- | --- |
| SPIKE-REN-001 | accepted | exact Python 3.9-compatible engine pair and native Windows/Linux payload hashes recorded |
| SPIKE-REN-002 | accepted | six exact font files, roles, upstream commits, sizes, hashes, and OFL records locked |
| SPIKE-REN-003 | pending | Linux current/candidate renders exist; run the prepared native Windows bundle |
| SPIKE-REN-004 | accepted feasibility | local embedding and total network denial observed on Linux and Windows; production corpus belongs to Lot 2 |
| SPIKE-REN-005 | accepted feasibility | JavaScript/service workers disabled and untrusted fragment literalized; trusted static HTML implementation belongs to Lot 2 |
| SPIKE-REN-006 | pending | canonical profile/HTML/assets are fingerprinted and repeat exactly on Linux; Windows equality pending |
| SPIKE-REN-007 | pending | comparator and actionable diffs exist; native Windows/Linux page comparison pending |
| SPIKE-PKG-001 | direction accepted | portable ZIP selected under ADR-007; exact release-candidate tests remain later gates |
| SPIKE-PKG-002 | accepted | only-shell direction built/exercised natively and 38.2% obsolete compressed browser payload quantified |

## Commands and retained evidence

Commands ran from the repository on Linux x86_64 unless stated otherwise.

| Command | Exit | Result |
| --- | ---: | --- |
| system `python3 -m unittest tests.test_g1_spikes -v` | 1 | expected dependency failure: system Python lacks `markdown`; no test changed |
| `python3 spikes/g1/fetch_font_candidates.py --output-dir /tmp/libremark-g1-font-fetch-test` | 0 | fresh download verified all six fonts and six license records by size and SHA-256 |
| create `/tmp/libremark-g1-visual-venv`; install exact Markdown/Playwright/Pillow/PDFium | 0 | clean target-version visual environment |
| target Playwright `install --only-shell chromium` into `/tmp/libremark-playwright-1223` | 0 | Chromium 148.0.7778.96 revision 1223 plus FFmpeg 1011 |
| first sandboxed current visual probe | 1 | container syscall restriction: Chromium `sandbox_host_linux` operation not permitted |
| current visual probe outside the container syscall restriction | 0 | two pages; zero network attempts/responses |
| candidate visual probe | 0 | six verified embedded fonts; two pages; zero network attempts/responses |
| repeated candidate visual probe | 0 | fingerprints and page PNG hashes repeated exactly |
| current/candidate `appearance` comparison | 0 | report produced with `review` result |
| candidate/repeat threshold comparison | 0 | structural and visual result `pass` |
| target-environment `unittest tests.test_g1_spikes -v` | 0 | seven focused tests passed |

Temporary JSON evidence hashes:

- Linux current evidence:
  `2bb2b03f10bbcbd90b147ed4e6e6b1d69324eeaf9eb821f3c04dcfc189e788dc`;
- Linux candidate evidence:
  `fc95679a406fa2021c97927630e47d92f41fad98733a09e14b8d2720bafec087`;
- Linux repeated-candidate evidence:
  `008859cd7c236b17feb2edebdf5e496e342da28448f4e9a0bbe742c05df5c01e`;
- appearance report:
  `69c0452b4244d2175daa75caba09518e317305ad354e4ab018eb1fe439d216e2`;
- repeated-candidate comparison:
  `76076bef3aa877a80182130afff20829d564cc98200d4e334464a54e5fba5d6f`.

All generated evidence remains under `/tmp/libremark-g1-visual` and all font,
license, browser, and environment payloads remain under `/tmp`. None is a
source-controlled product resource or an official artifact.
