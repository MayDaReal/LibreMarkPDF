# Windows standalone build validation

Use this checklist as the release acceptance record for `dist\LibreMarkPDF.exe`.
Complete it on the Windows computer where the executable will be used. Check a
box only after observing the stated result. Record failures verbatim instead of
marking them as passed.

## Validation record

- Tester: ______________________________
- Date and time: ________________________
- Git commit or source archive identifier: ______________________________
- Windows edition: ______________________
- Windows version/build (`winver`): ______________________
- CPU architecture (`AMD64`, `ARM64`, or other): ______________________
- Build location: ______________________________
- Antivirus/security product: ______________________________
- Network state during offline tests: ______________________________
- Notes about VM, network drive, or managed workstation: ______________________________

## Known pre-validation evidence

The following results were observed on July 12, 2026 before this manual
acceptance pass. They are evidence about that specific environment, not a
substitute for the manual checks below.

- Windows platform reported by PyInstaller: `Windows-10-10.0.26200-SP0`,
  `AMD64`.
- Build Python: CPython 3.11.0 from
  `C:\Users\Utilisateur\AppData\Local\Programs\Python\Python311`.
- The previous broken environment used the Microsoft Store alias and Python
  3.11.9; Playwright subprocess creation failed there with `WinError 998`.
- Dependency versions: Playwright 1.61.0, pypdfium2 5.11.0, Pillow 12.3.0,
  tkinterdnd2 0.6.2, and PyInstaller 6.21.0.
- Playwright 1.61.0 expects Chromium revision 1228. The bundled browser tree
  contained revision 1228, installation markers, and `chrome.exe`.
- `build.bat` completed successfully from a recreated virtual environment and
  used `LibreMarkPDF.spec`.
- `python -m unittest discover -s tests -v` passed all 21 tests, including PDF
  generation and PNG preview rendering.
- The final executable size was 373,231,113 bytes (approximately 356 MiB).
- An external-path CLI test with an empty user profile and invalid HTTP proxy
  settings returned exit code 0, emitted valid JSON with no stderr output, and
  created a 130,887-byte PDF beginning with `%PDF-`.
- Manual GUI startup and interaction still require confirmation below. The
  automated window-discovery attempt was inconclusive and is not recorded as a
  pass.

## 1. Clean release build

- [ ] Close every running LibreMark PDF window and command prompt using its venv.
- [ ] Open a normal `cmd.exe` in the repository root.
- [ ] Run `build.bat`.
- [ ] Confirm the command ends with `=== Build complete ===` and no
  `[FAILED]` message.
- [ ] Confirm `dist\LibreMarkPDF.exe` exists and is larger than 300 MB.

Observed executable size: __________________ bytes

If this section fails, attach the complete console output. Also record whether
the repository is on a local disk, network share, synchronized folder, or VM
shared folder.

## 2. Automated regression suite

From the repository root, run:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

- [ ] Every test reports `ok`.
- [ ] The final summary reports `OK` with no failures or errors.
- [ ] The preview test
  `test_render_preview_png_returns_valid_png_bytes` passes.
- [ ] The PDF test
  `test_convert_markdown_text_to_pdf_creates_a_file` passes.

Observed test count: __________  Duration: __________

## 3. GUI startup in the repository

- [ ] Double-click `dist\LibreMarkPDF.exe` without activating the venv.
- [ ] A LibreMark PDF window opens and remains open.
- [ ] The logo, file drop area, CSS row, header/footer section, preview area,
  output row, and Generate button are visible.
- [ ] Switching between `EN` and `FR` updates the visible labels.
- [ ] Close and reopen the application; it opens normally again.

Expected result: no console window, traceback, missing-module dialog, or silent
exit.

## 4. GUI preview

- [ ] Open `dist\LibreMarkPDF.exe` without arguments.
- [ ] Without adding a file, click **Refresh preview**.
- [ ] The status changes to **Rendering preview...** (or the French
  equivalent).
- [ ] A page thumbnail appears in the preview area.
- [ ] The status returns to **Ready.** (or **Prêt.**) without an error.
- [ ] Add `README.md`, click **Refresh preview** again, and confirm that the
  preview changes to the README content.

Expected result: a visible, non-empty PNG thumbnail of page 1. A successful PDF
generation alone does not pass this section.

## 5. CLI conversion in the repository

Delete or move any previous `README.pdf`, then run from the repository root:

