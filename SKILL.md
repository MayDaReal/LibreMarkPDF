---
name: libremark-pdf
description: Convert UTF-8 Markdown files or generated Markdown text to styled PDF with LibreMark PDF. Use for single or batch Markdown-to-PDF requests, including custom CSS, headers, footers, and page numbers. Do not silently substitute another converter when LibreMark PDF is unavailable.
---

# LibreMark PDF

Use the non-interactive CLI and request JSON so results can be verified.

## Locate the command

Use the first command form that is actually available:

1. `libremark-pdf` when an installed console command exists;
2. `python -m libremark_pdf` from a source checkout with dependencies installed;
3. `LibreMarkPDF-cli.exe` on Windows or `LibreMarkPDF` on another platform from
   a locally built, validated artifact.

If none exists, explain that LibreMark PDF must be installed or built. The
repository build commands create local artifacts; they do not install a
command on `PATH`.

The examples below use `python -m libremark_pdf`; replace that prefix when
another verified form is selected.

## Convert and verify

```bash
# One file; creates report.pdf beside the source
python -m libremark_pdf convert report.md --json

# Explicit destination
python -m libremark_pdf convert report.md -o exported/report.pdf --json

# Batch destination
python -m libremark_pdf convert a.md b.md --out-dir exported --json

# Header, footer, and custom CSS
python -m libremark_pdf convert report.md --css print.css \
  --header-center "{title}" \
  --footer-center "Page {page} / {total}" --json

# Local theme and reproducible date
python -m libremark_pdf convert report.md --theme default@1 \
  --date 2026-07-14 --json
```

Tokens are `{title}`/`{titre}`, `{date}`, `{page}`, and `{total}`.

Exit `0` means every requested conversion succeeded. A single input returns one
object; a batch returns `{"results": [...]}`. Each result contains `input`,
`output`, `status`, `error`, and `error_code`; accepted requests also identify
the render profile, fingerprint, theme, Playwright, and Chromium. Confirm every
status is `"ok"` and every reported output exists before reporting success.
JSON stdout must contain no other text. The public result schema is
`docs/CLI_JSON_SCHEMA.json`.

For generated Markdown text, write a UTF-8 temporary `.md` file, choose an
explicit PDF output, then remove only the temporary source created for the task.

## Safety boundary

Default conversion literalizes raw HTML, validates and embeds approved local
images, blocks CSS resource loaders, and refuses existing output unless
`--overwrite` is explicit. `--trusted-html` is a narrow static compatibility
mode: active content, network access, and `file:` URLs remain blocked. Use
`--date YYYY-MM-DD` for reproducible date tokens; `--render-date` is a retained
legacy alias. A theme must already be installed locally and validated. Do not
download or install a theme as part of conversion.

```bash
python -m libremark_pdf --version
python -m libremark_pdf doctor --json
python -m libremark_pdf convert --help
```

`doctor --json` reports the Python runtime and the Playwright, Chromium and
FFmpeg identities. It checks for the selected headless shell and required local
resources without launching Chromium or downloading anything. Use the same
renderer when resolving a missing shell.
