# Validation

LibreMark PDF separates fast checks from artifact validation. Normal tests
never modify the canonical corpus or its expected results.

## Commands

After running the native bootstrap with standard CPython 3.14:

```text
make test-pure     # focused source and CLI contract checks
make test          # complete suite with the locked Chromium payload
make test-ui       # Tk orchestration and stable UI actions
make test-visual   # canonical corpus contract
```

Native validation through `make validate-windows` and `make validate-linux`
produces a candidate, diagnostics, and a checklist under
`dist/<version>/<platform>/`.

Run native candidate validation from a clean checkout so every artifact and
evidence manifest identifies one exact commit. The validators do not install or
download dependencies or browsers. Use their offline option only after physical
network interfaces have been disconnected; automated startup evidence does not
replace the generated manual GUI checklist.

Each native build first stages `MANUAL_EN.pdf` and `MANUEL_FR.pdf` outside
tracked source by converting both authoritative Markdown guides through
LibreMark PDF's CLI with the root `style.css`. The build fails if conversion or
either output fails. Artifact review opens both localized PDFs from the exact
GUI and checks styling, headings, code, links, Unicode, pagination, selectable
text, the default footer, clipping, and absence of remote resources.

On Windows x64, the direct validation command requires no arguments after
bootstrapping the native environment.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-windows-artifact.ps1
```

It defaults to `.venv-windows-py314`, `browser-win`, and
`dist/<version>/windows-x64`. Use `-Python` and `-EvidenceRoot` to override
the interpreter and evidence paths. Set `LIBREMARK_PDF_BROWSER_SOURCE` for the
direct bootstrap, build, and validation scripts to use a separate staging
directory, for example when retaining an earlier browser payload.

The bootstrap scripts are interactive when a terminal is available. They ask
for confirmation before installing Python or GNU Make. Linux searches for
standard CPython 3.14 and only offers Ubuntu packages when both the
interpreter and venv packages are available. Windows options
`-InstallPython`, `-InstallMake`, and `-NonInteractive`, and their Linux
equivalents `--install-python`, `--install-make`, and `--non-interactive`,
support automated execution. Offline mode does not install or download
anything.

## Canonical corpus

`tests/fixtures/canonical/manifest.json` and
`tests/goldens/canonical/expected.json` define the current canonical corpus.
They cover Markdown, pagination, resources, Unicode, themes, collisions, and
paths. Active tools are `tools/visual_regression.py`,
`tools/artifact_visual_regression.py`, `tools/validate-windows-artifact.ps1`,
and `tools/validate-linux-artifact.sh`.

Text extraction and PDFium character geometry are exact within each reviewed
native platform. `tools/update_visual_goldens.py --structure-platform` merges a
complete reviewed platform evidence set without replacing another platform's
hashes or the approved raster baseline. Cross-platform review remains separate
and must report semantic differences rather than normalizing them away.

Normal comparison is read-only. Updating goldens requires the dedicated update
tool, a tracked issue, a justification, human review, and before/after
comparisons retained with the release.

## User interface

UI tests target stable business actions such as `files.add`,
`advanced.toggle`, `preview.refresh`, and `convert.start`. They do not depend on
coordinates, colors, or EN/FR labels. Native checklists retain human checks for
contrast, focus, DPI, and desktop integration.

The internal modern-component gallery is independent of conversion services:

```powershell
python -m tools.ui_component_gallery --lang fr
python -m tools.ui_component_gallery --lang en
```

Its local Bootstrap Icons subset is owned by
`libremark_pdf.desktop.ctk.assets`. When the approved upstream version, icon
list, sizes, or semantic colors change, replace the retained SVG sources and
run:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path browser-win).Path
python -m tools.generate_ui_icons
python -m unittest tests.test_ctk_foundations -v
```

Review `assets/ui-icons/manifest.json`, the generated PNG diff, upstream
licence, source hashes, 100/125/150% DPI rendering, and offline packaging.
Delete the generator only if the runtime no longer consumes rasterized local
icons.
