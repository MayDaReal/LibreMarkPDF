# Pre-GUI cleanup execution plan

## P00 — Remove obsolete GUI compatibility facades

Status: **completed**

### Scope

Remove the unshipped compatibility-only modules `gui_inputs.py`,
`gui_layout.py`, `gui_preview.py`, and `gui_conversion.py`. Their canonical Tk
implementations already live in `libremark_pdf/desktop/tk/`. Keep
`libremark_pdf/gui.py` as the stable GUI launch facade.

### Preserved observable behavior

- `libremark_pdf.gui` imports and launches the same `LibreMarkPdfApp`;
- optional `tkinterdnd2` import and fallback launch behavior remain unchanged;
- widgets, geometry, colors, fonts, spacing, EN/FR text, dialogs, bindings,
  preview, conversion, cancellation, and close behavior remain unchanged;
- no rendering input, render profile, resource, hash, or default theme changes.

### Required evidence

- no tracked production, test, packaging, or active architecture document
  imports an obsolete facade;
- focused GUI, i18n, desktop-service, and packaging tests pass;
- the complete test suite passes with the bundled Chromium path;
- modified Python files compile with the configured Python 3.9 interpreter;
- CLI help/version and GUI startup both with and without `tkinterdnd2` pass;
- `git diff --check` passes and no generated resource, golden, PDF, cache, or
  owner-owned G2 file is staged.

### Results

- `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python
  -m unittest tests.test_gui tests.test_i18n tests.test_desktop_services
  tests.test_packaging -v` — exit 0; 51 tests passed.
- `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python
  -m unittest discover -s tests -v` — exit 0; 218 tests passed.
- `PYENV_VERSION=3.9.23 python3.9 -m py_compile tests/test_gui.py` — exit 0.
- `venv-linux/bin/python -m libremark_pdf convert --help` — exit 0.
- `venv-linux/bin/python -m libremark_pdf --version` — exit 0:
  `LibreMark PDF 1.0.0; render-profile default@1; Playwright 1.60.0; Chromium
  148.0.7778.96 (revision 1223)`.
- Xvfb GUI smoke tests — exit 0 with `tkinterdnd2` available (`gui-dnd-ok`) and
  blocked (`gui-no-dnd-ok`).
- `git diff --check` — exit 0. No renderer, profile, core, theme, font, CSS,
  icon, asset, golden, cache, or PDF file changed.

### Risks and deviations

Removing these unshipped internal import paths is intentionally incompatible
only for direct imports of the four compatibility modules. There is no public
GUI API change: `libremark_pdf.gui` remains the launch facade. No UI/UX work is
in scope. Historical R00–R12 and G3 report references remain unchanged as
historical evidence; active architecture records now name `desktop/tk/`.
