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
   The header trash action removes all files directly. Add and remove actions
   are unavailable during conversion, with the reason shown in the file panel.
   In the large two-column layout, drag the separator between the left panel
   and preview from its 360 px minimum up to the available limit that preserves
   a usable preview; this width is retained only for the current session. Long parent paths are
   elided in the middle while their complete value remains available from the
   tooltip and **Copy path** action.
   At window widths of 759 px and below, use the **Files**, **Preview**,
   **Settings**, and **Results** tabs. Exactly one panel is visible, the active
   tab is remembered for the current session, and resizing does not clear the
   files, active preview page, zoom, settings, conversion, or results. The
   generate/progress area remains fixed at the bottom.
3. The four **Settings** rows always summarize the active PDF style,
   destination, headers and footers, and advanced options. Long values remain
   on one line and their complete value is available in a tooltip. Select the
   **PDF style** row to open its dedicated editor. Select a validated local
   theme, or select **Custom CSS** and **Choose CSS**. These choices are
   mutually exclusive, but choosing CSS does not forget the selected theme.
   Draft changes refresh the preview after 450 ms; **Save** applies them to the
   session, while **Cancel**, Escape, close, or compact **Back** restores the
   previous style and preview. Select the **Destination** row to open its
   dedicated editor. Choose either **Same folder as each source file** or
   **Single folder**, then use **Browse** to select a path. The complete custom
   path remains selectable and copyable; Unicode characters and spaces are
   preserved. Destination drafts never refresh or replace the preview.
   **Save** applies the destination to the session; **Cancel**, Escape, close,
   or compact **Back** restores it exactly. Select **Headers and footers** to
   edit the explicitly labelled Left, Center, and Right positions. An empty
   field displays nothing. Select `{titre}`, `{title}`, `{date}`, `{page}`, or
   `{total}` to insert that variable at the active field’s cursor. Draft field
   changes refresh the preview after 450 ms. **Restore defaults** asks for
   confirmation only when custom values exist, changes only these six fields,
   and restores `Page {page} / {total}` in the center footer. Save and Cancel
   follow the same session and preview restoration rules as PDF style. In
   compact mode each dedicated editor fills the Settings tab and keeps Save
   visible. The header/footer fields retain their three-column layout; an
   internal vertical scrollbar appears only when the remaining height cannot
   show the variables and reset action. Select **Advanced options**, or the
   **Edit** action beside the Settings heading, to open its dedicated editor.
   Leave the render date empty for the automatic current date, or enter a valid
   `YYYY-MM-DD` value. Invalid dates are reported inline. Enabling trusted
   static HTML asks for confirmation on its first activation in the application
   session; refusing leaves the switch off. Scripts, remote resources, and
   active content remain blocked. Advanced drafts refresh the preview after
   450 ms, and Save or Cancel follows the same exact session and preview rules.
4. Optional: edit **Headers and footers** as described above.
5. The active file's preview is refreshed after a short delay when a
   preview-compatible setting changes. The preview keeps the previous image
   visible while updating and identifies empty, updating, and unavailable
   states explicitly. The first file added to an empty list opens in
   **Fit page** mode. Selecting a different preview file, including the file
   automatically selected after removing the active one, returns to page 1 in
   **Fit page** mode. Adding or removing another file without changing the
   active file preserves the current view. Select the ↻ button, or press
   `Ctrl+R`, to refresh
   immediately and reset the view to **Fit page**. Use
   **‹ Page n of total ›** to rasterize any page from the same temporary preview
   PDF without changing the final PDF. A new document version returns to page
   1; zoom keeps the current page. With the preview focused, Left and Right
   move between pages. Use
   **− 100% +**, `Ctrl+-`, `Ctrl++`, or `Ctrl+0` to set zoom from 10% through
   200%. **Fit page** uses the available width and height, while **Fit width**
   uses the available width. Both actions resize the existing preview image
   without rendering the document again; resizing the window recalculates an
   active fit mode, and a manual zoom exits it. In compact windows, both Fit
   actions are in the preview overflow menu. With the preview focused, the
   wheel scrolls, `Shift+wheel` scrolls horizontally, `Ctrl+wheel` zooms around
   the pointer, and middle-button drag pans the page. Scrollbars appear only
   when needed. A preview error can be retried, copied, or opened in the local
   **Report a problem** workflow and does not prevent a valid PDF generation
   attempt.
