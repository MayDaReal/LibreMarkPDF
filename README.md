# LibreMark PDF

LibreMark PDF converts UTF-8 Markdown files into styled A4 PDFs on the local
computer. One shared engine serves a desktop GUI, a non-interactive CLI, and the
agent contract in [`SKILL.md`](SKILL.md).

> **Project status:** pre-release prototype. No official standalone download is
> published yet. Build scripts are provided for development and validation;
> they are not evidence of a supported release.

## Features

- batch conversion from `.md` and `.markdown` files;
- responsive, scrollable, zoomable first-page preview in the desktop app;
- versioned local themes, the compatible `default@1` style, or a user-supplied
  CSS file;
- six header/footer positions with page, title, and date tokens;
- English and French desktop interface;
- cancellable batch progress and pre-conversion collision choices;
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
| Inspect reliability decisions and evidence | [`docs/project-reliability/README.md`](docs/project-reliability/README.md) |

The reliability directory contains audit records, accepted architecture
decisions, and gate evidence. It is deliberately detailed for maintainers and
auditors; it is not required reading for an ordinary documentation or code
contribution.

## Run from source

Prerequisites: Python 3.9+, Tk for the GUI, and the Python dependencies listed
in `requirements.txt`.

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

On Windows, activate with `venv\Scripts\activate` and use `python` in place of
`python3`.

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

1. Prepare the hash-locked Python 3.9 environment and exact Chromium described
   by the validation guide.
2. Run `build_portable.bat` from a clean native Windows x64 checkout.
3. Test the complete `dist\LibreMarkPDF` directory with
   [`docs/WINDOWS_BUILD_VALIDATION.md`](docs/WINDOWS_BUILD_VALIDATION.md).

The portable candidate provides `LibreMarkPDF.exe` for the no-console GUI,
`LibreMarkPDF-cli.exe` for authoritative CLI streams, and
`LibreMarkPDF-debug.exe` for GUI startup diagnostics. No candidate is an
official release until its retained native evidence passes the applicable
gates.

### Linux

Prepare the hash-locked CPython 3.9 x86_64 environment and exact browser
payload described by the
[`Linux validation guide`](docs/LINUX_BUILD_VALIDATION.md), then run:

```bash
export LIBREMARK_PDF_PYTHON="$PWD/.venv-linux-g3/bin/python"
export LIBREMARK_PDF_BROWSER_SOURCE=/absolute/staging/browser
./build_linux_portable.sh
```

The candidate is `dist/LibreMarkPDF-linux-x86_64-candidate.tar.gz`. It expands
to an onedir layout with `LibreMarkPDF` (GUI), `LibreMarkPDF-cli`
(authoritative streams), and `LibreMarkPDF-debug` (diagnostic GUI). The
tarball avoids FUSE but still requires compatible glibc and Chromium host
libraries. Linux is not advertised as supported or portable until its
independent native matrix gate passes.

## Architecture

```text
GUI ─┐
CLI ─┼─> libremark_pdf/core.py ─> Markdown/HTML ─> Chromium ─> PDF
Skill┘                                           └> PDFium ─> preview PNG
```

`libremark_pdf/core.py` is the only reusable conversion engine. Runtime files
are in `style.css`, `icons/`, `assets/`, `fonts/`, and the generated `browsers/`
tree.
See [`AGENTS.md`](AGENTS.md) for contribution rules and
[`docs/project-reliability/README.md`](docs/project-reliability/README.md) for
the gated reliability program and its reading paths.

## Current security limitations

Default conversion treats raw HTML as literal Markdown text, validates and
embeds approved local images, blocks active/network-capable HTML and CSS, and
does not replace existing output without `--overwrite`. The exceptional
`--trusted-html` CLI mode allows only the documented static HTML subset; it
still blocks scripts, event handlers, frames, resource loaders, and network or
`file:` URLs. Custom CSS cannot load resources. These controls do not make
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
