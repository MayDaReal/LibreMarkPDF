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
3. `LibreMarkPDF.exe` or `LibreMarkPDF` from a locally built artifact.

If none exists, explain that LibreMark PDF must be installed or built. Do not
claim that `build.sh` or `build.bat` installs a command on `PATH`.

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
```

Tokens are `{title}`/`{titre}`, `{date}`, `{page}`, and `{total}`.

Exit `0` means every requested conversion succeeded. A single input returns one
object; a batch returns `{"results": [...]}`. Each result contains `input`,
`output`, `status`, and `error`. Confirm every status is `"ok"` and every
reported output exists before reporting success.

For generated Markdown text, write a UTF-8 temporary `.md` file, choose an
explicit PDF output, then remove only the temporary source created for the task.

## Current safety boundary

The prototype does not yet enforce the target network, raw-HTML, resource, or
overwrite policies. Convert only trusted Markdown and CSS, avoid remote
resources, and do not overwrite a valuable existing PDF.

```bash
python -m libremark_pdf convert --help
```