6. Optional: edit **Destination** and select **Single folder**. Otherwise, each
   PDF is written beside its Markdown source.
   **Advanced options** contains the render date and trusted static HTML as
   described above.
7. Select **Generate PDF** for one file, or **Generate n PDFs** for a
   batch. The label follows the file count without abbreviated plural forms.

The application presents existing PDFs and output collisions directly in the
fixed action bar before conversion, without a modal dialog. **Back** appears
before the decision title, like the settings pages; Escape performs the same
safe return. The title and counts share one line. Details list each source,
destination, short issue, and replacement decision in a compact table. Check
**Replace?** for each existing PDF that may be replaced after a successful
render; unchecked PDFs receive the neutral **Kept** state. The checkbox in the
column heading changes all eligible rows and shows an intermediate state for a
mixed selection. Collision rows show **Blocked** instead of a checkbox and can
be reported while independent files continue. A separate summary states how
many PDFs will be replaced or kept; the **Continue** button remains fixed.
Hover a cell for its full value. The mouse wheel scrolls this table only while
the table has focus; otherwise it continues to scroll the main interface.

During conversion, the bar identifies the batch destination, active item and
filename. The numeric percentage remains based only on fully completed files,
while an animated segment and the exact **Preparing document**, **Rendering with
Chromium**, **Finalizing PDF**, or **Publishing safely** phase show that the
active file is advancing. Chromium prints a complete PDF in one blocking call,
so page-level percentages are not claimed. The first file may take longer while
Chromium starts and local resources and fonts are prepared. **Applied options
ⓘ** is an informational link, not a setting control: hover or focus it for a
tooltip, or activate it to keep a small non-modal summary open. It gives the
immutable style, full destination, six header/footer values, date mode, and
trusted-HTML setting used by the worker from the start of conversion. File
selection, the existing preview
(pages, zoom, fit, scrolling, and panning), settings summaries, and produced
results remain consultable; file and setting mutations and preview re-rendering
remain locked until the terminal event.

Select **Stop after this file** to let the current file finish and cancel files
not started. Select **Cancel now** to interrupt at the next safe point and
cancel the whole remainder. A blocking Chromium call may take a few seconds to
return; no partial PDF is published and any previous destination PDF is kept.
Closing the window asks whether to **Continue conversion** (the safe default,
also used by Escape) or **Cancel conversion and close**; the active file may
finish before the remaining files are cancelled. The final list keeps one row
per input in source order, including successful, failed, kept, and cancelled
items. An existing PDF that the user explicitly chose not to replace is
**Kept**, not failed; an unexpected overwrite refusal remains a failure.
On normal and large windows, **Results** is a bounded full-width lower panel
below the Files/Settings and Preview workspace. Expand or collapse it, or drag
its horizontal separator to adjust its height; the main workspace and fixed
action bar remain available. Settings keeps a fixed height while Files uses
the remaining height, down to its minimum. The vertical separator can grow the
left workspace to the available limit while retaining a usable Preview. On compact
windows, the same ordered results use condensed vertical cards in the
**Results** tab without horizontal scrolling. A terminal
batch containing an error selects Results automatically; conversion never
changes tabs while it is still running, and an all-success batch keeps the
current tab.

The panel header places the batch summary beside **Results**. Its trash action
clears results directly, consistently with the Files panel, and the chevron
collapses or expands the panel. Row actions use standard icons with localized
tooltips and accessible names. Successful items offer **Open PDF** and
**Open folder**. Failed items offer **Copy details**, the existing prefilled
**Report a problem** workflow, and a direct information button for expandable details.
Cancelled items never offer an open action; their details, when available, are
also reached through the same information button. The Output cell shows an
ellided failure message when no PDF was produced. Expanded details avoid
repeating that message and show the stable error code followed by any
additional monospace technical details; they stay expanded during later UI updates or a
language change. **Clear results** is available only while no conversion is
active; it removes no PDF and returns the application to its ready state when
source files remain.

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

In compact windows, open the image-only application menu beside the product
name. It contains **User manual**, **Keyboard shortcuts**, the checked
**Language** submenu, **Report a problem**, **About LibreMark PDF**, and the
current version. The logo, product name, menu, and native window controls stay
visible at the minimum 560 px width.

Press `F1` to display the available keyboard shortcuts.
**Help → User manual** opens this local guide in the system application.

**About LibreMark PDF** shows the application, render profile, Playwright,
Chromium, Python, system, and architecture identities. **Copy technical
information** copies only these
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
- Default conversion renders raw HTML literally. **Advanced options** in
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
