# Dependency workflow

LibreMark PDF separates runtime, GUI/preview, build, test, and documentation
inputs in the adjacent `*.in` files. `constraints.txt` fixes development
resolution. Release environments use an OS, architecture, and Python-specific
lock with hashes.

The existing `requirements.txt` remains the compatibility input used by the
unmodified native build scripts. Its historical lower bounds are intentionally
not presented as reproducible. Switching production builds to a platform lock
requires the remaining G1 renderer/golden and native validation evidence.

The mandatory initial release candidate is Windows x64 on CPython 3.9:
`locks/windows-x64-py39.txt`. The optional G3 Linux x86_64 candidate uses
`locks/linux-x86_64-py39.txt`; that lock is not a distribution support claim.
Both select Playwright 1.60.0, whose wheel manifest selects Chromium/headless
shell 148.0.7778.96 at revision 1223 and FFmpeg 1011. Changing Playwright or
its browser manifest requires a dedicated dependency PR, an updated
platform-specific lock, renderer-spike review, and golden evidence; Dependabot
must not merge it automatically.

## Contributor setup

From a clean checkout with Python 3.9 or newer:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -c requirements/constraints.txt -e ".[test]"
python -m unittest tests.test_cli tests.test_community tests.test_i18n tests.test_packaging \
  tests.test_quality_foundations \
  tests.test_core.TestTitleExtraction \
  tests.test_core.TestHeaderFooterConfig \
  tests.test_core.TestTemplateBuilding \
  tests.test_core.TestMarkdownConversion
```

On Windows, activate with `.venv\Scripts\activate` and use the same `python`
commands. The command above is the pure, browser-free gate. Browser-backed
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

The initial coverage floor is 30% overall, based on a measured 31% branch-aware
pure-suite result. Reports retain per-module values so GUI, CLI, core, and i18n
gaps remain visible. Raising the floor requires added tests; it must never be
lowered to accept a regression.

## Hashed Linux candidate install

On native Linux x86_64 with CPython 3.9:

```bash
python -m pip install --require-hashes \
  -r requirements/locks/linux-x86_64-py39.txt
```

The wheels were resolved for a manylinux2014 x86_64 input set. This ensures
archive integrity, not runtime compatibility. The exact candidate still
requires the distribution, glibc, desktop-library, offline, GUI/CLI and
canonical checks in `docs/LINUX_BUILD_VALIDATION.md`.
