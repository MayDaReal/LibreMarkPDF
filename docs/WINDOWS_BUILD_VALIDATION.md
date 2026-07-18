# Windows x64 G3 candidate build and validation

This guide is the native Windows x64 acceptance procedure for the portable
LibreMark PDF G3 candidate. A successful build alone does not pass G3. The
candidate must also pass the automated artifact checks and the retained manual
GUI checklist.

The authoritative portable directory contains three entry paths:

- `LibreMarkPDF.exe`: GUI entry, without a console window;
- `LibreMarkPDF-cli.exe`: CLI entry with authoritative stdout, stderr, and
  process status;
- `LibreMarkPDF-debug.exe`: diagnostic GUI entry with a console.

Distribute and test the complete `LibreMarkPDF` directory. Copying an
executable without its `_internal` directory is not a valid candidate.

The one-file build remains a development convenience. It is not the
authoritative G3 Windows artifact.

## Scope and gate boundary

This procedure covers Windows x64 G3 only. It does not start macOS, Linux
distribution, publication, release upload, credential, or signing work.

The independent G2 PDFium `23-unicode` limitation remains open. Record its
canonical comparison result in the G3 evidence, but do not alter G2 evidence or
claim G2 closure. Windows G3 is evaluated from the native candidate evidence.

## Native build prerequisites

Use a clean native Windows x64 checkout at the exact signed commit being
evaluated. Run from a normal, non-administrative PowerShell session.

Prepare CPython 3.9 and the hash-locked dependency environment:

```powershell
py -3.9 -m venv venv
venv\Scripts\python.exe -m pip install --require-hashes `
  -r requirements\locks\windows-x64-py39.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\browsers"
venv\Scripts\python.exe -m playwright install --only-shell chromium
```

The last command is an acquisition step and requires network access. Complete
it before the disconnected-runtime test. It must stage the Playwright 1.60.0
Chromium headless-shell payload: Chromium `148.0.7778.96`, revision `1223`.
Runtime conversion must use that bundled payload and must never download a
browser.

Before disconnecting, verify:

```powershell
venv\Scripts\python.exe -m pip check
venv\Scripts\python.exe -m libremark_pdf --version
venv\Scripts\python.exe -m libremark_pdf doctor --json
git status --short --branch
git rev-parse HEAD
git log -1 --show-signature
```

Do not continue if the checkout has unrelated changes, the architecture is not
AMD64, the dependency lock is not satisfied, or the browser identity differs.

## Automated candidate run

Choose an evidence directory outside the checkout whose path contains both
Unicode and spaces. Physically disconnect all network adapters before passing
`-RequireOffline`; invalid proxy settings alone are not sufficient evidence.

```powershell
$evidence = "C:\G3 Evidence\LibreMark PDF – Windows x64"
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\run_g3_windows_candidate.ps1 `
  -EvidenceRoot $evidence `
  -Python "$PWD\venv\Scripts\python.exe" `
  -RequireOffline
```

The runner performs the following without elevation:

- records the signed source identity, clean status, Windows build, AMD64
  architecture, Python and locked dependency identities;
- runs the complete `unittest` suite;
- builds the portable onedir candidate with `build_portable.bat`;
- copies the complete candidate to an external Unicode-and-space path;
- uses an isolated empty user profile and a `PATH` without Python;
- verifies CLI JSON success, validation error, partial batch, collision,
  theme selection, and a temporary permission-denied destination;
- records the physically disconnected network state;
- starts the GUI and diagnostic entries and retains their startup observations;
- runs the canonical artifact comparison without updating expected data;
- creates an SPDX JSON SBOM, dependency/font/theme notices, logs, checksums,
  candidate ZIP, and an evidence archive;
- records Authenticode and antivirus observations without configuring signing.

The runner restores the process environment and any temporary access-control
entry it creates. It never installs system software, changes machine policy,
configures credentials, signs, uploads, publishes, or pushes.

If a normal user cannot apply the temporary denial rule, record that failed
experiment and perform the permission check in a user-owned directory. Do not
elevate merely to force that check.

## Retained manual GUI checklist

Automation cannot establish visual quality, keyboard order, assistive labels,
contrast, or high-DPI usability. Complete the generated
`manual-gui-checklist.md` against the exact copied candidate and record the
tester, Windows scaling, display resolution, locale, and time.

The checklist must demonstrate all of the following:

- `LibreMarkPDF.exe` starts without a console, with and without
  `tkinterdnd2` available in the build environment;
- EN and FR labels and statuses are complete and idiomatic;
- keyboard traversal reaches every interactive control with visible focus;
- the interface remains usable at 100%, 150%, and 200% Windows scaling;
- preview is responsive, scrollable, and zoomable;
- rapid preview requests discard stale results;
- conversion progress is visible, cancellation is safe, and closing during
  work does not call Tk from a worker;
- incompatible actions are disabled while work is active;
- overwrite and collision choices appear before conversion;
- open-PDF and open-folder actions appear only after a successful conversion;
- batch processing continues after an independent failure;
- the selected local theme is visible in preview and conversion;
- the default theme remains visually compatible with the approved default;
- no browser download, network request, unexpected console, or traceback is
  observed.

Retain screenshots or recordings for the language states, preview zoom,
collision prompt, progress/cancellation, successful actions, and high-DPI
checks. Do not replace reviewed golden files as a normal test side effect.

## Candidate inspection

The evidence directory must contain:

- complete command transcripts with exact exit codes;
- source, lock, browser, render-profile, font, theme, fixture, and expected-data
  hashes;
- Windows edition/build and architecture;
- external candidate path and isolated profile path;
- disconnected adapter observations;
- CLI JSON outputs and stderr captures;
- GUI startup and manual checklist evidence;
- canonical comparison reports and retained visual diffs;
- `LibreMarkPDF-windows-x64-unsigned.zip`, its byte size and SHA-256;
- SPDX SBOM and third-party/font/theme notices;
- Authenticode status and antivirus observations;
- every warning, failed experiment, limitation, and unverified item;
- the evidence archive and its SHA-256.

Inspect the candidate entry paths explicitly:

```powershell
Get-ChildItem "$evidence\candidate-external\LibreMarkPDF*.exe" |
  Select-Object Name, Length, LastWriteTime
Get-AuthenticodeSignature `
  "$evidence\candidate-external\LibreMarkPDF.exe",
  "$evidence\candidate-external\LibreMarkPDF-cli.exe",
  "$evidence\candidate-external\LibreMarkPDF-debug.exe"
Get-FileHash "$evidence\LibreMarkPDF-windows-x64-unsigned.zip" -Algorithm SHA256
```

When no approved signing identity exists, the accurate label is **unsigned
Windows candidate**. Do not request, display, configure, or use signing
secrets.

## Acceptance

Use:

`WINDOWS G3 PASSED — pending separate G2 closure for release progression`

only when every mandatory Windows G3 criterion has reproducible native evidence
and the manual checklist is complete.

Otherwise use:

`WINDOWS G3 NOT YET PASSED`

and list each remaining item with its owner, exact command or human decision,
and whether it is a G3 blocker or the separate known G2 blocker.

The Windows candidate must not be published, uploaded, tagged as a release, or
represented as official under this procedure.
