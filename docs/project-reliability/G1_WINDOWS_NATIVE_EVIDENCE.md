# G1 Windows Native Evidence

Status: **Windows evidence package only — not a G1 decision**
Evidence dates: 2026-07-13 to 2026-07-14 (Europe/Paris)
Packaging source commit: `50f134121366e4922774bd67c6e5e7554108d09b`
Visual source commits: `4107aea0d7d28a8bf9728d4a27854c5210393380`,
`93fbf83404339999064e7b09b18399ea9dfb4606`
Native lane: Windows x64, PyInstaller candidate
Evidence root: `%TEMP%\LibreMark G1 Windows 20260713` (outside the repository)

This report records measured Windows facts for the integrator. It does not
declare Gate G1 passed, does not advertise Windows as an official platform, and
does not infer security or portability from a successful local build.

## 1. Scope, ownership, and source state

The repository files owned by this validation are this report,
`G1_WINDOWS_EVIDENCE_MANIFEST.sha256`, `LibreMarkPDF-portable.spec`,
`build_portable.bat`, the focused additions to `tests/test_packaging.py`, and
the portable-candidate additions to `docs/WINDOWS_BUILD_VALIDATION.md`.
Production code, rendering behavior, CSS, fonts, margins, pagination, identity
assets, dependency declarations, the existing onefile spec/script, and the
immutable `BASELINE_AUDIT.md` were not modified. The packaging additions were
made only after explicit owner authorization on 2026-07-14.

The required initial commands produced the following results:

| Command | Exit | Observable result |
| --- | ---: | --- |
| `git status --short --branch` | 1 | Git rejected the repository because its owner is the local Administrators group (`dubious ownership`). No state changed. |
| `git rev-parse HEAD` | 1 | Same safe-directory rejection. No state changed. |
| `git -c safe.directory=D:/repos/LibreMarkPDF status --short --branch` | 0 | `## main`; no tracked or untracked entries. |
| `git -c safe.directory=D:/repos/LibreMarkPDF rev-parse HEAD` | 0 | `50f134121366e4922774bd67c6e5e7554108d09b`. |

A clean source export was made without touching the working tree:

```powershell
git -c safe.directory=D:/repos/LibreMarkPDF archive --format=zip `
  --output="$env:TEMP\LibreMark G1 Windows 20260713\source-50f1341.zip" HEAD
Expand-Archive -LiteralPath "$env:TEMP\LibreMark G1 Windows 20260713\source-50f1341.zip" `
  -DestinationPath "$env:TEMP\LibreMark G1 Windows 20260713\source-50f1341"
```

Exit was 0. The archive is 190,018 bytes, SHA-256
`A2FC0CA7D69E68682D945CDFC12857114393F1091A1BF840E8FC18C7CCA3F37C`.
This is a clean committed-source export rather than a second Git worktree. The
local, intentionally untracked baseline was read from the original repository
and was not copied, edited, staged, or published.

Documentation discrepancy: the requested `docs/WINDOWS_VALIDATION.md` does not
exist at this commit. The available and reviewed guide is
`docs/WINDOWS_BUILD_VALIDATION.md`. `build_onefile.bat` is also absent.

## 2. Environment and provenance

| Component | Measured value |
| --- | --- |
| Windows | Windows 10 Pro / Professional, display version 25H2, build 26200, `Microsoft Windows 10.0.26200`, 64-bit |
| Architecture | x64; Intel Core i7-12700KF, 12 cores / 20 logical processors |
| Memory / power | 68,553,269,248 bytes RAM; Power saver plan during measurements |
| PowerShell | 5.1.26100.8655, Desktop edition |
| Python | CPython 3.9.13 x64 in `%EVIDENCE_ROOT%\venv-py39` |
| pip | 22.0.4 |
| PyInstaller | 6.21.0 |
| Playwright | 1.60.0 |
| Chromium | Chrome for Testing headless shell 148.0.7778.96, Playwright revision 1223 |
| Markdown / PDF tools | Markdown 3.9; pypdfium2 5.11.0; Pillow 11.3.0 |
| Source lock | `requirements/locks/windows-x64-py39.txt`, SHA-256 `CFB6B7DE3D272BD57EAC79C38E68FAD3C6836F1930353CD789DAD9251FD87C9D` |
| Onefile PyInstaller spec | `LibreMarkPDF.spec`, SHA-256 `A92AE27E401BAFD9563908545DFCEB27DB47E171D3CCF5DA8C84CF58ACB091E0` |
| Portable PyInstaller spec | `LibreMarkPDF-portable.spec`, SHA-256 `60385BE0221DBCF65D5C32B2520FA27E1837BC9E2BBFF336865F93AA33847DAF` |

Python 3.9 was initially unavailable (`py -0p` listed only 3.10 and 3.11).
The official Python 3.9.13 x64 installer had SHA-256
`FB3D0466F3754752CA7FD839A09FFE53375FF2C981279FD4BC23A005458F7F5D`
and a valid Python Software Foundation Authenticode signature (certificate
thumbprint `36168EE17C1A240517388540C903BB6717DD2563`). The silent installer exited 0,
but its unquoted target containing spaces was parsed as `%TEMP%\LibreMark`.
Verification of the requested target therefore exited 1. The installed 3.9.13
interpreter was found through `py -3.9`, and it created the correctly located
isolated virtual environment. This installer-path discrepancy is retained as an
operational limitation.

