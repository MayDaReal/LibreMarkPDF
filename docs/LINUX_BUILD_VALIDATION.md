# Linux x86_64 G3 candidate build and validation

This guide defines the optional Linux G3 candidate lane. Linux is not an
advertised or officially supported platform until every distribution/version
and architecture named by a later release decision passes its own native Gate
G4. The mandatory Windows lane remains independent.

## Candidate scope and baseline

The current implementation candidate is:

- architecture: x86_64 only;
- build interpreter: CPython 3.9;
- build host under test: Ubuntu 24.04.4 LTS x86_64 with glibc 2.39;
- renderer: Playwright 1.60.0, Chromium headless shell 148.0.7778.96 revision
  1223;
- format: PyInstaller onedir compressed as
  `LibreMarkPDF-linux-x86_64-candidate.tar.gz`.

This is a test baseline, not a support promise. Ubuntu 22.04, Debian, Fedora,
Arch, other versions, other C libraries and other architectures remain
unverified until exact native evidence is retained for them. Building on glibc
2.39 does not imply compatibility with older glibc.

The candidate directory contains:

- `LibreMarkPDF`: GUI entry without a terminal contract;
- `LibreMarkPDF-cli`: authoritative CLI stdout/stderr entry;
- `LibreMarkPDF-debug`: GUI entry with diagnostic streams;
- `_internal/`: exact Python, PDFium, browser, fonts, themes, icons, licences
  and frozen resources.

Copy or extract the complete directory. A top-level executable without
`_internal/` is not a valid artifact.

## AppImage versus portable tarball

The onedir tarball is the G3 implementation candidate because it:

- needs no FUSE device, mount helper or AppImage extraction fallback;
- preserves the complete PyInstaller resource layout directly;
- exposes distinct GUI, CLI and diagnostic entry paths;
- can be inspected with ordinary `tar`, `sha256sum`, `ldd` and `readelf`;
- makes host-library requirements visible rather than implying universal
  Linux portability.

An AppImage could offer a single clickable file and desktop integration, but
it adds an AppImage runtime, FUSE 2/3 and mount-policy variation. Hosts without
`/dev/fuse` may require `--appimage-extract-and-run`, and sandbox or
container policies can still block Chromium. On the initial Ubuntu evidence
host, `appimagetool` and `/dev/fuse` are absent, so no AppImage behavior has
been claimed. Reconsider AppImage only with a pinned builder, licence/SBOM
inventory, direct mount and extraction-fallback evidence on the declared
matrix.

## Locked preparation

Acquisition is separate from the candidate build and may require network.
Using CPython 3.9 x86_64:

```bash
python3.9 -m venv .venv-linux-g3
. .venv-linux-g3/bin/activate
python -m pip install --require-hashes \
  -r requirements/locks/linux-x86_64-py39.txt
export PLAYWRIGHT_BROWSERS_PATH=/absolute/staging/browser
python -m playwright install --only-shell chromium
```

The browser staging root must contain only the approved
`chromium_headless_shell-1223` payload (plus its matching FFmpeg payload).
Perform acquisition before disconnecting the test host.

The authoritative build itself is offline and has no elevation path:

```bash
export LIBREMARK_PDF_PYTHON="$PWD/.venv-linux-g3/bin/python"
export LIBREMARK_PDF_BROWSER_SOURCE="$PLAYWRIGHT_BROWSERS_PATH"
./build_linux_portable.sh
```

It refuses the wrong OS, architecture, Python/PyInstaller versions, dependency
lock or browser revision. It never runs `pip install`, `playwright install`,
`install-deps`, `sudo` or a package manager.

## Required host libraries

Python and application resources are frozen, but glibc, the dynamic loader and
Chromium desktop libraries remain host dependencies. The exact bundled
browser carries `deb.deps` and `rpm.deps`; the evidence runner also executes
`ldd` over every ELF object and fails on any `not found` result.

The Debian-family browser list includes NSS/NSPR, GLib/GObject/GIO,
ATK/AT-SPI, D-Bus, X11/XCB/XComposite/XDamage/XFixes/XRandR, GBM/DRM,
libxkbcommon, ALSA, expat, udev, GTK, Cairo, Pango, CUPS and Vulkan libraries.
Package names vary by distribution. Do not copy an `apt` command to another
distribution or request elevation from the evidence runner; a native matrix
owner must prepare each host using its normal administration process.

`linux-artifact-dependencies.json` records every ELF, unresolved library and
maximum referenced glibc symbol. The highest observed symbol is evidence for
that exact build, not proof that every system with that glibc number has the
remaining libraries or a compatible desktop.

## Chromium sandbox and FUSE

Playwright 1.60.0 adds `--no-sandbox` unless `chromium_sandbox=True` is
explicit. LibreMark PDF currently uses Playwright's default and the headless
shell payload has no `chrome-sandbox` setuid helper. The renderer still blocks
runtime network requests and active document content, but those controls are
not a process sandbox. This behavior must be disclosed and reassessed before
advertising Linux; it must not be hidden by a packaging claim.

The tarball does not use FUSE. The runner records `/dev/fuse`, `fusermount`,
`fusermount3` and unprivileged-user-namespace state solely to make the
AppImage comparison and Chromium host policy reproducible.

## Exact candidate evidence

Run from a clean checkout at the signed commit. Select an evidence directory
outside the checkout. Physically disconnect non-loopback interfaces before
using `--require-offline`:

```bash
tools/run_g3_linux_candidate.sh \
  --evidence-root "/tmp/G3 Evidence/LibreMark PDF – Linux x86_64" \
  --python "$PWD/.venv-linux-g3/bin/python" \
  --browser-source "$PLAYWRIGHT_BROWSERS_PATH" \
  --require-offline
```

The runner requires a normal unprivileged user and never changes network,
mount, sandbox or system-package policy. It records source/host/lock hashes,
runs the full suite, builds the exact candidate, copies it to a Unicode-and-
space path, and exercises it with an empty home/cache and a `PATH` containing
no Python. It checks CLI JSON success, missing input, partial batch, collision,
permissions and `default@1`; starts GUI and diagnostic entries under Xvfb;
runs the immutable canonical comparison; scans ELF dependencies; creates an
SPDX 2.3 SBOM, normalized tarball, hashes and evidence archive.

Automation cannot prove real desktop accessibility or integration. Complete
the generated `manual-linux-gui-review.md` on every declared desktop/display
server and retain screenshots or video.

## Gate decision

Use `LINUX G3 PASSED` only after `LNX-001` through `LNX-005` have exact
reproducible evidence on every declared native host and the human GUI review is
complete. Otherwise use `LINUX G3 NOT YET PASSED` and list the exact host,
command or human decision still required.

The separate open G2 PDFium `23-unicode` limitation must be disclosed in the
canonical report. It is not to be normalized, weakened or claimed closed by
this lane.
