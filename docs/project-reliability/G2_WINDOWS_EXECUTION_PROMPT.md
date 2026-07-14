# G2 native Windows evidence prompt

Run this evidence lane on native Windows x64, not WSL.  It is an execution
request, not permission to change source, install during the offline proof, or
publish anything.  Record every failure, warning, and unverified item.  Do not
substitute a newer browser, font, dependency, or expected-data manifest.

Candidate source commit: `1822a7c538558622a088ef464f15ddee408eef1d`

Expected-data SHA-256: `2cdd297d108f6a8a0bd15593f7b81b2a3b545ff2795b74e4c94a4ae7735fd4b5`
Windows lock SHA-256: `cfb6b7de3d272bd57eac79c38e68fad3c6836f1930353cd789dad9251fd87c9d`

## Preconditions

- Native Windows x64 and CPython 3.9.
- A clean checkout containing the candidate commit and its signed-review
  baseline data.
- Dependencies installed from `requirements/locks/windows-x64-py39.txt` before
  the offline proof.
- The locked Playwright 1.60.0 Chromium/headless shell revision 1223 and the
  seven approved static fonts are already staged locally.  Do **not** run a
  browser install/download command in this lane.
- Disconnect Wi-Fi/Ethernet before the commands below and retain a screenshot
  or administrator-provided record of that state.  A proxy setting alone is
  insufficient.

## Commands

Open PowerShell in the checkout and run the following commands verbatim,
capturing standard output and standard error into the named files.  `$LASTEXITCODE`
must be appended to the matching log after each external command.

```powershell
$ErrorActionPreference = 'Continue'
$candidate = '1822a7c538558622a088ef464f15ddee408eef1d'
$evidence = Join-Path $env:TEMP 'LibreMark-G2-Windows-1822a7c'
New-Item -ItemType Directory -Force $evidence | Out-Null
git checkout --detach $candidate
git status --short --branch | Tee-Object "$evidence\git-before.txt"
git rev-parse HEAD | Tee-Object "$evidence\commit.txt"
if ((git rev-parse HEAD) -ne $candidate) { throw 'Wrong candidate commit' }

$python = '.\venv\Scripts\python.exe'
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\browsers"
Get-ComputerInfo | Out-File "$evidence\system.txt" -Encoding utf8
Get-NetAdapter | Format-List * | Out-File "$evidence\network-disconnected.txt" -Encoding utf8
& $python --version 2>&1 | Tee-Object "$evidence\python.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\python.txt"
& $python -m pip freeze 2>&1 | Tee-Object "$evidence\dependencies.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\dependencies.txt"
& $python -c "import importlib.metadata; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print('playwright='+importlib.metadata.version('playwright')); print('executable='+p.chromium.executable_path); b=p.chromium.launch(); print('browser='+b.version); b.close(); p.stop()" 2>&1 | Tee-Object "$evidence\renderer.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\renderer.txt"
Get-FileHash requirements\locks\windows-x64-py39.txt, tests\fixtures\g2\manifest.json, tests\goldens\g2\expected.json -Algorithm SHA256 | Format-Table -AutoSize | Out-File "$evidence\input-hashes.txt" -Encoding utf8
Get-ChildItem fonts -File | Get-FileHash -Algorithm SHA256 | Format-Table -AutoSize | Add-Content "$evidence\input-hashes.txt"

& $python -m unittest discover -s tests -v 2>&1 | Tee-Object "$evidence\unittest.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\unittest.txt"
& $python -m libremark_pdf convert --help 2>&1 | Tee-Object "$evidence\cli-help.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\cli-help.txt"
& $python -m libremark_pdf convert README.md --json 2>&1 | Tee-Object "$evidence\cli-json.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\cli-json.txt"

$actual = Join-Path $evidence 'actual'
$diff = Join-Path $evidence 'diff'
& $python tools\g2_visual_harness.py --manifest tests\fixtures\g2\manifest.json --actual-dir $actual --report (Join-Path $evidence 'generate-report.json') --diff-dir $diff --generate-only 2>&1 | Tee-Object "$evidence\generate.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\generate.txt"
& $python tools\g2_visual_harness.py --manifest tests\fixtures\g2\manifest.json --expected tests\goldens\g2\expected.json --actual-dir $actual --report (Join-Path $evidence 'comparison-report.json') --diff-dir $diff --collect-only 2>&1 | Tee-Object "$evidence\compare.txt"; "EXIT=$LASTEXITCODE" | Add-Content "$evidence\compare.txt"

git status --short --branch | Tee-Object "$evidence\git-after.txt"
Get-ChildItem -Recurse $evidence | Get-FileHash -Algorithm SHA256 | Format-Table -AutoSize | Out-File "$evidence\evidence-file-hashes.txt" -Encoding utf8
$archive = "$evidence.zip"
Compress-Archive -Path "$evidence\*" -DestinationPath $archive -Force
Get-Item $archive | Select-Object FullName,Length | Format-List
Get-FileHash $archive -Algorithm SHA256 | Format-List
```

If `$PWD\browsers` is not the staged locked payload, stop and report that
blocker; do not point the run at a cache containing a different revision.
The source-tree font inventory is recorded in `input-hashes.txt`; it must
contain exactly the seven approved static font files.

## Return bundle and review checklist

Return the ZIP path, byte size, SHA-256, and its unmodified contents.  It must
include at least these filenames:

- `git-before.txt`, `commit.txt`, `git-after.txt`;
- `system.txt`, `network-disconnected.txt`, `python.txt`,
  `dependencies.txt`, `renderer.txt`, `input-hashes.txt`;
- `unittest.txt`, `cli-help.txt`, `cli-json.txt`, `generate.txt`,
  `compare.txt`;
- `actual/evidence.json`, all `actual/entries/*.json`,
  `comparison-report.json`, and `evidence-file-hashes.txt`.

The written response must explicitly state the Windows edition/build and x64
architecture, Python/dependency/Playwright/Chromium versions, font and
fixture-manifest hashes, disconnected-network evidence, every command exit
code, comparison result, archive metadata, and all failures/warnings/unverified
items.  The integration owner reviews the bundle before changing G2 status.