Environment inventory: `Z_environment_inventory.log`, 5,663 bytes, SHA-256
`4D4C141E9328ED25B65A08797C52D312A68FF8AD9006D57FFBA87F27253132DA`.

## 3. Task evidence

### QAS-003 / QAS-004 — clean Python 3.9 install and tests

**State: passed for the measured Windows environment; partial as gate evidence.**

Before: Python 3.9 and the target browser were absent. After: an isolated 3.9
environment was populated strictly from the Windows x64 Python 3.9 hash lock.
No production requirement was changed.

```powershell
python -m pip install --require-hashes `
  -r requirements\locks\windows-x64-py39.txt
```

Exit 0. Log: `A_clean_install.log`, SHA-256
`9E0952D8803574673B677BB25E4BF814853F42AD70CD2CD2161B65460109AEC9`.

Pure tests were run with an empty `PLAYWRIGHT_BROWSERS_PATH`:

```powershell
python -m unittest tests.test_cli tests.test_community tests.test_i18n `
  tests.test_packaging tests.test_quality_foundations `
  tests.test_core.TestTitleExtraction tests.test_core.TestHeaderFooterConfig `
  tests.test_core.TestTemplateBuilding tests.test_core.TestMarkdownConversion -v
python -m libremark_pdf convert --help
```

Both commands exited 0. The pure selection ran 36 tests in 0.091 seconds. Log:
`A_pure_tests_and_help.log`, SHA-256
`F740DBF084004E32B19AE3661988E4F31E825A95BCBFA8FD06C7553A61319D12`.

With the locked browser installed, the required full suite was also run:

```powershell
python -m unittest discover -s tests -v
```

Exit 0; 39 tests, 31.523 seconds, `OK`. Combined probe/test log:
`B_probe_and_full_tests.log`, SHA-256
`22461373B143FFF8E2D8233D4354323C6FC824FCE6C5E4E27819F704A796A586`.
The next-gate dependency remains an approved native artifact and complete
Windows functional evidence, not merely source-level test success.

### SPIKE-REN-001 / SPIKE-REN-004 / SPIKE-REN-005 — locked browser probe

**State: passed as a renderer spike; partial for production enforcement.**

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = `
  "$env:TEMP\LibreMark G1 Windows 20260713\playwright-browsers-1223"
python -m playwright install --only-shell chromium
python spikes\g1\renderer_probe.py `
  --output "$env:TEMP\LibreMark G1 Windows 20260713\B_renderer_probe_windows.json"
```

Both commands exited 0. Install log SHA-256:
`8A57382B6D77FF8F612AE4CCF82108B474A1059EADCEFD36E24C3F42E2C2B0A6`.
The executable is
`%EVIDENCE_ROOT%\playwright-browsers-1223\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe`,
201,396,224 bytes, SHA-256
`2D8F2ABAD1A0F2998AAF861967C374D4AAD6A104916B8794318760ED35DB772F`.
Its `--version` output is `Google Chrome for Testing 148.0.7778.96`.

The JSON probe, 1,145 bytes, SHA-256
`F59A29D4D356947F0C28100CF35EDC6A5E2FB1F7C0200EEFC06904937A737F25`,
records:

- browser version 148.0.7778.96 and revision-1223 executable path;
- `java_script_enabled: false`, service workers blocked, network policy denied;
- local fixture: zero HTTP/HTTPS attempts/responses, embedded image width 121,
  and no script execution;
- hostile fixture: one blocked attempt to
  `https://example.invalid/blocked.png`, zero external responses, and remote
  image width zero;
- profile fingerprint
  `bc545f04fd2b19f804e6f9d7cef7a29957259a2b2a0e2002aa3e145a107f7316`.

Limitation and risk: this is the non-production G1 spike. The current
`libremark_pdf/core.py` does not apply the ADR-004 network/JavaScript/service
worker policy in the same way. The probe cannot be used to claim that the
production conversion path enforces those controls. The next gate depends on
implementing and testing the approved renderer policy without rendering drift.

### SPIKE-PKG-001 / SPIKE-PKG-002 / WIN-004 — artifact construction

**State: partial. Onefile and portable diagnostic candidates built; no windowed release candidate.**

The original repository spec contains an `EXE` and no `COLLECT`, so it defines
onefile packaging. After the owner explicitly authorized a portable definition,
`LibreMarkPDF-portable.spec` added the standard PyInstaller `COLLECT` layout
with the same package entry point and the same frozen `style.css`, icons,
assets, and browser resources. `build_portable.bat` requires CPython 3.9,
PyInstaller 6.21.0, and a pre-staged `chrome-headless-shell.exe`; it performs no
dependency installation or browser download and accepts external dist/work
paths. The existing onefile files remain unchanged.

`build.bat` was not executed because it creates its own environment, installs
the lower-bound `requirements.txt`, downloads the current full Chromium, and
pauses interactively. Those actions would not preserve the locked G1 inputs.
Instead, the authoritative spec was invoked directly from the hash-locked
environment after copying revision 1223 into the clean export's `browsers`
directory. `LIBREMARK_PDF_CONSOLE=1` selected the existing diagnostic console
branch required to exercise CLI stdout/stderr.

```powershell
$env:LIBREMARK_PDF_CONSOLE = '1'
python -m PyInstaller --noconfirm --clean `
  --distpath "%EVIDENCE_ROOT%\artifacts\onefile-console" `
  --workpath "%EVIDENCE_ROOT%\build-onefile-console" LibreMarkPDF.spec
```

