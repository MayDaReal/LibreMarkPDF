# Dependency workflow

The adjacent `*.in` files specify the runtime, GUI, build and test inputs.
`constraints.txt` pins the complete dependency graph. `requirements.txt`
uses the pinned GUI and build graph for source development.

The Ubuntu 24.04 x86_64 and Windows x64 lanes use standard CPython 3.14 and
their respective native locks in `locks/`. Use CPython 3.14.10 for migration
validation. Resolve and verify each wheel lock on its target platform.

Playwright's installed wheel metadata and `driver/package/browsers.json`
identify the Python package, Chromium headless shell and FFmpeg revisions.
Keep renderer dependency updates in individual PRs and require native visual
evidence for each change. Run `python -m libremark_pdf doctor --json` to see
the selected identities and locate the exact staged shell.

## Linux contributor setup

Run `./bootstrap-linux.sh` to install the hash-locked wheels and stage the
native browser in `browser-linux/`. Activate `.venv-linux-py314` to run
the application or tools. For an editable install in that environment, use
`python -m pip install --no-build-isolation --no-deps -e .` followed by
`python -m pip check`.

Setup and browser staging can access the network. Normal conversion uses
local resources. See [native validation](../docs/VALIDATION.md) for the
complete Xvfb test, 75% branch coverage floor, and artifact gates.

## Refresh the native Linux lock

Run on Ubuntu 24.04 x86_64 using standard CPython 3.14. Verify the package
versions, wheel selection and security advisories before refreshing the lock.

```bash
lock_work="$(mktemp -d)"
python -m pip install --dry-run --ignore-installed --only-binary=:all: \
  --report "$lock_work/report.json" -c requirements/constraints.txt \
  -r requirements/build.in -r requirements/test.in
python - "$lock_work/report.json" > "$lock_work/linux-x86_64-py314.txt" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("# Native Ubuntu 24.04 x86_64 / CPython 3.14 wheel lock.")
print("# Refresh and verify using requirements/README.md.")
for item in sorted(report["install"], key=lambda item: item["metadata"]["name"].lower()):
    metadata = item["metadata"]
    download = item["download_info"]
    if item["is_yanked"] or not download["url"].endswith(".whl"):
        raise SystemExit(f"Unsupported archive for {metadata['name']}")
    digest = download["archive_info"]["hashes"]["sha256"]
    print(f"{metadata['name'].lower()}=={metadata['version']} " + chr(92))
    print(f"    --hash=sha256:{digest}")
PY
python -m venv "$lock_work/venv"
"$lock_work/venv/bin/python" -m pip install --only-binary=:all: --require-hashes \
  -r "$lock_work/linux-x86_64-py314.txt"
"$lock_work/venv/bin/python" -m pip check
cp "$lock_work/linux-x86_64-py314.txt" requirements/locks/linux-x86_64-py314.txt
```

## Refresh the native Windows lock

On Windows x64, run the following in PowerShell with `python` set to standard
CPython 3.14 x64. Use a fresh scratch directory outside tracked source.

```powershell
$lockWork = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $lockWork | Out-Null
python -m pip install --dry-run --ignore-installed --only-binary=:all: `
    --report "$lockWork/report.json" -c requirements/constraints.txt `
    -r requirements/build.in -r requirements/test.in
if ($LASTEXITCODE -ne 0) { throw "Wheel resolution failed." }
$report = Get-Content -LiteralPath "$lockWork/report.json" -Raw | ConvertFrom-Json
$lines = @(
    '# Native Windows x64 / CPython 3.14 wheel lock.'
    '# Refresh and verify using requirements/README.md.'
)
foreach ($item in ($report.install | Sort-Object { $_.metadata.name })) {
    $download = $item.download_info
    $digest = $download.archive_info.hashes.sha256
    if ($item.is_yanked -or $download.url -notlike '*.whl' -or $digest -notmatch '^[0-9a-f]{64}$') {
        throw "Unsupported archive for $($item.metadata.name)"
    }
    $lines += "$($item.metadata.name.ToLowerInvariant())==$($item.metadata.version) \"
    $lines += "    --hash=sha256:$digest"
}
$lock = Join-Path $lockWork 'windows-x64-py314.txt'
[IO.File]::WriteAllText($lock, ($lines -join "`n") + "`n")
python -m venv "$lockWork/venv"
if ($LASTEXITCODE -ne 0) { throw "Environment creation failed." }
$venvPython = Join-Path $lockWork 'venv/Scripts/python.exe'
& $venvPython -m pip install --only-binary=:all: --require-hashes -r $lock
if ($LASTEXITCODE -ne 0) { throw "Locked wheel installation failed." }
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw "Dependency check failed." }
Copy-Item -LiteralPath $lock -Destination requirements/locks/windows-x64-py314.txt
```
