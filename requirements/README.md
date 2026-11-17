# Dependency workflow

LibreMark PDF separates runtime, GUI/preview, build, test, and documentation
inputs in the adjacent `*.in` files. `constraints.txt` fixes development
resolution. Release environments use an OS, architecture, and Python-specific
lock with hashes.

The existing `requirements.txt` remains a convenient compatibility input for
source development. Its lower bounds are intentionally not presented as
reproducible; native candidates use the platform locks exclusively.

The initial release has two mandatory native candidate lanes on CPython 3.9:
Windows x64 uses `locks/windows-x64-py39.txt`, and Ubuntu 24.04 x86_64 uses
`locks/linux-x86_64-py39.txt`. A lock ensures archive integrity but is not by
itself a distribution support claim. Both select Playwright 1.60.0, whose wheel
manifest selects Chromium/headless shell 148.0.7778.96 at revision 1223 and
FFmpeg 1011. Changing Playwright or
its browser manifest requires a dedicated dependency PR, an updated
platform-specific lock, renderer-spike review, and golden evidence; Dependabot
must not merge it automatically.

The GUI input and both candidate locks select CustomTkinter 6.0.0 exactly.
Its runtime resources are collected by the PyInstaller specification; normal
application startup never downloads the package, themes, or assets.

## Contributor setup

From a clean checkout, use `bootstrap-windows.ps1` or `bootstrap-linux.sh`.
They create the platform environment from its hashed lock and acquire the
exact browser payload in `browser-win/` or `browser-linux/`. On Windows,
`-InstallPython` and `-InstallMake` opt in to installing missing recommended
tools; Linux accepts `--install-python` and `--install-make`. Interactive
terminals ask before installation when these options are omitted. The
equivalent manual development setup is:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -c requirements/constraints.txt -e ".[test]"
python tools/run_tests.py pure
```

On Windows, activate with `.venv-windows-py39\Scripts\Activate.ps1` and use
the same `python` commands. The command above is the pure, browser-free gate. Browser-backed
tests additionally require the exact Playwright browser payload:

```bash
PLAYWRIGHT_BROWSERS_PATH=/path/to/isolated/browsers \
  python -m playwright install --only-shell chromium
PLAYWRIGHT_BROWSERS_PATH=/path/to/isolated/browsers \
  python -m unittest discover -s tests -v
```

Installation and browser acquisition may use the network. Normal conversion
must never download dependencies or a browser. The repository's current
top-level runtime resource layout is authoritative for source and PyInstaller
execution; an ordinary wheel is not yet accepted as a standalone runtime
artifact because `resource_path()` has not been migrated or release-tested.

## Hashed Windows candidate install

On native Windows x64 with CPython 3.9:

```powershell
python -m pip install --require-hashes `
  -r requirements\locks\windows-x64-py39.txt
```

The lock was resolved for the target platform, but must still be installed and
tested on native Windows before it becomes release evidence.

The branch-aware coverage gate runs the complete suite under Xvfb and enforces
75% overall coverage. Reports retain per-module values so GUI, CLI, core, and
i18n gaps remain visible. Raising the floor requires added tests; it must never
be lowered to accept a regression.

## Hashed Linux candidate install

On native Linux x86_64 with CPython 3.9:

```bash
python -m pip install --require-hashes \
  -r requirements/locks/linux-x86_64-py39.txt
```

The wheels were resolved for a manylinux2014 x86_64 input set. This ensures
archive integrity, not runtime compatibility. The exact candidate still
requires the distribution, glibc, desktop-library, offline, GUI/CLI and
canonical checks described in `docs/VALIDATION.md` and
`docs/PLATFORM_SUPPORT.md`.