Exit 0; 62.426 seconds. Build log SHA-256:
`77DA041E88ADF68787568DE489BF80A30211D23A0CFCBFD232CCA992843A182C`.

Candidate provenance:

| Property | Measured value |
| --- | --- |
| Path | `%EVIDENCE_ROOT%\artifacts\onefile-console\LibreMarkPDF.exe` |
| Size | 177,256,363 bytes |
| SHA-256 | `CA1FC08B1A6B7A3A4B4F3D43FCE3D5E81D8D0D0A1616C040E94246408D3E4E06` |
| PE | machine `0x8664` (AMD64), PE32+, console subsystem 3 |
| Signature | Not signed |
| Inputs | commit `50f1341`, Python 3.9.13, PyInstaller 6.21.0, Playwright 1.60.0, Chromium 148.0.7778.96/revision 1223 |

This is a console diagnostic candidate, not the windowed release candidate. It
can expose CLI streams, but launching its GUI also exposes a console. WIN-001
therefore remains a release blocker.

The portable spec and script were copied into the same clean source export,
whose `browsers` directory already contained revision 1223. The authorized
build command was:

```powershell
$env:LIBREMARK_PDF_PYTHON = "%EVIDENCE_ROOT%\venv-py39\Scripts\python.exe"
$env:LIBREMARK_PDF_DISTPATH = "%EVIDENCE_ROOT%\artifacts\portable-console-rebuild"
$env:LIBREMARK_PDF_WORKPATH = "%EVIDENCE_ROOT%\build-portable-console-rebuild"
$source = "%EVIDENCE_ROOT%\source-50f1341"
& (Join-Path $source "build_portable.bat") --console
```

Two clean work/dist paths completed with exit 0. The retained second-build log
has SHA-256
`6299F9B8BF7832D8258B83F7D4BDF01E0C926CC0204EF40627760CD25DFD300D`.
The two directories each contained 1,447 files. They were not byte-reproducible:
only `LibreMarkPDF.exe` and `_internal/base_library.zip` differed; the remaining
1,445 files matched. Their total sizes differed by eight bytes. This divergence
is visible evidence, not treated as a pass.

Portable candidate provenance:

| Property | Measured value |
| --- | --- |
| Path | `%EVIDENCE_ROOT%\artifacts\portable-console-rebuild\LibreMarkPDF` |
| Directory | 1,447 files; 435,324,503 bytes |
| ZIP | 178,091,360 bytes; SHA-256 `C54F6B945871252538B078DAF24599C6A3B08994DDD91884E2ADA346A7E5691D` |
| Launcher | 2,777,472 bytes; SHA-256 `FC87C8B7D1418842535921A23C78E218EFCF635C706290FE77E8D0D806DC8B5B` |
| Directory manifest | SHA-256 `A5ACFAC6273CE04EB2892BA8B2C7FFDA6649EC0BA4B7C5048358D29BEDB7DBD2` |
| PE | machine `0x8664` (AMD64), PE32+, console subsystem 3 |
| Signature | Not signed |
| Inputs | commit `50f1341` plus the authorized spec/script above; Python 3.9.13, PyInstaller 6.21.0, Playwright 1.60.0, Chromium 148.0.7778.96/revision 1223 |

The first portable directory was 435,324,511 bytes; launcher SHA-256
`B396529F67744A5F0D69175A9A649AA764D6E849C056302C88007D0EA6E25622`;
directory-manifest SHA-256
`E2EB265DF53933DBC72B454D353CCE0370983159FDD66AB5DE1473E0C646B9EA`.
The focused packaging suite passed 7 tests, then the complete target-browser
suite passed 39 tests in 4.513 seconds (`OK`, exit 0). No generated build,
browser, PDF, raw log, or ZIP was placed in Git.

### WIN-005 — CLI, GUI, preview, empty cache, and paths with spaces

**State: partial. CLI, GUI file conversion, and preview passed; GUI usability anomalies remain.**

The candidate and README input were copied to
`%EVIDENCE_ROOT%\external path\entrée avec espaces`. Every invocation used a
fresh external `USERPROFILE`, `HOME`, `LOCALAPPDATA`, `APPDATA`, `TEMP`, and
`TMP`, without touching personal cache data.

CLI help exited 0 twice. Measured elapsed times were 3.991 and 3.777 seconds.
The successful conversion command was:

```powershell
LibreMarkPDF.exe convert "README entrée avec espaces.md" `
  -o "sortie avec espaces.pdf" --json
```

Exit 0; 30.153 seconds. Stdout is a single valid JSON document (`status: ok`,
`error: null`) and stderr is empty. Stdout SHA-256 is
`2A9CE68F9D6EE217B894D04067B0161253A5FC54F955639813FB18157CA109D3`;
empty stderr SHA-256 is
`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
The generated PDF is 91,480 bytes, SHA-256
`A85321FFDCD99A9E07F822770989E76F9903B2797A881E7538D0C09BDA9AAD62`,
three pages, each 595.92 by 842.88 points.

