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
   changing the batch order. The active row is identified by an **Active
   preview** badge; every other row remains part of the batch. Use the row
   **Actions** menu to show the source folder, copy the path, or remove the
   file. With a row focused, use Up/Down to move, Enter or Space to activate
   its preview, Delete to remove it, and Menu or Shift+F10 to open its actions.
   Add and remove actions are unavailable during conversion, with the reason
   shown in the file panel. In the large two-column layout, drag the separator
   between the left panel and preview to set the left panel from 360 to 440 px;
   this width is retained only for the current session. Long parent paths are
   elided in the middle while their complete value remains available from the
   tooltip and **Copy path** action.
3. The four **Settings** rows always summarize the active PDF style,
   destination, headers and footers, and advanced options. Long values remain
   on one line and their complete value is available in a tooltip. Select the
   single **Edit** action beside the Settings heading to open one dialog for
   all four families; **Apply** keeps all changes and **Cancel** or Escape
   restores the settings present when it opened. In **PDF style**,
   select a validated local theme, or select **Custom CSS** and **Choose CSS**.
   These choices are mutually exclusive;
   **Use the selected theme** removes the custom CSS without forgetting the theme
   selected for this session.
4. Optional: edit **Headers and footers** and change the explicitly labelled
   Left, Center, and Right positions. **Restore defaults** changes only
   these six fields and restores the default center footer.
5. The active file's preview is refreshed after a short delay when a
   preview-compatible setting changes. The preview keeps the previous image
   visible while updating and identifies empty, updating, and unavailable
   states explicitly. Select the ↻ button to refresh immediately. Use
   **‹ Page n of total ›** to rasterize any page from the same temporary preview
   PDF without changing the final PDF. A new document version returns to page
   1; zoom keeps the current page. With the preview focused, Left and Right
   move between pages. Use
   **− 100% +**, `Ctrl+-`, `Ctrl++`, or `Ctrl+0` to set zoom from 50% through
   200%. With the preview focused, the wheel scrolls, `Ctrl+wheel` zooms around
   the pointer, and middle-button drag pans the page. Scrollbars appear only
   when needed. A preview error can be retried or copied and does not prevent a
   valid PDF generation attempt.
6. Optional: edit **Destination** and select an output folder. Otherwise,
   each PDF is written beside its Markdown source.
   **Advanced options** contains the render date and trusted static HTML.
   Enabling trusted HTML requires confirmation the first time in each
   application session.
7. Select **Generate PDF** for one file, or **Generate n PDFs** for a
   batch. The label follows the file count without abbreviated plural forms.

The application presents output collisions and existing PDFs before conversion.
The choices use explicit labels: a collision can be skipped while independent
files continue, and an existing PDF can be replaced only after a successful
render or kept and reported as a failure. During a batch the persistent action
bar identifies progress and allows safe cancellation after the current file.
Closing the window asks whether to **Continue conversion** (the safe default,
also used by Escape) or **Cancel conversion and close**; the active file may
finish before the remaining files are cancelled. The final list keeps one row
per input in source order, including successful, failed, and cancelled items.
Error codes can be expanded and copied. **Open PDF** and **Open folder** actions
are shown only for successful outputs.

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

Use the language menu in the fixed desktop header and select **English** or
**Français**. The checked choice is stored locally in
`~/.libremark-pdf/config.json`. Failure to save this preference does not block
conversion. Changing language immediately retranslates visible labels and
accessible names without clearing the selected files, active preview, or PDF
settings.

Press `F1` to display the available keyboard shortcuts.
**Help → User manual** opens this local guide in the system application.

The compact version beside the LibreMark PDF name opens **About LibreMark
PDF**. The same dialog is available from **Help → About LibreMark PDF**. It
shows the application, render profile, Playwright, Chromium, Python, system,
and architecture identities. **Copy technical information** copies only these
values: it does not include selected files, document contents, private paths,
environment variables, or logs, and it does not send anything over the
network.

**Help → Report a problem** opens an entirely local, editable report. Describe
what happened; reproduction steps and the expected result are optional. If the
dialog was opened from a failed file, its error code is prefilled. **Include
anonymized technical diagnostics** is off by default. When enabled, it adds
application and renderer identities, operating-system details, resource
presence, the selected theme identifier, file count, drag-and-drop state, and
an anonymized error. It never adds selected filenames or paths, Markdown, PDF,
HTML or CSS contents, account or machine names, environment variables,
clipboard contents, or global logs. Review and edit the complete report before
using **Copy report** or **Save report…**. Nothing is uploaded or sent.

No official support page is configured in this build, so the dialog provides
offline instructions instead of inventing a link. Save or copy the reviewed
report and share it only through an official channel you trust. Review the
report yourself before sharing it; automated path removal is a safeguard, not
a substitute for that review.

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