```powershell
dist\LibreMarkPDF.exe convert README.md --json
echo $LASTEXITCODE
```

- [ ] Standard output contains one JSON object and no other text.
- [ ] The JSON contains `"status": "ok"` and `"error": null`.
- [ ] `$LASTEXITCODE` is `0`.
- [ ] `README.pdf` exists and is not empty.
- [ ] The PDF opens in a PDF viewer and displays the README content correctly.
- [ ] Page numbers are visible in the default footer.

Observed PDF size: __________________ bytes

## 6. External path containing spaces

Create a directory outside the repository, for example:

```powershell
$testDir = "$env:USERPROFILE\Desktop\LibreMark PDF Offline Test"
New-Item -ItemType Directory -Force $testDir
Copy-Item dist\LibreMarkPDF.exe, README.md $testDir
Set-Location $testDir
```

- [ ] Confirm the test directory path contains at least one space.
- [ ] Confirm no `venv`, `browsers`, `style.css`, `icons`, or `assets` folder
  was copied beside the executable.
- [ ] Double-click the copied `LibreMarkPDF.exe`; the GUI opens correctly.
- [ ] Refresh the sample preview; a thumbnail appears without error.
- [ ] Run `LibreMarkPDF.exe convert README.md --json` in that directory.
- [ ] The command returns exit code 0 and valid JSON only.
- [ ] The generated `README.pdf` is non-empty and opens correctly.

External test path: ______________________________

## 7. No Python and no active virtual environment

Open a new `cmd.exe` or PowerShell window. Do not run an activation script.

- [ ] `VIRTUAL_ENV` is empty or undefined.
- [ ] Temporarily rename `python.exe`/`py.exe` on `PATH`, or perform this test
  on a Windows account/computer without Python installed.
- [ ] From the external test directory, the GUI still opens.
- [ ] The CLI conversion still returns exit code 0 and creates a valid PDF.
- [ ] The GUI preview still renders.

How Python was made unavailable: ______________________________

## 8. Empty Playwright cache

Playwright normally uses `%LOCALAPPDATA%\ms-playwright`. Preserve user data by
renaming the directory instead of deleting it:

```powershell
$cache = "$env:LOCALAPPDATA\ms-playwright"
if (Test-Path $cache) { Rename-Item $cache "$cache.disabled" }
```

Run the external GUI preview and CLI conversion again.

- [ ] GUI startup succeeds with the user Playwright cache unavailable.
- [ ] Preview generation succeeds.
- [ ] CLI conversion succeeds with exit code 0.
- [ ] No new browser download is requested or started.
- [ ] No new `%LOCALAPPDATA%\ms-playwright` browser cache is required for the
  conversion.

Restore the original cache after the test if one was renamed.

## 9. Offline runtime

Disconnect Wi-Fi/Ethernet or use a firewall rule that blocks network access for
the copied `LibreMarkPDF.exe`. Merely setting a proxy is useful supporting
evidence but is not equivalent to disconnecting the network.

- [ ] Windows reports that the test computer is offline, or the firewall rule
  is recorded below.
- [ ] The external GUI opens while offline.
- [ ] The sample and README previews render while offline.
- [ ] The external CLI conversion returns exit code 0 while offline.
- [ ] The PDF opens and contains the expected styled content and page footer.
- [ ] No download prompt, network error, or long network timeout occurs.

Offline method or firewall rule: ______________________________

## 10. Diagnostic build path

This validates that startup failures can be investigated reproducibly.

```powershell
build.bat --console
dist\LibreMarkPDF.exe
```

- [ ] The diagnostic build completes successfully.
- [ ] A console remains attached when the GUI starts.
- [ ] Python/PyInstaller startup errors would be visible in that console.
- [ ] Run plain `build.bat` again and confirm the release build is windowed.

## Final acceptance

- [ ] Sections 1 through 10 all pass.
- [ ] Every failure encountered during testing is recorded below with the exact
  command, exit code, complete error, and affected environment.
- [ ] `dist\LibreMarkPDF.exe` is accepted as a standalone Windows release.

Final result: **PASS / FAIL** (circle one)

Tester signature: ______________________________

## Failure record

For each failure, copy and complete this block:

```text
Section/check:
Date and time:
Exact command or GUI action:
Exit code:
Complete stdout:
Complete stderr/traceback:
Windows version/build:
Test path:
Network state:
Python/venv state:
Playwright cache state:
Antivirus/security event:
Reproducible after reboot: yes/no/not tested
```
