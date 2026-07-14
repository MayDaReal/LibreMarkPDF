# Gate G1 renderer and packaging spike report

Status: **variable and unflagged static candidates rejected; flagged profile pending Windows**
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
| Renderer/browser | Python 3.9-compatible Playwright 1.60.0, Chromium/headless shell 148.0.7778.96 revision 1223, FFmpeg 1011, with `--disable-font-subpixel-positioning` in the measured profile | native Windows/Linux engine evidence exists; exact flagged Windows profile pending |
| Fonts | seven-file static-weight Noto replacement locked below | variable and unflagged static pairs failed; static commits, hashes, sizes, roles, and OFL records remain selected while the positioning profile is measured |
| Resources/network | embed accepted local resources before rendering; deny HTTP/HTTPS; disable JavaScript and service workers; literal safe HTML by default | Linux and Windows feasibility probes observed zero responses; production implementation is Lot 2 |
| Visual thresholds | ADR-002 remains unchanged pending its one permitted review: 144 DPI, SSIM >= 0.995, changed pixels <= 0.10% at RGB delta 16, largest changed region <= 0.50%, plus strict structural equality | two native pairs failed; integer positioning restores preliminary structural equality and isolates antialiasing variance; exact flagged pair and owner decision pending |
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

`spikes/g1/font_candidates.json` preserves the first machine-readable
variable-font candidate. Google
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
bytes. This set is rejected for cross-OS use but remains locked so its negative
evidence is reproducible. Actual redistribution notices are produced only when
Lot 2 chooses the final bundled subset.

`spikes/g1/font_candidates_static.json` is the replacement authority. It adds
the official Noto distribution commit
`11caf4e14799c87eadf02026f2bd17eec5d50adb` and separates proportional Regular
and SemiBold instead of asking each OS to instantiate one variable file.

| Role | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| proportional regular | `NotoSans-Regular.ttf` | 621,572 | `478c558ea716033cd60c03438f628dfa75694dcf6b5f6d505a2f05fd2b4f3823` |
| proportional semibold | `NotoSans-SemiBold.ttf` | 625,052 | `a4e91fd530ac2b4ef5367240144ff37d7d65d66cf76f2e9a2187b93c676f92d0` |
| monospace regular | `NotoSansMono-Regular.ttf` | 596,428 | `65b5e2b2c4a1fba9ae8be1f026cb35b03dcb8886d9b2a4147054fde12f7e767d` |
| Arabic/RTL fallback | `NotoSansArabic-Regular.ttf` | 234,892 | `bdff3e5659d67e67def05b33f749683b9376ae819d65d3dd62ac4640b3aaef48` |
| CJK fallback | `NotoSansCJKsc-Regular.otf` | 16,437,364 | `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b` |
| symbols fallback | `NotoSansSymbols2-Regular.ttf` | 1,233,128 | `7d5fb73b7ca67a6798101741f5d280a3d016a56a197afcd4199dbb57b4b82a21` |
| monochrome emoji fallback | `NotoEmoji.ttf` | 1,982,596 | `de6c18832938afc99caf132b39d6a30a19bac7f2e812e28db2535b4608d27551` |

The replacement totals 21,731,032 bytes. Its four unique OFL records total
24,371 bytes. CJK represents 75.6% of the font payload. Emoji remains a
variable upstream file but is fixed to CSS weight 400; its four exercised
glyphs must still pass the replacement native comparison.

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

The first native Windows archive has SHA-256
`f2e5e636c3e5676f38b270b5e970d2c38ddded0ae9933d234ea15691e0b63014`.
It records source commit `4107aea0d7d28a8bf9728d4a27854c5210393380`, a clean
status, Python 3.9.13, Playwright 1.60.0, PDFium 5.11.0, the exact browser and
font hashes, zero network requests/responses, and an exact same-Windows repeat.
All 18 payload hashes match the internal manifest values; its unusable `ea/`
path prefixes are a runner-relative-path defect, not content corruption.

The variable-font Windows/Linux comparison failed. Page 1 changed `4.2511%`
of pixels with SSIM `0.57125`; page 2 changed `5.8090%` with SSIM `0.42945`.
Extracted text also differed. PDF inspection explains the geometry change:
Windows embedded separate `NotoSans` and `NotoSans-SemiBold` instances while
Linux embedded only `NotoSans-Regular` from the variable file.

