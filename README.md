# LibreMark PDF

LibreMark PDF converts UTF-8 Markdown files into styled A4 PDFs on the local
computer. One shared engine serves a desktop GUI, a non-interactive CLI, and the
agent contract in [`SKILL.md`](SKILL.md).

> **Project status:** `0.1.0rc1` is the first public release candidate. Download
> the validated Windows x64 and Ubuntu 24.04 x86_64 artifacts from the
> [`v0.1.0rc1` release](https://github.com/MayDaReal/LibreMarkPDF/releases/tag/v0.1.0rc1).
> This is a pre-release, not the stable `v0.1.0` release. The Windows archive is
> not Authenticode-signed; signed checksums and native validation evidence are
> attached to the release. Verification instructions and the release public key
> are documented in [`docs/RELEASE.md`](docs/RELEASE.md#release-checksum-signature).

## Features

- batch conversion from `.md` and `.markdown` files;
- modern file cards with optional drag-and-drop, exact mixed-add feedback,
  keyboard navigation, direct folder/copy/remove actions at every responsive
  width, and an independently identified active preview
  file;
- responsive multipage preview with explicit empty, scheduled, rendering,
  ready, error, and unavailable states, an active-file label, 10–200% zoom in
  2-point steps,
  fit-page behavior when the active document changes, fit-page/fit-width
  actions, an explicit refresh-and-fit reset, scrolling, panning, and local
  error reporting;
- versioned local themes, the compatible `default@1` style, or a user-supplied
  CSS file;
- four summarized desktop setting sections for style, destination, six
  header/footer positions, date, and trusted static HTML, with complete
  tooltips for long values; all four sections have responsive draft editors
  with session Save/Cancel semantics;
- compact navigation at 759 px and below with persistent Files, Preview,
  Settings, and Results tabs, one visible content panel, and a fixed
  full-width generate/progress area;
- English and French desktop interface;
- a fixed modern header with native Help and language menus; compact windows
  use one keyboard-accessible application menu for the manual, shortcuts,
  language, problem reporting, and About;
- responsive keyboard-shortcut and About dialogs with structured local
  identities, exact technical-information copy, local third-party notices,
  and safe focus restoration;
- an editable local problem report with opt-in anonymized diagnostics, copy,
  and UTF-8 save actions, with no automatic submission;
- a fixed, non-modal action bar with compact per-output replacement decisions,
  exact completed-file progress plus live engine phases, applied-option details, safe
  stop-after-current or cooperative immediate cancellation, terminal summaries,
  and persistent results;
- responsive persistent results with a collapsible, vertically resizable
  full-width lower panel on normal and large windows, vertical cards on compact
  windows, compact icon actions, an explicit neutral state for existing PDFs
  kept by user choice, expandable technical details, and clearing that never
  deletes generated PDFs; Files absorbs the available height above fixed
  Settings, while the vertical divider lets the left workspace grow up to the
  Preview limit;
- deterministic JSON output and meaningful exit status for automation.

Tracked user-guide sources: [English Markdown](docs/MANUAL_EN.md) ·
[Markdown français](docs/MANUEL_FR.md). Native candidate builds generate and
package the matching local PDF guides with LibreMark PDF itself and `style.css`.

## Find the right document

Most users only need this README and one of the user guides. Contributors can
start with [`CONTRIBUTING.md`](CONTRIBUTING.md), then use the focused policy
documents below as needed:

| Need | Canonical document |
| --- | --- |
| Report a bug or request support | [`SUPPORT.md`](SUPPORT.md) |
| Report a security vulnerability | [`SECURITY.md`](SECURITY.md) |
| Understand review and release decisions | [`GOVERNANCE.md`](GOVERNANCE.md) |
| See planned work | [`ROADMAP.md`](ROADMAP.md) |
| Check user-facing documentation parity | [`docs/DOCUMENTATION_SYNC.md`](docs/DOCUMENTATION_SYNC.md) |
| Build, test, and release candidates | [`docs/VALIDATION.md`](docs/VALIDATION.md) · [`docs/RELEASE.md`](docs/RELEASE.md) |
| Platform status and limits | [`docs/PLATFORM_SUPPORT.md`](docs/PLATFORM_SUPPORT.md) |

## Run from source

For Ubuntu 24.04 x86_64, install standard CPython 3.14 with Tk, then run
`./bootstrap-linux.sh`. Use CPython 3.14.10 for migration validation. The
bootstrap detects an installed pyenv runtime, or accepts an explicit
interpreter with `PYTHON=/path/to/python3.14`. Initial setup downloads locked
wheels and stages Chromium in `browser-linux/`.

```bash
./bootstrap-linux.sh --non-interactive
. .venv-linux-py314/bin/activate

# GUI
python -m libremark_pdf

# CLI
python -m libremark_pdf convert report.md --json
```

On Windows x64, install standard CPython 3.14 with Tk and run
`powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap-windows.ps1`.
The script prepares `.venv-windows-py314` and stages Chromium in
`browser-win/`. Pass `-Python <path>` to select an interpreter, then use
`.\.venv-windows-py314\Scripts\python.exe -m libremark_pdf` to run the GUI.

## CLI examples

```bash
# Create report.pdf next to report.md
python -m libremark_pdf convert report.md

# Select an output and custom footer
python -m libremark_pdf convert report.md -o output.pdf \
  --footer-center "Page {page} / {total}"

# Convert a batch and return machine-readable results
python -m libremark_pdf convert a.md b.md --out-dir pdfs --json

# Reproducible date and explicit replacement of an existing PDF
python -m libremark_pdf convert report.md --date 2026-07-14 --overwrite

# Inspect pinned identities without launching or downloading Chromium
python -m libremark_pdf --version
python -m libremark_pdf doctor --json

# Inspect or select a validated local theme
python -m libremark_pdf theme list --json
python -m libremark_pdf convert report.md --theme default@1 --json
```

Run `python -m libremark_pdf convert --help` for every option. A successful
command exits `0`; validation or conversion failure exits nonzero. JSON is
written to stdout with no diagnostic noise, while human-readable errors are
written to stderr. The conversion contract is described by
[`docs/CLI_JSON_SCHEMA.json`](docs/CLI_JSON_SCHEMA.json). The legacy
`--render-date` spelling remains an alias of `--date`.

## Headers and footers

The top and bottom of each page each have left, center, and right fields. The
default footer is `Page {page} / {total}`.

| Token | Value |
| --- | --- |
| `{titre}` or `{title}` | First level-one heading |
| `{date}` | UTC render date in `YYYY-MM-DD` format (or `--date`) |
| `{page}` | Current page number |
| `{total}` | Total page count |

## Build a local artifact

Dependency and browser acquisition may require network. The authoritative
candidate build steps consume already staged inputs and perform no download.
Conversion runs locally with the bundled resources.

### Windows

The initial `v0.1.0` release scope includes Windows x64 and Ubuntu 24.04
x86_64. Each artifact must pass its own native release gate. macOS is not
included in that support promise.

Run `make build-windows` after preparing the native locked environment with
`bootstrap-windows.ps1`. Without GNU Make, call
`tools\build-windows-artifact.bat` directly. Validate the complete candidate
with `make validate-windows`.

The portable candidate provides `LibreMarkPDF.exe` for the no-console GUI,
`LibreMarkPDF-cli.exe` for authoritative CLI streams, and
`LibreMarkPDF-debug.exe` for GUI startup diagnostics. No candidate is an
official release until its retained native evidence passes the applicable
gates. The build generates `MANUAL_EN.pdf` and `MANUEL_FR.pdf` from the tracked
Markdown guides and packages them under `docs/`; generated PDFs are not source
files and are never committed.

### Linux

Prepare the hash-locked CPython 3.14 x86_64 environment and exact browser
payload with `bootstrap-linux.sh`, then run `make build-linux`. Without GNU
Make, call:

```bash
export LIBREMARK_PDF_PYTHON="$PWD/.venv-linux-py314/bin/python"
export LIBREMARK_PDF_BROWSER_SOURCE=/absolute/staging/browser
./tools/build-linux-artifact.sh
```

The candidate is
`dist/<version>/linux-x86_64/artifacts/LibreMarkPDF-linux-x86_64-candidate.tar.gz`.
It expands to an onedir layout with `LibreMarkPDF` (GUI), `LibreMarkPDF-cli`
(authoritative streams), and `LibreMarkPDF-debug` (diagnostic GUI). The
tarball avoids FUSE but still requires compatible glibc and Chromium host
libraries. The initial Linux support promise is limited to validated Ubuntu
24.04 x86_64 candidates; it does not imply compatibility with other Linux
distributions, versions, architectures, desktop environments, or display
servers.

## Architecture

```text
GUI ─┐
CLI ─┼─> libremark_pdf/core.py ─> Markdown/HTML ─> Chromium ─> PDF
Skill┘                                           └> PDFium ─> preview PNG
```

`libremark_pdf/core.py` is the only reusable conversion engine. Runtime files
are in `style.css`, `icons/`, `assets/`, `fonts/`, and the generated
platform-specific browser tree.
See [`AGENTS.md`](AGENTS.md) for contribution rules and
[`docs/VALIDATION.md`](docs/VALIDATION.md) for the active validation workflow.

## Current security limitations

Default conversion treats raw HTML as literal Markdown text, validates and
embeds approved local images, blocks active/network-capable HTML and CSS, and
does not replace existing output without `--overwrite`. Trusted HTML is
available through **Advanced options** in the desktop
interface after a first-use confirmation, and through the CLI
`--trusted-html` option. Both allow only the documented static HTML subset;
scripts, event handlers, frames, resource loaders, and network or `file:` URLs
remain blocked. Custom CSS cannot load resources. These controls do not make
untrusted documents harmless in every respect; review document content before
conversion.

Community themes are validated local directories with a versioned manifest,
file hashes, licences, and declared render-profile compatibility. Installation,
replacement, and removal are atomic; remote URLs, scripts, traversal, and
unlicensed packages are rejected. See
[`docs/THEME_CONTRIBUTING.md`](docs/THEME_CONTRIBUTING.md).

## License

LibreMark PDF source code is released under the [MIT License](LICENSE).
Bundled-resource and dependency notices are recorded in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md); candidate SBOMs are attached
to each native release.
