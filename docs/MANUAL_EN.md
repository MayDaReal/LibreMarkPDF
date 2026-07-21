# LibreMark PDF user guide

LibreMark PDF converts one or more Markdown files into styled A4 PDFs on your
computer. It provides a desktop interface and a non-interactive command line.

> **Pre-release notice:** there is no officially validated download yet. The
> current application must be run from source or built locally.

For a source checkout, run `bootstrap-windows.ps1` on Windows or
`bootstrap-linux.sh` on Linux. They prepare the locked Python 3.9 environment
and the required local Chromium payload. A shared checkout keeps the native
payloads separate in `browser-win/` and `browser-linux/`. On Windows,
`bootstrap-windows.ps1 -InstallPython -InstallMake` can explicitly install
missing recommended tools. On Linux, use
`bootstrap-linux.sh --install-python --install-make`. Without explicit options,
an interactive terminal asks before installing a missing tool.
On Ubuntu 24.04 and other distributions without a native CPython 3.9 package,
install CPython 3.9 with pyenv first; the Linux bootstrap detects an installed
`3.9.x` pyenv version automatically.

## Desktop workflow

1. Open LibreMark PDF.
2. Select **Add files**, or drop `.md` or `.markdown` files when optional
   drag-and-drop support is available. Without it, the empty area says
   **Select Markdown files** and opens the native selector with a click, Enter,
   or Space.
   Valid files keep their addition order. A mixed selection still adds valid
   files and reports exact added, duplicate, and unsupported counts in the
   status area. Select any file row to make it the active preview file without
   changing the batch order.
3. Optional: expand **PDF style** and select a validated local theme, or select
   **Custom CSS** and **Choose CSS**. These choices are mutually exclusive;
   **Use the selected theme** removes the custom CSS without forgetting the theme
   selected for this session.
4. Optional: expand **Headers and footers** and edit the explicitly labelled
   Left, Center, and Right positions. **Restore defaults** changes only
   these six fields and restores the default center footer.
5. The active file's first page is refreshed after a short delay when a
   preview-compatible setting changes. The preview keeps the previous image
   visible while updating and identifies empty, updating, and unavailable
   states explicitly. Select the ↻ button to refresh immediately. Use
   **− 100% +**, `Ctrl+-`, `Ctrl++`, or `Ctrl+0` to set zoom from 50% through
   200%. With the preview focused, the wheel scrolls, `Ctrl+wheel` zooms around
   the pointer, and middle-button drag pans the page. Scrollbars appear only
   when needed. A preview error can be retried or copied and does not prevent a
   valid PDF generation attempt.
6. Optional: expand **Destination** and select an output folder. Otherwise,
   each PDF is written beside its Markdown source.
   **Other advanced options** contains the render date and trusted static HTML.
   Enabling trusted HTML requires confirmation the first time in each
   application session.
7. Select **⚙ Generate PDF**.

The application presents output collisions and existing PDFs before conversion.
During a batch it displays progress and allows safe cancellation after the
current file. When an item fails, the result identifies the source and error;
other independent files continue. **Open PDF** and **Open folder** actions are
shown only for successful outputs.

## Header and footer tokens

The default center footer is `Page {page} / {total}`. Empty fields display
nothing.

| Token | Value |
| --- | --- |
| `{title}` or `{titre}` | First level-one (`#`) heading |
| `{date}` | UTC render date in `YYYY-MM-DD` format (or `--date`) |
| `{page}` | Current page number |
| `{total}` | Total page count |

Literal text is allowed around tokens, for example:

```text
{title} — Page {page} / {total}
```

## Command line

When running from source, use `python -m libremark_pdf`. In a built console
artifact, replace that prefix with the executable path
(`LibreMarkPDF-cli.exe` on Windows or `LibreMarkPDF-cli` inside the Linux
candidate directory).

```bash
# Create report.pdf beside report.md
python -m libremark_pdf convert report.md

# Choose one output file
python -m libremark_pdf convert report.md -o exported/report.pdf

# Convert several files to one directory
python -m libremark_pdf convert a.md b.md --out-dir exported --json

# Apply custom CSS and page numbering
python -m libremark_pdf convert report.md --css print.css \
  --footer-center "Page {page} / {total}"

# Select a local theme and fixed date
python -m libremark_pdf convert report.md --theme default@1 \
  --date 2026-07-14 --json

# Read-only identity and resource diagnostics
python -m libremark_pdf --version
python -m libremark_pdf doctor --json
```

The CLI never prompts. Exit `0` means every requested conversion succeeded.
With `--json`, stdout contains exactly one JSON result object for a single file or a
`{"results": [...]}` object for a batch. Each result contains `input`, `output`,
`status`, `error`, and `error_code`; valid conversion requests also report the
render date, profile, fingerprint, theme, Playwright, and Chromium identities.
Human errors use stderr. The schema is
[`CLI_JSON_SCHEMA.json`](CLI_JSON_SCHEMA.json).

Run the complete reference with:

```bash
python -m libremark_pdf convert --help
```

Manage local themes with `theme list`, `theme show`, `theme install`, and
`theme remove`. Installation and replacement are validated and atomic.
`default@1` is the immutable compatible default. The `--render-date` spelling
is retained as a legacy alias of `--date`.

## Language preference

Select **EN** or **FR** in the desktop window. The choice is stored locally in
`~/.libremark-pdf/config.json`. Failure to save this preference does not block
conversion.

Press `F1` to display the available keyboard shortcuts.

## Files and safety

- Use UTF-8 Markdown.
- Custom CSS applies to the complete document but cannot use `@import` or
  `url(...)` resources.
- Existing output is refused unless the CLI caller passes `--overwrite`; a
  replacement is published only after successful rendering.
- Default conversion renders raw HTML literally. **Other advanced options** in
  the desktop interface and the CLI `--trusted-html` compatibility option
  permit the same narrow static subset, never scripts, event handlers, frames,
  resource loaders, or network/`file:` URLs. The desktop asks for confirmation
  on first use in each session.
- Markdown images must be approved local PNG, JPEG, GIF, or static SVG files;
  they are validated and embedded before rendering.
- Theme packages must be local, hashed, licensed, compatible with
  `default@1`, and free of scripts, remote URLs, traversal, and active assets.
- Use `--date YYYY-MM-DD` when a reproducible `{date}` value is needed;
  otherwise it uses the current UTC date.

## Troubleshooting

- **A selected or dropped item is ignored:** read the non-modal counts in the
  status area. Only `.md` and `.markdown` files are supported, and files already
  present in the list are treated as duplicates.
- **Preview fails:** verify that Chromium and `pypdfium2` are installed, then
  read the complete error shown in the status area.
- **CSS is not found:** select an existing `.css` file or restore the bundled
  default.
- **The application closes on Windows:** start
  `dist\LibreMarkPDF\LibreMarkPDF-debug.exe` to retain startup diagnostics.
- **The Linux candidate does not start:** keep its complete `_internal`
  directory, start `LibreMarkPDF-debug` from a terminal, and retain the `ldd`
  missing-library output. The tarball does not use FUSE, but it still depends
  on compatible glibc and Chromium desktop libraries.
- **A table wraps unexpectedly:** the default stylesheet uses a fixed table
  layout; long content may wrap or increase pagination.

For a bug report, retain the exact command, exit code, error text, operating
system, Python version, and whether the issue occurs from source or a built
artifact. Do not include private document contents unless necessary.
