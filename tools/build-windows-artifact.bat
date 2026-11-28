@echo off
REM Build the Windows x64 portable-directory candidate.
REM
REM Prerequisites:
REM - standard CPython 3.14 x64 environment prepared from the hashed Windows lock;
REM - Playwright Chromium already staged under browser-win\;
REM - no dependency or browser download is performed by this script.
REM
REM Optional external output locations:
REM   set LIBREMARK_PDF_DISTPATH=C:\path\to\artifacts
REM   set LIBREMARK_PDF_WORKPATH=C:\path\to\build-work
REM
REM The output always contains:
REM - LibreMarkPDF.exe: authoritative windowed GUI;
REM - LibreMarkPDF-cli.exe: authoritative console CLI;
REM - LibreMarkPDF-debug.exe: GUI with an attached diagnostic console.

setlocal
cd /d "%~dp0\.."

echo === LibreMark PDF portable-directory build (Windows x64) ===
echo Building from: %cd%
echo(

if not defined LIBREMARK_PDF_PYTHON set "LIBREMARK_PDF_PYTHON=%cd%\.venv-windows-py314\Scripts\python.exe"
if not defined LIBREMARK_PDF_BROWSER_SOURCE set "LIBREMARK_PDF_BROWSER_SOURCE=%cd%\browser-win"
set "PLAYWRIGHT_BROWSERS_PATH=%LIBREMARK_PDF_BROWSER_SOURCE%"

"%LIBREMARK_PDF_PYTHON%" -c "import os, sys, sysconfig; raise SystemExit(not (sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 14) and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED') and (os.environ.get('PROCESSOR_ARCHITEW6432') or os.environ.get('PROCESSOR_ARCHITECTURE')) == 'AMD64'))"
if errorlevel 1 (
    echo [FAILED] This candidate build requires standard CPython 3.14 on native Windows x64.
    goto :error
)

"%LIBREMARK_PDF_PYTHON%" -m tools.verify_locked_environment --lock requirements\locks\windows-x64-py314.txt --check-browser
if errorlevel 1 (
    echo [FAILED] Prepare the hashed Windows lock first.
    goto :error
)

if not defined LIBREMARK_PDF_DISTPATH set "LIBREMARK_PDF_DISTPATH=%cd%\dist"
if not defined LIBREMARK_PDF_WORKPATH set "LIBREMARK_PDF_WORKPATH=%cd%\build"

set "LIBREMARK_PDF_MANUAL_SOURCE=%LIBREMARK_PDF_WORKPATH%\manual-pdfs"
"%LIBREMARK_PDF_PYTHON%" tools\stage_manual_pdfs.py --output-dir "%LIBREMARK_PDF_MANUAL_SOURCE%"
if errorlevel 1 (
    echo [FAILED] Localized manual PDF generation failed.
    goto :error
)

echo Distribution path: %LIBREMARK_PDF_DISTPATH%
echo Work path: %LIBREMARK_PDF_WORKPATH%
echo(

"%LIBREMARK_PDF_PYTHON%" -m PyInstaller --noconfirm --clean ^
    --distpath "%LIBREMARK_PDF_DISTPATH%" ^
    --workpath "%LIBREMARK_PDF_WORKPATH%" ^
    LibreMarkPDF.spec
if errorlevel 1 (
    echo [FAILED] PyInstaller portable-directory build failed.
    goto :error
)

if not exist "%LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF.exe" (
    echo [FAILED] Build completed without the expected portable executable.
    goto :error
)
if not exist "%LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF-cli.exe" (
    echo [FAILED] Build completed without the authoritative console CLI.
    goto :error
)
if not exist "%LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF-debug.exe" (
    echo [FAILED] Build completed without the diagnostic GUI executable.
    goto :error
)
set "PLAYWRIGHT_BROWSERS_PATH="
"%LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF-cli.exe" doctor --json
if errorlevel 1 (
    echo [FAILED] Frozen resource verification failed.
    goto :error
)

echo(
echo === Portable-directory build complete ===
echo Folder: %LIBREMARK_PDF_DISTPATH%\LibreMarkPDF
echo GUI: %LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF.exe
echo CLI: %LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF-cli.exe
echo Diagnostic GUI: %LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF-debug.exe
echo This is an unsigned candidate until the native release gates are complete.
endlocal
exit /b 0

:error
echo(
echo === Portable-directory build FAILED ===
endlocal
exit /b 1
