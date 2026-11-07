# Validation

LibreMark PDF separates fast checks from artifact validation. Normal tests
never modify the canonical corpus or its expected results.

## Commands

After running `bootstrap-windows.ps1` or `bootstrap-linux.sh`:

```text
make test-pure     # unit checks that do not require a browser
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

On Windows, the direct command requires no arguments:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-windows-artifact.ps1
```

It defaults to `.venv-windows-py39`, `browser-win`, and
`dist/<version>/windows-x64`. Use `-Python` and `-EvidenceRoot` to override
those values.

The bootstrap scripts are interactive when a terminal is available. They ask
for confirmation before installing Python 3.9 or GNU Make. Windows options
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