The controlled missing-input invocation was captured with native
`System.Diagnostics.ProcessStartInfo` to avoid PowerShell adding its own error
record. It exited 1, wrote zero bytes to stdout, and wrote an actionable
`Input file not found` error to stderr. Stdout SHA-256 is the empty-file hash;
stderr SHA-256 is
`C8B9DFFD400516EDFEBF4824751E70638F07691A6CB38BA8E5FD246D9CB028A9`.
CLI functional log SHA-256:
`147A979468FFC176BAE6F835445DD507F97DF7C2D35A9DE626ABFAAE1C188D12`.

GUI observations from the exact candidate:

- launch succeeded from the Unicode/spaces path with an empty profile;
- title, logo/application icon, French labels, action buttons, status icons,
  and `Ready` state were visible;
- `Refresh preview` produced a non-empty A4 sample preview with heading, table,
  and `Page 1 / 1`; the app remained responsive;
- `WM_CLOSE` caused normal closure, and no `_MEI*` extraction directory remained;
- startup screenshot SHA-256:
  `20881CA79C8E56804E6F81F98E09AB0CB5E145BA53F5DE951F43DCCAA58BBFA7`;
- preview screenshot SHA-256:
  `8023E2BE5D7CC9A7243601E632F2827850775BA72E3DEE8EE9026618D30CC142`.

Native UI automation could not reliably open the file selector during the
initial run. On 2026-07-14, the operator witnessed the exact candidate opening
the Unicode/spaces input through the Windows file picker, displaying the
preview and expected icons, showing `Génération en cours...`, and completing
with `Terminé: 1 PDF généré(s).` The resulting
`README entrée avec espaces.pdf` is 91,480 bytes, SHA-256
`987392BD4A58023A48856A7D203CF626EA652247BC8720B18C8F16CE243B4F54`,
three pages, each 595.92 by 842.88 points. The operator closed the application
normally.

Two GUI anomalies were observed. Drag-and-drop did not accept the Markdown,
although the supported Windows file picker path worked. After preview display,
the `Générer le PDF` button moved below the visible window on a lower-height
display; the operator had to enlarge the window and reported that another
screen did not have enough vertical pixels to reach it. These are usability
defects and do not invalidate the witnessed picker-based conversion.

Across three isolated profiles, `%LOCALAPPDATA%\ms-playwright` remained absent:
the candidate located the embedded revision-1223 browser without a download.
The final cache-check shell command itself exited 1 because its last
`Get-Process` query correctly found no running process; the recorded cache
observations remain valid. Timing/GUI log SHA-256:
`28F5886D7F9819D16353BE396BA8D9A97F94D700E36C7871CE773549E6FF16BB`.

Risk: this host has system Python installations. Running outside an activated
virtual environment demonstrates bundling behavior, but is not proof on a
machine with no Python installed.

The portable candidate was then exercised from its complete directory, whose
path contains spaces, against
`%EVIDENCE_ROOT%\portable external path\entrée avec espaces`. With a new empty
profile, `convert --help` exited 0 in 1.131 seconds. JSON conversion exited 0
in 2.012 seconds, produced one clean JSON document with empty stderr, created
no Playwright cache, and used the embedded
`chromium_headless_shell-1223` executable reporting version 148.0.7778.96. The
PDF is 91,480 bytes, SHA-256
`914DC4871DB06F233F1D09FD9E5CB47D4C0542E749AFB726904109366C9FB3E1`,
three pages of 595.92 by 842.88 points. A missing input in human-output mode
exited 1, wrote zero stdout bytes, and wrote an actionable error to stderr;
stderr SHA-256 is
`C5FA013F6713A8F8DDEB41E922C25BFF666832347497D82232E84B7CEE3ED6B0`.

Under a standard non-elevated account, the portable GUI launched and closed
with exit 0. The operator confirmed successful drag-and-drop, correct preview,
icons, progress/completion states, and PDF generation. The resulting PDF is
91,480 bytes, SHA-256
`6EC6D735F312FF3A3B07499AE2E002DBA489EA91A89BC3172709AA0A8CFE610E`,
three A4 pages. The same low-height defect remained: after preview, the Generate
button can move below the accessible window area. A console also appeared by
design because this is the diagnostic `--console` candidate.

An attempted automated GUI-startup timing probe failed to recognize the visible
Tk windows, timed out at 30 seconds, and left the opened windows for manual
closure. The operator closed them and verified zero remaining LibreMarkPDF
processes. Those 30-second values are harness errors and are excluded from all
performance results. Portable GUI cold/warm startup remains unverified.

### WIN-006 — offline runtime

**State: passed for the measured firewall-default-deny condition; strict air-gap remains unverified.**

The attempted reversible outbound rule was:

```powershell
New-NetFirewallRule `
  -DisplayName 'LibreMark PDF G1 temporary outbound block 20260713' `
  -Direction Outbound -Program '<candidate LibreMarkPDF.exe>' `
  -Action Block -Profile Any
