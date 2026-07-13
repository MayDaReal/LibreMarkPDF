@echo off
REM build.bat - builds a standalone LibreMarkPDF.exe for Windows.
REM
REM Run this once on your Windows machine. Requires Python 3.9+ installed
REM with "Add python.exe to PATH" checked.
REM
REM IMPORTANT: run this from a normal local folder (e.g. C:\Users\you\libremark-pdf
REM or your Desktop) - NOT from a VirtualBox/VMware shared folder or a network
REM drive. Those commonly cause "Access denied" errors with pip/venv because
REM they don't fully support the file locking/symlink operations Python
REM packaging tools rely on.
REM
REM Usage: double-click build.bat, or run it from a command prompt.
REM For a diagnostic build with startup tracebacks: build.bat --console

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === LibreMark PDF build (Windows) ===
echo Building in: %cd%
echo(

set "LIBREMARK_PDF_CONSOLE=0"
if /i "%~1"=="--console" set "LIBREMARK_PDF_CONSOLE=1"

echo --- Creating virtual environment ---
where py >nul 2>nul
if errorlevel 1 (
    python -m venv --clear venv
) else (
    py -3 -m venv --clear venv
)
if errorlevel 1 (
    echo(
    echo [FAILED] Could not create the virtual environment.
    echo Check that Python is installed and on PATH ^(try: python --version^).
    goto :error
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo(
    echo [FAILED] Could not activate the virtual environment.
    goto :error
)

echo --- Installing Python dependencies ---
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo(
    echo [FAILED] pip install failed - see the error above.
    echo If you see "Access denied" or similar permission errors and this
    echo folder is on a shared/network/VM drive, copy the whole "libremark-pdf"
    echo folder to a local path first ^(e.g. C:\Users\%USERNAME%\libremark-pdf^)
    echo and run build.bat again from there.
    goto :error
)

echo --- Downloading Chromium (bundled, local copy) ---
set PLAYWRIGHT_BROWSERS_PATH=%cd%\browsers
python -m playwright install chromium
if errorlevel 1 (
    echo(
    echo [FAILED] Could not download Chromium via Playwright - see the error above.
    echo This step needs internet access ^(and no restrictive proxy/firewall^).
    goto :error
)

echo --- Building the executable with PyInstaller ---
python -m PyInstaller --noconfirm --clean LibreMarkPDF.spec
if errorlevel 1 (
    echo(
    echo [FAILED] PyInstaller build failed - see the error above.
    goto :error
)

if not exist "dist\LibreMarkPDF.exe" (
    echo(
    echo [FAILED] Build finished but dist\LibreMarkPDF.exe was not created.
    goto :error
)

echo(
echo === Build complete ===
echo Executable: dist\LibreMarkPDF.exe
echo Double-click it to launch LibreMark PDF - no further installation needed.
endlocal
pause
exit /b 0

:error
echo(
echo === Build FAILED - see the message above for what to fix ===
endlocal
pause
exit /b 1