The static replacement then loaded all seven declared custom faces on Linux,
recorded profile fingerprint
`57528ca5490e3a7f255c85960417e313ebba91d08573b9fa78c9d34dcba4e450`,
HTML fingerprint
`a2fb435001bec8878f675623960cf121795bdd2c41411645316a46929f7cf1ed`,
and page hashes `b0d7c56f72438ff29b0e7a2bd4541cc8cdb2996465e7018b89aa03e5dbe3e8d5`
and `f0973141ad31f24c66b4edbf95778627b162e11b09531926797414f28aa5bd86`.
Its Linux repeat passed with SSIM `1.0`, zero changed pixels/region, identical
text, geometry, profile, and HTML.

The native static-font archive is 1,630,905 bytes with SHA-256
`53e96d0ab0fa7288475c882b293f2102dc6644359a6f0d104722a33a96e4c62a`.
It records source commit `93fbf83404339999064e7b09b18399ea9dfb4606`,
a clean status, Windows 11 Pro x64 build 26200, Python 3.9.13, the exact locked
package/browser/font hashes, all seven custom font faces, and zero attempted or
completed network requests. The owner confirmed that the physical Realtek
adapter was disconnected, DNS resolution failed, and TCP 443 was unavailable;
only local Hyper-V/VirtualBox adapters remained active. All 18 internal payload
hashes validate. Its Windows repeat has exact page pixels, text, geometry, and
fingerprints.

The unflagged static Windows/Linux comparison nevertheless failed. Page 1
changed `4.5371%` with SSIM `0.60230`; page 2 changed `6.2990%` with SSIM
`0.46773`. Extracted text differed. The report SHA-256 is
`c5f7c72598485dd3dec447d9225bf886a43d2e010f955fe2015ffdb50cb6f4b8`.
Rerasterizing both PDFs with the same Linux PDFium reproduced the same metrics,
so the difference originates in Chromium's platform text layout rather than
the inspection tool.

Launching the unchanged static set on Linux with
`--disable-font-subpixel-positioning` produced the exact two extracted-text
hashes and page dimensions of the retained Windows PDF. Two Linux executions
produced identical page hashes
`9805e313904485e15379e2cf9aefd0a1dfb75578bc352ffc8f1b4346c80c329b`
and `64e6fc6f407ebe542c2ae1c86ca9f43a4f37fab9324c57eafc9504b3978364b7`.
The flag is now part of the spike profile, whose fingerprint is
`6132c01cac337b07b2866650f40a2b0c4cb2b12b27ecd5774a4564ad13249450`.

The preliminary comparison against the retained Windows PDF is structurally
green but intentionally has unequal profile fingerprints because that Windows
run predates the flag record. Its raster metrics are `3.1196%`/`4.0963%`
changed pixels, SSIM `0.71837`/`0.70820`, and largest changed regions
`0.01732%`/`0.02224%`. The retained diffs show distributed glyph-edge variance,
not geometry shifts. This is the antialiasing case contemplated by ADR-002's
single amendment clause. No threshold is amended here: an exact flagged
Windows run and explicit owner decision are still mandatory.

For that decision, the provisional evidence-bounded amendment is SSIM at least
`0.70`, changed pixels at most `4.20%` at the unchanged delta of `16`, and
largest changed region at most `0.05%`, with every structural requirement still
exact. It passes the preliminary glyph-edge case while rejecting both measured
geometry failures: their SSIM values are at most `0.60230` and their largest
regions are at least `0.08618%`. These numbers are a proposal, not an accepted
contract, and must be recalculated if the exact flagged Windows result differs.

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
| SPIKE-REN-002 | accepted research/revised candidate | rejected variable set and seven-file static replacement have exact roles, commits, sizes, hashes, and OFL records |
| SPIKE-REN-003 | pending final profile | variable and unflagged static native pairs failed ADR-002; exact repeats exist on each platform; rerun the flagged Windows bundle |
| SPIKE-REN-004 | accepted feasibility | local embedding and total network denial observed on Linux and Windows; production corpus belongs to Lot 2 |
| SPIKE-REN-005 | accepted feasibility | JavaScript/service workers disabled and untrusted fragment literalized; trusted static HTML implementation belongs to Lot 2 |
| SPIKE-REN-006 | pending final profile | logical inputs match and the flagged profile repeats exactly on Linux; confirm its fingerprint on Windows |
| SPIKE-REN-007 | pending owner decision | both failed pairs have actionable diffs; preliminary integer positioning restores structure and isolates antialiasing |
| SPIKE-PKG-001 | direction accepted | portable ZIP selected under ADR-007; exact release-candidate tests remain later gates |
| SPIKE-PKG-002 | accepted | only-shell direction built/exercised natively and 38.2% obsolete compressed browser payload quantified |