```

It failed with `Access denied` (exit 1) because the shell was not elevated.
Final cleanup verification found no rule with that display name
(`FIREWALL_RULE_REMOVED=True`). Log SHA-256:
`2124FED58DAE764AE4585FBB8997253AB0C87C70CED986A99F7DDC22C9687AE1`.

On 2026-07-14, an elevated follow-up recorded all Domain, Private, and Public
profiles as enabled. Their original `DefaultOutboundAction` values were
`NotConfigured`. A `try`/`finally` procedure changed all three to `Block`, ran
the candidate, and restored all three to `NotConfigured` after each test.

The first CLI attempt under `Block` exited 2 without conversion because the
test script used PowerShell's reserved automatic `$input` variable; the
application correctly reported that `INPUT.md` was required. This was a test
harness error. The corrected invocation used `$inputPath` and produced clean
JSON with `status: ok`, exit 0, and a PDF while all three profiles displayed
`Block`. The restored profiles all displayed `NotConfigured`. The PDF is
91,480 bytes, SHA-256
`FC443C6F1F109BC08F9A196BF9E8C80C5DC4622AB622D0B93B204E50A303338D`,
three pages of 595.92 by 842.88 points.

The same elevated procedure then launched the GUI with all three profiles at
`Block` and waited for normal process exit. The operator selected the distinct
Unicode/spaces Markdown through the Windows picker, refreshed the preview,
generated the PDF, and observed correct icons and rendering. The GUI has no
Reset button; an earlier operator description of Reset was clarified and is
not claimed as evidence. Drag-and-drop did not work on this host run. The GUI process exited 0, the PDF
existed before reporting completion, and all profiles were restored to
`NotConfigured`. The GUI offline PDF is 91,480 bytes, SHA-256
`B4B0AC78D8555C767F4DD0A399EE86AE1FE396ABEEFB670B4BBF6B6EDBD4E66B`,
three pages of 595.92 by 842.88 points.

This proves successful CLI and GUI operation under the measured Windows
Firewall default-outbound-deny configuration. It is not packet-capture evidence
and is weaker than disabling every network adapter: pre-existing explicit allow
rules were not exhaustively excluded. A disconnected-adapter or captured-traffic
run is still required if the integrator interprets “strict offline” as an
air-gap rather than this firewall condition.

On 2026-07-14, a second, stronger run used a newly enabled Windows Sandbox
(`wsb` 0.5.3.0) with `<Networking>Disable</Networking>`. Enabling the optional
component exposed a host configuration issue: firmware virtualization and SLAT
were enabled, but BCD had `hypervisorlaunchtype Off`. After the operator
explicitly changed it to `Auto` and restarted, the Sandbox launched. This is a
host setup fact, not a LibreMark PDF change.

The final Sandbox instance was disposable and reported:

- no `python.exe` or `py.exe` command;
- zero Python registry entries under HKLM and HKCU;
- zero network adapters and an unsuccessful HTTPS probe to `example.com:443`;
- a read-only mapped input containing the candidate with its expected SHA-256;
- an external writable test path containing both Unicode and spaces;
- no `%LOCALAPPDATA%\ms-playwright` before CLI conversion, after CLI
  conversion, or after GUI conversion.

In that environment, `convert --help` exited 0. CLI conversion returned clean
JSON with `status: ok`, exited 0, and created a 91,480-byte, three-page A4 PDF
with SHA-256
`4C3A8BF9C60B01E65F3FEECF0A2D3AD434CBCBFC5AB5CA797F6E3C99BBD9ED09`.
The GUI then opened the Markdown, displayed the same correct preview/icons and
completion behavior as the host, generated a 91,480-byte, three-page A4 PDF,
and exited 0. Its PDF SHA-256 is
`6B23879726DA74335E14F1CB9C231ED2CFA1DA0B1FE077B146B145A48E422F41`.
Drag-and-drop worked in the Sandbox, showing that the host-only drag-and-drop
failure is environment-dependent. The low-height layout issue remained.

Both Sandbox PDFs were copied to `C:\LibreMarkG1Evidence` and re-hashed on the
host before the disposable instance was stopped. This supplies no-Python and
network-adapter-disabled CLI/GUI evidence. Its limitation is that Windows
Sandbox is a disposable VM using the host Windows build, not an independently
provisioned physical Windows installation.

The portable candidate was separately repeated with a new empty profile while
all three host firewall profiles displayed `DefaultOutboundAction=Block`.
Portable CLI conversion emitted clean success JSON, exited 0, created no
Playwright cache, and produced a 91,480-byte, three-page A4 PDF with SHA-256
`CE78A4DE5C7C9F9E40E4F786E05E298D7A9087A22640000BCE04E32425BA06D7`.
The firewall profiles were restored to `NotConfigured`.

An elevated portable GUI run under the same block exited 0, produced no cache,
and created a 91,480-byte, three-page A4 PDF with SHA-256
`11F3C4F71DB9BDB4C8C09BB048254D57033D6DBCC82C98F351191915F946B04B`.
Preview, icons, status, and conversion were correct, but drag-and-drop failed.
A controlled follow-up left the firewall block in the administrator shell and
launched the portable GUI from a separate standard-user shell. Drag-and-drop
then worked, preview/conversion succeeded, process exit was 0, and the PDF was
91,480 bytes with SHA-256
`6A06DA9F92D38467B2F591FEB16BD6EC911E60CC8E841390337EAA9C2F4E9369`.
All profiles were again restored to `NotConfigured`.

This paired observation supports the Windows UIPI explanation: Explorer at
medium integrity cannot perform the same UI interaction with an elevated
target, while the standard-to-standard path works. It disproves a network
dependency for drag-and-drop but does not claim drag-and-drop must work for an
intentionally elevated application.

### WIN-007 — visual evidence

**State: partial inventory; visual equivalence unverified.**

The README PDF above was rasterized at 144 DPI with pypdfium2 5.11.0. Its three
1192 by 1686 pixel pages have SHA-256 values:

1. `EB5FD3ABA0BD018AC99EC21BA607EB8912B5FBAAA707849FF88A1A5ACA407211`
2. `C38B2D89D2A5F179DFAB69A56A33C215F2DFE0913D8591515C0712D6A9B537A0`
3. `229D85B84E21DBF2B18AA3932B7E702C32444FBF1C4C26316D135DF605165F3B`

Inventory JSON SHA-256:
`61280412ADA6490D8AB90BFE89C208B4DC40CEF989228A5BBEAD024CCD5907CC`.
Page 1 was visually inspected and appeared structurally coherent, including
the `Page 1 / 3` footer. This is observation, not a golden comparison.

The committed repository has no approved canonical fixture corpus, Windows
goldens, connected-region baseline, or completed native page-pair evidence.
Consequently no SSIM/pixel/connected-region threshold comparison was possible,
and cross-OS structural/strict visual equivalence remains unverified. Rendering
was not changed to reduce any difference.

### WIN-009 — artifact-format measurements and security observations

**State: partial comparison completed; controlled GUI cold starts remain unverified.**

Two measured warm GUI launches took 3.995 and 3.893 seconds. While running,
onefile extracted respectively to `_MEI34002` and `_MEI248242`; each extraction
occupied 432,547,031 bytes. After normal close, zero `_MEI*` directories
remained in the isolated `TEMP` directories. These are host-specific warm
measurements under the Power saver plan, not controlled cold-start results.

The portable directory stores the same 432,547,031 bytes under `_internal`.
Across connected, firewall-blocked CLI, and firewall-blocked GUI profiles, zero
`_MEI*` directories were created. The portable therefore moves that disk cost
from per-launch extraction to the persistent distribution directory.

Five alternating `convert --help` launches per format all exited 0 with empty
stderr. Onefile times were 4,025, 10,046, 4,016, 4,033, and 5,012 ms (median
4,033 ms). Portable times were 1,016, 1,011, 1,012, 1,031, and 1,018 ms
(median 1,016 ms). The timing CSV SHA-256 is
`DF8C9ED081F787CBF02BC21D3F9B089CBF5429C4C2F5932C96D3F1668B97BDF0`.

Three alternating README conversions per format all exited 0, emitted empty
stderr, created 91,480-byte PDFs, and left zero `_MEI*` directories. Onefile
times were 7,041, 7,026, and 7,040 ms (median 7,040 ms); portable times were
2,017, 2,012, and 2,022 ms (median 2,017 ms). On this workload the portable
median was approximately 71% faster. The conversion-timing CSV SHA-256 is
`96ECB3180212E197AC34CB052B5509A71E08461447D2A1486DD3FFC2D968369E`.
These are warm/current-system CLI measurements, not controlled post-reboot GUI
cold starts.

Microsoft Defender details:

- platform/product version 4.18.26060.3008;
- signature version 1.455.123.0, updated 2026-07-13 13:16 local time;
- `MpCmdRun.exe -Scan -ScanType 3 -File <candidate> -DisableRemediation`;
- exit 0 at 2026-07-13 21:48:10Z, with `found no threats`;
- log SHA-256
  `BDB860848131D3FB51E69426F2D4C8642E211E7047C5D07F77418F7DA802B393`.

A same-session comparison on 2026-07-14 used Defender product/platform
4.18.26060.3008, engine 1.1.26060.3008, and signature 1.455.130.0 updated at
02:12:57 local time. With `-DisableRemediation`, the unchanged onefile scan
exited 0 and reported `found no threats` (137 ms); the portable ZIP scan exited
0 with the same observation (14,713 ms); and the extracted portable-directory
scan exited 0 with the same observation (911 ms). These operator-console
transcripts were not retained as standalone logs. Absence of detection under
one definition set is not a security or quality inference.

On 2026-07-14, an unchanged copy in the operator's Downloads folder was given a
simulated Mark-of-the-Web alternate data stream containing `ZoneId=3`, a
deliberately non-resolving `HostUrl=https://example.invalid/LibreMarkPDF.exe`,
and the same-domain referrer. The primary EXE stream retained SHA-256
`CA1FC08B1A6B7A3A4B4F3D43FCE3D5E81D8D0D0A1616C040E94246408D3E4E06`.

