# LibreMark PDF user guide

LibreMark PDF converts one or more Markdown files into styled A4 PDFs on your
computer. It provides a desktop interface and a non-interactive command line.

> **Pre-release notice:** there is no officially validated download yet. The
> current application must be run from source or built locally.

## Desktop workflow

1. Open LibreMark PDF.
2. Drop `.md` or `.markdown` files onto the window, or select **Browse files**.
3. Optional: select **Change** to use a custom CSS file.
4. Optional: expand **Header and footer (advanced)** and edit the six positions.
5. Select **Refresh preview** to render the first page.
6. Optional: select an output folder. Otherwise, each PDF is written beside its
   Markdown source.
7. Select **Generate PDF**.

The status area reports the number of successful and failed conversions. When
an item fails, the error dialog identifies the source and the underlying error.
Other files in the same batch continue to run.

## Header and footer tokens

The default center footer is `Page {page} / {total}`. Empty fields display
nothing.

| Token | Value |
| --- | --- |
| `{title}` or `{titre}` | First level-one (`#`) heading |
| `{date}` | Local render date in `YYYY-MM-DD` format |
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
```

The CLI never prompts. Exit `0` means every requested conversion succeeded.
With `--json`, stdout contains one result object for a single file or a
`{"results": [...]}` object for a batch. Each result contains `input`, `output`,
`status`, and `error`.

Run the complete reference with:

```bash
python -m libremark_pdf convert --help
```

## Language preference

Select **EN** or **FR** in the desktop window. The choice is stored locally in
`~/.libremark-pdf/config.json`. Failure to save this preference does not block
conversion.

## Files and safety

- Use UTF-8 Markdown.
- Custom CSS applies to the complete document; use CSS from a trusted source.
- The current prototype may replace an existing PDF with the selected output
  name. Keep a backup until overwrite protection is implemented.
- The safe-rendering work is not complete. Treat raw HTML, linked resources,
  and Markdown from third parties as trusted input for now.
- Building downloads Python packages and Chromium. Normal conversion is
  designed to use local resources, but strict network blocking is not yet
  verified in this prototype.

## Troubleshooting

- **A dropped file is ignored:** confirm its extension is `.md` or `.markdown`.
- **Preview fails:** verify that Chromium and `pypdfium2` are installed, then
  read the complete error shown in the status area.
- **CSS is not found:** select an existing `.css` file or restore the bundled
  default.
- **The application closes on Windows:** run `build.bat --console`, then start
  `dist\LibreMarkPDF.exe` from that console to capture the traceback.
- **A table wraps unexpectedly:** the default stylesheet uses a fixed table
  layout; long content may wrap or increase pagination.

For a bug report, retain the exact command, exit code, error text, operating
system, Python version, and whether the issue occurs from source or a built
artifact. Do not include private document contents unless necessary.
