# LibreMark PDF

LibreMark PDF converts UTF-8 Markdown files into styled A4 PDFs on the local
computer. One shared engine serves a desktop GUI, a non-interactive CLI, and the
agent contract in [`SKILL.md`](SKILL.md).

> **Project status:** pre-release prototype. No official standalone download is
> published yet. Build scripts are provided for development and validation;
> they are not evidence of a supported release.

## Features

- batch conversion from `.md` and `.markdown` files;
- adaptive file selection with optional drag-and-drop, explicit ignored-item
  feedback, and an independently selectable preview file;
- responsive multipage preview with explicit empty, updating, ready, and error
  states, an active-file label, 50–200% zoom, scrolling, and panning;
- versioned local themes, the compatible `default@1` style, or a user-supplied
  CSS file;
- four summarized desktop setting sections for style, destination, six
  header/footer positions, date, and trusted static HTML;
- English and French desktop interface;
- compact in-window version access with local, copyable technical identities;
- cancellable per-file batch progress, explicit close and collision choices,
  and persistent success, failure, and cancellation results;
- deterministic JSON output and meaningful exit status for automation.

User guides: [English](docs/MANUAL_EN.md) · [Français](docs/MANUEL_FR.md)

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

The historical reliability programme is preserved by the local Git tag
`reliability-evidence-2026-07`. It is not required reading for normal work.

## Run from source

Prerequisites: CPython 3.9, Tk for the GUI, and network access for the initial
dependency/browser acquisition. Start with the platform bootstrap:

```powershell
.\bootstrap-windows.ps1
```

```bash
./bootstrap-linux.sh
```

The bootstraps create a locked environment and stage the exact Chromium
payload in the platform-specific ignored directory `browser-win/` or
`browser-linux/`. The payloads are native and must not be shared between
operating systems.

By default, an interactive bootstrap asks before installing a missing Python
or GNU Make. Explicit options are useful for automation:

```powershell
.\bootstrap-windows.ps1 -InstallPython -InstallMake
```

```bash
./bootstrap-linux.sh --install-python --install-make
```

Use `-NonInteractive` on Windows or `--non-interactive` on Linux to disable
questions; without the explicit install options, missing tools then cause an
error or remain optional. Reopen PowerShell after GNU Make installation if
`make` is not yet on `PATH`. GNU Make exposes
`make test`, `make test-ui`, and native validation shortcuts.

```bash
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium

# GUI
python -m libremark_pdf

# CLI
python -m libremark_pdf convert report.md --json
```

On Windows, the locked environment is `.venv-windows-py39`; activate it with
`.venv-windows-py39\Scripts\Activate.ps1`. The Linux environment is
`.venv-linux-py39`.

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

Run `make build-windows` from the locked environment created by
`bootstrap-windows.ps1`. Without GNU Make, call
`tools\build-windows-artifact.bat` directly. Validate the complete candidate
with `make validate-windows`.

The portable candidate provides `LibreMarkPDF.exe` for the no-console GUI,
`LibreMarkPDF-cli.exe` for authoritative CLI streams, and
`LibreMarkPDF-debug.exe` for GUI startup diagnostics. No candidate is an
official release until its retained native evidence passes the applicable
gates.

### Linux

Prepare the hash-locked CPython 3.9 x86_64 environment and exact browser
payload with `bootstrap-linux.sh`, then run `make build-linux`. Without GNU
Make, call:

```bash
export LIBREMARK_PDF_PYTHON="$PWD/.venv-linux-py39/bin/python"
export LIBREMARK_PDF_BROWSER_SOURCE=/absolute/staging/browser
./tools/build-linux-artifact.sh
```

The candidate is `dist/LibreMarkPDF-linux-x86_64-candidate.tar.gz`. It expands
to an onedir layout with `LibreMarkPDF` (GUI), `LibreMarkPDF-cli`
(authoritative streams), and `LibreMarkPDF-debug` (diagnostic GUI). The
tarball avoids FUSE but still requires compatible glibc and Chromium host
libraries. Linux is not advertised as supported or portable until its
independent native validation passes.

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
available through **Other advanced options** in the desktop
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
Dependency and bundled-resource licenses must be verified and included before
an official binary is published.
