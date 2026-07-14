@echo off
REM build_portable.bat - builds the Windows portable-directory candidate.
REM
REM Prerequisites:
REM - CPython 3.9 x64 environment prepared from the hashed Windows lock;
REM - Playwright Chromium already staged under browsers\;
REM - no dependency or browser download is performed by this script.
REM
REM Optional external output locations:
REM   set LIBREMARK_PDF_DISTPATH=C:\path\to\artifacts
REM   set LIBREMARK_PDF_WORKPATH=C:\path\to\build-work
REM
REM Use --console for a diagnostic candidate with reliable CLI streams.

setlocal
cd /d "%~dp0"

echo === LibreMark PDF portable-directory build (Windows x64) ===
echo Building from: %cd%
echo(

set "LIBREMARK_PDF_CONSOLE=0"
if /i "%~1"=="--console" set "LIBREMARK_PDF_CONSOLE=1"
if not defined LIBREMARK_PDF_PYTHON set "LIBREMARK_PDF_PYTHON=python"

"%LIBREMARK_PDF_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 9) else 1)"
if errorlevel 1 (
    echo [FAILED] This candidate build requires CPython 3.9.
    goto :error
)

"%LIBREMARK_PDF_PYTHON%" -c "import PyInstaller; raise SystemExit(0 if PyInstaller.__version__ == '6.21.0' else 1)"
if errorlevel 1 (
    echo [FAILED] PyInstaller 6.21.0 is required. Prepare the hashed lock first.
    goto :error
)

if not exist "browsers\" (
    echo [FAILED] The locked Playwright browser payload is missing from browsers\.
    goto :error
)

where /r "%cd%\browsers" chrome-headless-shell.exe >nul 2>nul
if errorlevel 1 (
    echo [FAILED] chrome-headless-shell.exe was not found under browsers\.
    goto :error
)

if not defined LIBREMARK_PDF_DISTPATH set "LIBREMARK_PDF_DISTPATH=%cd%\dist"
if not defined LIBREMARK_PDF_WORKPATH set "LIBREMARK_PDF_WORKPATH=%cd%\build"

echo Distribution path: %LIBREMARK_PDF_DISTPATH%
echo Work path: %LIBREMARK_PDF_WORKPATH%
echo Console mode: %LIBREMARK_PDF_CONSOLE%
echo(

"%LIBREMARK_PDF_PYTHON%" -m PyInstaller --noconfirm --clean ^
    --distpath "%LIBREMARK_PDF_DISTPATH%" ^
    --workpath "%LIBREMARK_PDF_WORKPATH%" ^
    LibreMarkPDF-portable.spec
if errorlevel 1 (
    echo [FAILED] PyInstaller portable-directory build failed.
    goto :error
)

if not exist "%LIBREMARK_PDF_DISTPATH%\LibreMarkPDF\LibreMarkPDF.exe" (
    echo [FAILED] Build completed without the expected portable executable.
    goto :error
)

echo(
echo === Portable-directory build complete ===
echo Folder: %LIBREMARK_PDF_DISTPATH%\LibreMarkPDF
echo This is an unsigned candidate until the native release gates are complete.
endlocal
exit /b 0

:error
echo(
echo === Portable-directory build FAILED ===
endlocal
exit /b 1