Explorer launch displayed Microsoft Defender SmartScreen with
`Windows a protégé votre ordinateur`, described the application as
unrecognized, and initially offered only `Ne pas exécuter`. After
`Informations complémentaires`, it identified `LibreMarkPDF.exe`, showed
`Éditeur inconnu`, and offered `Exécuter quand même` or `Ne pas exécuter`.
Choosing `Ne pas exécuter` left no LibreMarkPDF process. On a separate launch,
the operator explicitly chose `Exécuter quand même`; the GUI opened normally,
closed normally, and left no process. The `Zone.Identifier` stream was absent
after that consent.

The portable launcher, SHA-256
`FC87C8B7D1418842535921A23C78E218EFCF635C706290FE77E8D0D806DC8B5B`,
was also unsigned and given a synthesized `ZoneId=3` marker. A standard-user
launch displayed the classic `File Open - Security Warning`, stated that the
publisher could not be verified, identified an unknown publisher, and offered
Run or Cancel. Cancel left no process. On a second launch, Run opened the GUI
directly and it worked normally; no purple SmartScreen reputation screen
appeared. The marker remained present until explicitly removed, and removing
it did not change the launcher hash.

The difference between these two locally synthesized-MOTW reactions is a
measured host behavior only. It does not establish how either ZIP/EXE would be
treated after a real browser download, signing, or reputation accumulation.

