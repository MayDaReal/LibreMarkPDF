# Target architecture and distribution decision

Status: **proposed architecture decision for backlog execution**
Decision date: **2026-07-13**

## Decision

Keep the existing Python package, shared conversion engine, Playwright, and
Chromium for the reliability program. Do not rewrite the product as a web,
Electron, or Tauri application before the deterministic-rendering and official
release gates are met.

Introduce one versioned internal `RenderProfile` as the source of truth for all
rendering inputs. The GUI, CLI, and agent skill must use the same public core
API and the same profile.

Build, test, and publish a separate standalone artifact for each advertised
operating system and architecture. The initial mandatory release target is
Windows x64. Linux and macOS become advertised only when their native release
gates pass.

## Why a web rewrite is not the shortcut

- A Windows `.exe` cannot execute natively on Linux or macOS. A single web
  codebase still needs either a browser or a platform-specific desktop shell.
- A browser application cannot use Chromium's automated `page.pdf()` API.
  Browser print dialogs and installed browser versions are user-controlled and
  cannot guarantee the same output.
- A hosted renderer could use one canonical engine, but it would require file
  upload, a network connection, infrastructure, and a privacy policy. That
  contradicts the local-first product contract.
- Electron embeds Chromium and can share a JavaScript codebase, but still
  produces OS-specific artifacts. Rewriting the mature core would add migration
  and security risk without eliminating platform-specific validation.
- Tauri uses the operating system webview by default, which makes renderer
  parity harder unless an additional fixed PDF engine is bundled.

A browser-based companion may be considered later for discovery or lightweight
preview, but it must not define or replace the canonical PDF engine.

## Render profile

The profile must expose a stable identifier and fingerprint and contain at
least:

- profile schema and profile version;
- exact Python-Markdown version and enabled extensions;
- exact Playwright version and Chromium revision;
- paper format, orientation, margins, scale, media mode, and background policy;
- locale, time zone, color scheme, and explicit test date;
- default theme identifier and version;
- SHA-256 hashes for CSS, icons, fonts, and other renderer assets;
- embedded proportional, semibold, monospace, and Unicode fallback fonts;
- raw HTML and JavaScript policy;
- local resource base and allowed media types;
- network policy and explicit opt-in rules;
- renderer timeouts and maximum resource/document sizes.

The JSON CLI result should expose `render_profile`, engine version, theme
identifier/version, and renderer fingerprint so a PDF can be diagnosed later.

## Deterministic resource model

1. Resolve a file conversion's relative resources from the Markdown file's
   parent directory.
2. Validate supported image/media types and size limits.
3. Embed accepted resources as data URIs before Chromium receives the HTML.
4. Reject missing or forbidden resources with a stable actionable error.
5. Deny all external network requests by default.
6. Disable JavaScript and service workers by default.
7. Define a documented compatibility option if trusted raw HTML or network
   access must be supported. Unsafe modes must never be the default.
8. Wait for bundled fonts and local images to be ready before creating the PDF.

## Font decision

The current CSS selects different installed fonts on different operating
systems. It is therefore impossible to preserve all current platform-specific
renderings and make them identical at the same time.

Select redistributable font files after a visual review against the current
default output. Bundle the selected regular, semibold, monospace, and required
Unicode fallback faces. Declare them with `@font-face`, use them in the document
and header/footer templates, and record licenses and hashes.

The first release using the fixed font set creates the canonical default-theme
baseline. Any later change to a font, renderer, Markdown extension, or default
CSS requires a render-profile version change and an explicitly reviewed golden
update.

## Equality contract

The project promises visual and structural equivalence, not identical PDF
bytes. For a versioned canonical fixture corpus, every supported official
artifact must have:

- identical page count and page dimensions;
- identical extracted text and order;
- identical headings, links, image inventory, and header/footer values;
- identical pagination, table geometry, line breaks, and image placement;
- exact canonical pre-render HTML and render-profile fingerprint;
- raster comparison at 144 DPI with SSIM at least `0.70`;
- at most `4.20%` of pixels exceeding an RGB-channel delta of `16`;
- no contiguous changed region larger than `0.05%` of a page;
- no semantic, missing-resource, or pagination difference, regardless of image
  metric results.

The one permitted antialiasing review was completed from an exact native
Windows/Linux pair and is recorded in ADR-002. These thresholds are frozen
before implementation release candidates are scored. Any later change requires
a superseding ADR and explicit golden review.

