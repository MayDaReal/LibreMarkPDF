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

Normal comparison is read-only. Updating goldens requires the dedicated update
tool, a tracked issue, a justification, human review, and before/after
comparisons retained with the release.

## User interface

UI tests target stable business actions such as `files.add`,
`advanced.toggle`, `preview.refresh`, and `convert.start`. They do not depend on
coordinates, colors, or EN/FR labels. Native checklists retain human checks for
contrast, focus, DPI, and desktop integration.