This is a passed local SmartScreen reaction test for an unsigned Internet-zone
file, supported by operator screenshots. It is not a real-download reputation
measurement because the Mark-of-the-Web and invalid source URL were synthesized.
It cannot predict the warning shown for a signed or publicly distributed
release. Defender's single no-detection result likewise is not evidence of
security or quality.

## 4. Portable versus onefile summary

| Element | Portable | Onefile | Verdict / limit |
| --- | --- | --- | --- |
| Approved build definition | Authorized `LibreMarkPDF-portable.spec` plus `build_portable.bat` | Existing `LibreMarkPDF.spec` plus `build.bat` | Portable definition is an uncommitted candidate layered on commit `50f1341`; existing onefile files unchanged. |
| Build | Two exit-0 onedir builds | Exit 0 onefile build | Both are unsigned diagnostic-console candidates, not windowed release candidates. |
| Distribution size | Directory 435,324,503 bytes; ZIP 178,091,360 bytes | EXE 177,256,363 bytes | Portable ZIP is 834,997 bytes (about 0.47%) larger. |
| PE / signature | AMD64 PE32+, console, unsigned | AMD64 PE32+, console, unsigned | Signing and GUI/no-console release strategy remain absent. |
| CLI help | Passed; median 1,016 ms over five | Passed; median 4,033 ms over five | Same profile and alternating order; onefile had a 10,046 ms outlier. |
| CLI JSON success | Passed | Passed | Clean JSON stdout, empty stderr, exit 0, PDF created. |
| Controlled CLI failure | Passed | Passed | Human mode: exit 1, empty stdout, actionable stderr. |
| Unicode/spaces path | CLI and GUI passed | CLI and GUI passed | Portable drag-and-drop works standard-to-standard; elevated failure is consistent with UIPI. |
| GUI launch/close | Passed under standard user | Passed | Correct visible controls; console appears for both diagnostic builds. |
| Preview | Passed | Passed | Correct non-empty previews observed. |
| GUI file conversion | Passed by operator witness | Passed by operator witness | Correct status/PDF; shared low-height button defect remains. |
| Empty user cache | Passed | Passed for host profiles and Sandbox | Embedded revision-1223 browser; no download or cache creation observed. |
| Offline CLI/GUI | Passed under firewall default deny | Passed under firewall deny and no-adapter Sandbox | Host profiles restored; strict packet capture still absent. |
| No-Python clean environment | Not independently repeated | Passed in Windows Sandbox | Portable uses the same frozen payload, but no separate Sandbox copy was run; do not infer the result. |
| First/second GUI startup | Not measured; harness failed | 3.995 / 3.893 seconds | Onefile observations exceed ADR-007's two-second criterion; controlled cold starts remain missing. |
| Conversion time | Median 2,017 ms over three | Median 7,040 ms over three | Portable about 71% faster on the measured README workload. |
| Temporary extraction | No `_MEI*`; 432,547,031 bytes persistent in `_internal` | 432,547,031-byte `_MEI*`; cleaned after exit | Portable avoids per-launch extraction in the measured profiles. |
| Build reproducibility | 1,445/1,447 files identical across two builds | Not repeated | Portable launcher and `base_library.zip` differed; byte reproducibility not proven. |
| Defender | ZIP and extracted folder: no threat found | No threat found | Same definitions; no security inference. |
| SmartScreen / attachment warning | Classic unknown-publisher warning; no purple screen after Run | Purple unrecognized-app SmartScreen warning | Both used synthesized Internet markers; real download/reputation remains unverified. |
| Visual equivalence | Same 91,480-byte/page-geometry observations; no golden comparison | Raster inventory only | Approved goldens, corpus, thresholds, and cross-OS pairs remain missing. |

## 5. Command deviations and reproducibility limits

All evidence-producing commands and their exit codes are recorded above and in
the hashed logs. The following non-evidence operator deviations are retained so
they cannot be mistaken for successful checks:

- initial Git commands exited 1 until scoped `safe.directory` was supplied;
- Python installer target parsing placed the interpreter at a shorter path;
- an exploratory recursive executable search selected DLLs as well as the
  browser executable and emitted launch errors; it was stopped and did not
  modify the browser payload;
- the first hash-inventory pipeline was rejected by PowerShell 5.1 with
  `EmptyPipeElement` (exit 1); the corrected read-only inventory succeeded;
- the first PowerShell CLI-failure capture added a PowerShell error record;
  native process capture was used as the authoritative evidence;
- firewall-rule creation exited 1 with access denied; cleanup verification
  confirmed that no rule remained.
- the first portable build exited 0 but its console stream was not retained as
  a file; the clean second build used a distinct work/dist path and retained a
  hashable log;
- the first portable directory manifests calculated relative paths from mixed
  Windows short/long roots; corrected manifests used the final folder marker;
- two timing-summary snippets were rejected by PowerShell 5.1 with
  `EmptyPipeElement` before launching candidates; corrected scripts stored the
  loop result before formatting;
- the GUI startup probe opened the applications but failed to discover their Tk
  windows, so every 30-second value was discarded; the operator closed the
  windows and verified zero remaining LibreMarkPDF processes;