Byte-for-byte PDF equality is not required. Creation timestamps, document IDs,
compression, and object serialization can differ without a user-visible change.

## Canonical fixture corpus

Maintain at least 30 versioned Markdown documents covering:

- headings, emphasis, nested and sane lists;
- wide, narrow, long, and multi-page tables;
- fenced and inline code, including status emoji literals;
- relative PNG, JPEG, SVG, GIF policy, data URI, and missing images;
- links, autolink policy, footnotes, and raw HTML policy;
- explicit page breaks and long unbreakable strings;
- EN/FR accents, multiple Unicode ranges, CJK, RTL, and emoji fallbacks;
- header/footer tokens and fixed test dates;
- custom and community themes;
- very small, large, malformed, and limit-exceeding inputs;
- duplicate stems, output collisions, paths with spaces, and Unicode paths.

Golden updates require a dedicated pull request label, before/after image
artifacts, an explanation, and reviewer approval.

## Distribution targets

### Windows x64 — mandatory first official target

- Standalone portable artifact requiring no Python or browser installation.
- Measure one-file startup and antivirus behavior against a portable zipped
  directory before choosing the primary format.
- Provide separate GUI and console entry points if needed to preserve reliable
  stdout/stderr behavior.
- Bundle only the Chromium payload actually used by the renderer.
- Sign the release with Authenticode when release credentials are available.
- Validate on a clean supported Windows VM, outside the repository, from a path
  with spaces, offline, without Playwright cache, and without Python.

### Linux x86_64 — advertise only after its gate passes

- Prefer an AppImage for the no-install path and a portable tarball as fallback.
- Build against a documented compatibility baseline.
- Test a declared distribution matrix and Chromium system dependencies.
- Do not claim support for every Linux distribution.

### macOS arm64 and x86_64 — future gated targets

- Build natively for each advertised architecture; use universal2 only if all
  nested Chromium and Python components are demonstrably compatible.
- Produce a signed `.app` in a notarized and stapled `.dmg` or zip.
- Validate Chromium nested-code signing, hardened runtime, CLI behavior, Gatekeeper,
  offline rendering, and a clean Mac launch.
- Do not advertise macOS until real hardware or suitable macOS runners and Apple
  signing/notarization credentials are available.

## Release contents and evidence

Every official release must publish:

- immutable versioned artifacts per OS/architecture;
- SHA-256 checksums;
- signatures where supported;
- CycloneDX or SPDX SBOM;
- dependency and bundled-font license notices;
- build provenance/attestation;
- render profile and renderer fingerprint;
- test report and cross-platform golden comparison report;
- direct download links with no account or email requirement;
- known limitations and supported platform versions.

No build is an official release merely because PyInstaller, AppImage, or another
packager completed successfully.

## Theme packages

Community themes are local, versioned, offline packages. A theme contains a
manifest, CSS, preview fixture, generated preview, assets, licenses, and hashes.
The validator rejects missing licenses, external URLs, scripts, path traversal,
unsupported files, duplicate identifiers, and incompatible renderer profiles.

Keep the existing `style.css` as the compatibility source for `default@1` until
the fixed-font baseline is deliberately approved. Never silently replace the
default theme when installing a community theme.

## Architecture gates

The architecture is accepted only after a spike proves:

1. A clean locked environment resolves the exact declared renderer and browser.
2. All runtime network requests are blocked and zero requests are observed.
3. Local images and bundled fonts render correctly.
4. Two clean builds produce the same renderer fingerprint.
5. The Windows standalone artifact passes GUI, CLI, preview, batch, offline, and
   external-path smoke tests.
6. The fixture harness produces actionable page-by-page reports.
7. At least two target operating systems meet the frozen visual-equivalence
   thresholds before cross-platform parity is advertised.

## Risks requiring explicit owner decisions

- Code-signing certificates and macOS notarization have financial and secret
  management requirements.
- One-file extraction may cause slow startup and antivirus false positives.
- Large Unicode font coverage increases artifact size.
- Linux Chromium dependencies may prevent a universal no-install artifact.
- Raw HTML compatibility conflicts with safe handling of untrusted Markdown.
- A brand rename must be legally and registry-checked and should not be coupled
  to renderer changes in the same integration change.