## Commands and retained evidence

Commands ran from the repository on Linux x86_64 unless stated otherwise.

| Command | Exit | Result |
| --- | ---: | --- |
| system `python3 -m unittest tests.test_g1_spikes -v` | 1 | expected dependency failure: system Python lacks `markdown`; no test changed |
| first variable-font fetch | 0 | six fonts and six license records verified by size and SHA-256 |
| create `/tmp/libremark-g1-visual-venv`; install exact Markdown/Playwright/Pillow/PDFium | 0 | clean target-version visual environment |
| target Playwright `install --only-shell chromium` into `/tmp/libremark-playwright-1223` | 0 | Chromium 148.0.7778.96 revision 1223 plus FFmpeg 1011 |
| first sandboxed current visual probe | 1 | container syscall restriction: Chromium `sandbox_host_linux` operation not permitted |
| current visual probe outside the container syscall restriction | 0 | two pages; zero network attempts/responses |
| candidate visual probe | 0 | six verified embedded fonts; two pages; zero network attempts/responses |
| repeated candidate visual probe | 0 | fingerprints and page PNG hashes repeated exactly |
| current/candidate `appearance` comparison | 0 | report produced with `review` result |
| candidate/repeat threshold comparison | 0 | structural and visual result `pass` |
| inspect Windows archive and recompute its 18 payload hashes | 0 | ZIP hash `f2e5e636...b63014`; content intact; `ea/` relative-path defect identified |
| variable-font Windows/Linux threshold comparison | 1 | correctly rejected by structural and visual criteria |
| static candidate fetch and two Linux probes | 0 each | seven fonts/four licenses verified; all glyphs custom; zero render-time network |
| static candidate/repeat threshold comparison | 0 | structural and visual result `pass`, SSIM 1.0 and zero delta |
| inspect static Windows archive and validate its 18 payload hashes | 0 | ZIP hash `53e96d0a...e4c62a`; clean exact source/dependencies, offline confirmation, zero network, exact repeat |
| unflagged static Windows/Linux threshold comparison | 1 | correctly rejected structurally and visually; report hash `c5f7c725...b6f4b8` |
| rerasterize both static PDFs with one Linux PDFium | 0 | reproduces the cross-OS metrics, excluding inspection-platform variance |
| two static Linux probes with integer positioning | 0 each | exact repeat; extracted text and page dimensions equal retained Windows; aligned layout in retained diffs; flag recorded in profile fingerprint |
| preliminary flagged-Linux/unflagged-Windows comparison | 1 | structural pass; raster thresholds fail on distributed glyph-edge variance; exact flagged Windows profile still required |
| target-environment `unittest tests.test_g1_spikes -v` | 0 | nine focused tests passed |

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
- exact-version static candidate evidence:
  `338dfbe251bc0bf5d2f1d39c947b1550b850effbcc6b7deaa97f02b92fb4b9a2`;
- exact-version static repeated-candidate evidence:
  `3c2b86ec737ea554a9a085f1f209ac0b652559a2644b116eb7db6ebc58852135`;
- static repeated-candidate comparison:
  `76076bef3aa877a80182130afff20829d564cc98200d4e334464a54e5fba5d6f`.
- rejected variable-font Windows/Linux comparison:
  `2d26a25621e879f80bead208af22326ad32199943b56c599a443221fd1916174`.
- rejected unflagged static-font Windows/Linux comparison:
  `c5f7c72598485dd3dec447d9225bf886a43d2e010f955fe2015ffdb50cb6f4b8`;
- preliminary integer-positioned Linux/retained Windows comparison:
  `d447db7455145df0621fa809a5bc38822706fe04b53891279a9e8ba7d6bd098b`.

All generated evidence remains under `/tmp`; the supplied Windows ZIP remains
outside the repository under `/shared/repos/LibreMarkPDF-artifact`. No font,
license, browser, PDF, PNG, diff, or archive is a
source-controlled product resource or an official artifact.
