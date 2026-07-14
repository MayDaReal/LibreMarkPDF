# G1 renderer probes

This directory contains feasibility code only. It is not imported by
`libremark_pdf` and does not change production rendering.

`renderer_probe.py` checks deterministic logical fingerprints, literal
neutralization of an untrusted HTML fragment, JavaScript/service-worker browser
controls, a local data-only fixture, and deny-all routing for an attempted
remote image. Write generated JSON outside the repository:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/libremark-playwright-1223 \
  /tmp/libremark-g1-venv/bin/python spikes/g1/renderer_probe.py \
  --output /tmp/libremark-g1-renderer-probe.json
```

The probe is not the Lot 2 implementation. In particular, it does not parse and
embed arbitrary Markdown resources or sanitize trusted HTML.

## Candidate fonts and visual comparison

`font_candidates.json` preserves the six-file variable-font candidate that
failed the first Windows/Linux comparison. `font_candidates_static.json` is
the default second candidate: it separates proportional Regular and SemiBold
into static files and locks seven font files and four license records to
immutable upstream commits and SHA-256 values. Fetching is an explicit
spike-setup operation, never a conversion-time action:

```bash
python spikes/g1/fetch_font_candidates.py --output-dir /tmp/libremark-g1-font-set
python spikes/g1/fetch_font_candidates.py \
  --output-dir /tmp/libremark-g1-font-set --verify-only
```

Pass `--manifest spikes/g1/font_candidates.json` to reproduce the rejected
variable-font candidate. `visual_probe.py` accepts the corresponding
`--font-manifest` option.

`visual_probe.py` renders the representative fixture with either the unchanged
current font stack or the candidate embedded fonts. It denies HTTP/HTTPS,
disables JavaScript and service workers, records renderer/font/asset hashes,
extracts text, and rasterizes every PDF page at 144 DPI. Generated evidence must
be outside the repository.

`visual_compare.py` checks page geometry, extracted-text hashes, logical
fingerprints, global grayscale SSIM, changed-pixel percentage, and largest
eight-connected changed region against ADR-002. `appearance` mode records the
deliberate current-versus-candidate typography change for human review;
`cross-os` mode enforces the frozen thresholds.

On Windows, run the preparation phase while downloads are permitted, disable
the test host's network, and then run the evidence phase with the existing
revision-1223 browser payload:

```powershell
powershell -ExecutionPolicy Bypass -File spikes/g1/run_windows_visual_evidence.ps1 `
  -Mode Prepare -Python C:\path\to\python.exe `
  -FontRoot C:\temp\libremark-g1-font-set

powershell -ExecutionPolicy Bypass -File spikes/g1/run_windows_visual_evidence.ps1 `
  -Mode Run -Python C:\path\to\python.exe `
  -FontRoot C:\temp\libremark-g1-font-set `
  -BrowserRoot C:\path\to\playwright-browsers-1223 `
  -EvidenceRoot C:\temp\libremark-g1-windows-visual
```

The second command requires CPython 3.9 and the exact locked Markdown,
Playwright, Pillow, and PDFium versions. It produces a ZIP and its SHA-256 for
integrator review. It does not install dependencies or download a browser.