- the first offline CLI follow-up used PowerShell's reserved `$input` variable
  and exited 2; the corrected `$inputPath` command exited 0;
- the SmartScreen marker was prepared from an elevated shell, but both launch
  decisions were observed from a verified standard-user shell; the marker was
  removed after the portable warning test without changing the EXE hash.

Raw logs, screenshots, browser payloads, build trees, executable, PDF, and
rasters remain outside Git under `%EVIDENCE_ROOT%`. The temporary directory is
not durable archival storage; the manifest permits integrity verification only
while those files are retained or after they are copied to an approved evidence
store.

## 6. Integrator conclusion

### Usable Windows evidence

The usable evidence is the clean commit provenance, hash-locked Python 3.9
installation, exact Chromium 148.0.7778.96/revision-1223 probe, passing 39-test
target suite, onefile and portable diagnostic build provenance, portable
two-build file manifests, clean CLI JSON success/failure behavior,
Unicode/spaces conversion, embedded-browser empty-cache behavior, witnessed
GUI conversion/preview/normal cleanup, CLI and GUI operation under firewall
default deny, onefile CLI and GUI operation in a no-Python/no-adapter disposable
Windows Sandbox, PDF/raster inventories, same-definition Defender observations,
simulated-MOTW warning behavior, and measured CLI-start/conversion comparisons.

### Remaining blockers

The integrator still lacks a windowed release candidate with a tested CLI
access strategy, portable execution repeated in the no-Python Sandbox,
controlled portable GUI cold/warm startup timing, real-download/signing
reputation evidence, approved visual goldens and cross-OS pairs, and production
enforcement of the probed ADR-004 browser policy. Portable byte reproducibility
also failed for two generated files. A packet capture or separate physical
clean host remains optional strengthening evidence if the integrator requires
more than the no-adapter Sandbox. The shared low-height layout defect needs
triage. Elevated drag-and-drop failure is attributable to the measured Windows
integrity-level boundary; the standard-user path passed. These are visible
non-passes; none is implied by successful builds.

### Distribution recommendation

Prefer the portable-directory candidate for the next integration step. The
onefile warm GUI observations already exceed ADR-007's absolute two-second
criterion; its measured CLI-start median is about four times the portable's,
its conversion median is about 3.5 times the portable's, it performs a
432,547,031-byte temporary extraction, and its simulated-MOTW launch produced
the stronger purple SmartScreen warning. The portable ZIP costs only 834,997
additional bytes (about 0.47%) in this build and passed the measured functional,
empty-cache, Unicode-path, firewall-offline, and Defender checks. This is a
factual candidate recommendation, not an official-format declaration: the
integrator must still resolve the blockers above before release selection.

## 7. Native visual-archive follow-ups

Two later visual archives supplement section 3 without changing its packaging
claims. The first variable-font archive is recorded in the renderer report and
failed cross-OS because the operating systems instantiated its weights
differently.

The second archive,
`LibreMark G1 Windows visual static 93fbf83.zip`, is 1,630,905 bytes with
SHA-256
`53e96d0ab0fa7288475c882b293f2102dc6644359a6f0d104722a33a96e4c62a`.
Its `Run` command exited 0 from clean commit
`93fbf83404339999064e7b09b18399ea9dfb4606`. It records Windows 11 Pro x64
build 26200, CPython 3.9.13, Playwright 1.60.0, Pillow 11.3.0, PDFium 5.11.0,
Chromium 148.0.7778.96 revision 1223, the static manifest SHA-256
`a6c3529fd009c36f44400642d5eadd1be1aad9b729875054be7a4c7f2805f031`,
and all seven custom faces. All 18 payload hashes validate. Candidate evidence
SHA-256 is
`1c6dd786ba47ce18bc78100046065390aeeca14584128352df158af9c40e11fb`;
repeat-comparison SHA-256 is
`be4753ee3ec162523f0e21c75a3f26dd71f935c172c4d276a6d7468a46140ac3`.

The owner confirmed that the Realtek physical adapter was disconnected for the
whole Run, DNS resolution of `example.com` failed, and TCP 443 was unavailable.
Only local Hyper-V and VirtualBox adapters remained active. The probe recorded
no attempted or completed network requests. The Windows repeat passed with
SSIM 1.0, zero changed pixels/regions, and exact text, geometry, and
fingerprints on both pages.

Independent Linux integration reproduced the exact locked dependencies and
font/browser assets. The cross-OS comparator exited 1: page 1 changed 4.5371%
with SSIM 0.60230; page 2 changed 6.2990% with SSIM 0.46773. Extracted text
differed. Report SHA-256 is
`c5f7c72598485dd3dec447d9225bf886a43d2e010f955fe2015ffdb50cb6f4b8`.
Rerasterizing both PDFs with one Linux PDFium produced the same metrics, so the
failure is in Chromium's platform text layout, not archive rasterization.

A follow-up Linux spike with `--disable-font-subpixel-positioning` restored
exact Windows extracted-text hashes and page dimensions, with the retained diff
showing aligned layout. The remaining raster
differences are distributed around glyph edges, with largest regions only
0.01732% and 0.02224%. Because the retained Windows run did not record that
flag in its profile, this is diagnostic evidence rather than a gate pass. The
next dependency is an exact flagged Windows run, followed by the explicit
owner decision on ADR-002's one permitted antialiasing-threshold amendment.
