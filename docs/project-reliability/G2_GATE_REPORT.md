# Gate G2 report

Status: **active — no decision**  
Baseline commit: `603acb34ca8ecc39e3d2c2a560fc367049b41ca7`

## Initial custody

- `git status --short --branch`: `## main`
- `git rev-parse HEAD`: `603acb34ca8ecc39e3d2c2a560fc367049b41ca7`
- The local immutable `BASELINE_AUDIT.md` was read and was not modified.
- `archive/g1/` was read as historical evidence and was not modified.

Subsequent sections record exact commands, exit codes, artifacts, and task
dispositions as implementation evidence is obtained.

## Phase 1 characterization

Environment: Ubuntu 24.04.4-compatible container, Linux
`6.17.0-35-generic`, x86_64, system and `venv-linux` CPython `3.12.3`.

| Command | Exit | Result |
| --- | ---: | --- |
| `venv-linux/bin/python -m unittest discover -s tests -v` | 1 | 54 tests ran; three renderer-dependent tests failed because `resource_path("browsers")` selected a repository payload without `chrome-headless-shell`. |
| `PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v` | 1 | 54 tests ran; three renderer-dependent tests failed because locked Chromium revision 1223 terminated at `sandbox_host_linux.cc:41` with `Operation not permitted`. |

The failures are retained as environment/product limitations. They do not
justify skipping or weakening renderer, network, output-integrity, or visual
tests. Browser-free tests passed in both runs.

| Command | Exit | Result |
| --- | ---: | --- |
| `/bin/bash -lc 'PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright" venv-linux/bin/python -m unittest discover -s tests -v'` (outside the container sandbox) | 0 | all 54 baseline tests passed with locked cached Chromium revision 1223. |

This establishes that the preceding cached-browser failure is a sandbox
restriction, not a baseline product failure.

The approved static font evidence is locally available outside the repository
at `/tmp/libremark-g1-font-static-5264143/fonts/`; its presence and hashes must
be independently verified before any production resource copy. No fonts,
browsers, PDFs, caches, or generated output were added to Git.
