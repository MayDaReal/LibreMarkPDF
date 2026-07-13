# LibreMark PDF

LibreMark PDF converts UTF-8 Markdown files into styled A4 PDFs on the local
computer. One shared engine serves a desktop GUI, a non-interactive CLI, and the
agent contract in [`SKILL.md`](SKILL.md).

> **Project status:** pre-release prototype. No official standalone download is
> published yet. Build scripts are provided for development and validation;
> they are not evidence of a supported release.

## Features

- batch conversion from `.md` and `.markdown` files;
- first-page preview in the desktop app;
- built-in style or a user-supplied CSS file;
- six header/footer positions with page, title, and date tokens;
- English and French desktop interface;
- JSON output and meaningful exit status for automation.

User guides: [English](docs/MANUAL_EN.md) · [Français](docs/MANUEL_FR.md)

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
```

Run `python -m libremark_pdf convert --help` for every option. A successful
command exits `0`; validation or conversion failure exits nonzero. JSON is
written to stdout, while human-readable errors are written to stderr.

## Headers and footers

The top and bottom of each page each have left, center, and right fields. The
default footer is `Page {page} / {total}`.

| Token | Value |
| --- | --- |
| `{titre}` or `{title}` | First level-one heading |
| `{date}` | Local render date in `YYYY-MM-DD` format |
| `{page}` | Current page number |
| `{total}` | Total page count |

## Build a local artifact

Builds download dependencies and Chromium, so the build step requires network
access. Conversion is intended to run locally with the bundled resources.

### Windows

1. Install Python 3.9+.
2. Run `build.bat` from a local disk.
3. Test `dist\LibreMarkPDF.exe` with
   [`docs/WINDOWS_BUILD_VALIDATION.md`](docs/WINDOWS_BUILD_VALIDATION.md).

Use `build.bat --console` to produce the same application with startup errors
visible. Run plain `build.bat` again for the windowed build.

### Linux

Install Tk for your distribution, then run:

```bash
chmod +x build.sh
./build.sh
```

The resulting `dist/LibreMarkPDF` is native to the build environment. Linux is
not advertised as portable until its native compatibility gate passes.

## Architecture

```text
GUI ─┐
CLI ─┼─> libremark_pdf/core.py ─> Markdown/HTML ─> Chromium ─> PDF
Skill┘                                           └> PDFium ─> preview PNG
```

`libremark_pdf/core.py` is the only reusable conversion engine. Runtime files
are in `style.css`, `icons/`, `assets/`, and the generated `browsers/` tree.
See [`AGENTS.md`](AGENTS.md) for contribution rules and
[`docs/project-reliability/BACKLOG.md`](docs/project-reliability/BACKLOG.md) for
the gated reliability program.

## Current security limitations

Until the safe-rendering backlog is complete, treat Markdown, raw HTML, linked
resources, and custom CSS as trusted input. Network denial, local-resource
sandboxing, script blocking, atomic output, and collision protection are target
requirements but are not yet fully implemented.

## License

LibreMark PDF source code is released under the [MIT License](LICENSE).
Dependency and bundled-resource licenses must be verified and included before
an official binary is published.
