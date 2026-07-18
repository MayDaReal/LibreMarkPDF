# LibreMark PDF user guide

LibreMark PDF converts one or more Markdown files into styled A4 PDFs on your
computer. It provides a desktop interface and a non-interactive command line.

> **Pre-release notice:** there is no officially validated download yet. The
> current application must be run from source or built locally.

## Desktop workflow

1. Open LibreMark PDF.
2. Drop `.md` or `.markdown` files onto the window, or select **Browse files**.
3. Optional: select a validated local theme, or select **Change** to use a
   custom CSS file. These choices are mutually exclusive.
4. Optional: expand **Header and footer (advanced)** and edit the six positions.
5. Select **Refresh preview** to render the first page. Scroll it or use the
   zoom controls from 50% through 200%.
6. Optional: select an output folder. Otherwise, each PDF is written beside its
   Markdown source.
7. Select **Generate PDF**.

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
artifact, replace that prefix with the executable path.

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

## Files and safety

- Use UTF-8 Markdown.
- Custom CSS applies to the complete document but cannot use `@import` or
  `url(...)` resources.
- Existing output is refused unless the CLI caller passes `--overwrite`; a
  replacement is published only after successful rendering.
- Default conversion renders raw HTML literally. The CLI-only `--trusted-html`
  compatibility option permits a narrow static subset, never scripts, event
  handlers, frames, resource loaders, or network/`file:` URLs.
- Markdown images must be approved local PNG, JPEG, GIF, or static SVG files;
  they are validated and embedded before rendering.
- Theme packages must be local, hashed, licensed, compatible with
  `default@1`, and free of scripts, remote URLs, traversal, and active assets.
- Use `--date YYYY-MM-DD` when a reproducible `{date}` value is needed;
  otherwise it uses the current UTC date.

## Troubleshooting

- **A dropped file is ignored:** confirm its extension is `.md` or `.markdown`.
- **Preview fails:** verify that Chromium and `pypdfium2` are installed, then
  read the complete error shown in the status area.
- **CSS is not found:** select an existing `.css` file or restore the bundled
  default.
- **The application closes on Windows:** start
  `dist\LibreMarkPDF\LibreMarkPDF-debug.exe` to retain startup diagnostics.
- **A table wraps unexpectedly:** the default stylesheet uses a fixed table
  layout; long content may wrap or increase pagination.

For a bug report, retain the exact command, exit code, error text, operating
system, Python version, and whether the issue occurs from source or a built
artifact. Do not include private document contents unless necessary.
