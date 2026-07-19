[CmdletBinding()]
param(
    [string]$Python = "",
    [switch]$Offline,
    [switch]$InstallPython,
    [switch]$InstallMake,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $RepoRoot ".venv-windows-py39"
$Lock = Join-Path $RepoRoot "requirements\locks\windows-x64-py39.txt"
$BrowserRoot = Join-Path $RepoRoot "browser-win"

if ($env:OS -ne "Windows_NT" -or -not [Environment]::Is64BitOperatingSystem) {
    throw "bootstrap-windows.ps1 requires native Windows x64."
}

function Confirm-Install {
    param(
        [Parameter(Mandatory = $true)][string]$Purpose,
        [switch]$Requested
    )
    if ($Requested) { return $true }
    if ($Offline -or $NonInteractive -or -not [Environment]::UserInteractive) {
        return $false
    }
    $Answer = Read-Host "$Purpose is missing. Install it now? [y/N]"
    return $Answer -match "^(?i:y|yes|o|oui)$"
}

function Test-NativeCommand {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { return $false }
    try {
        & $Name --version *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Install-RecommendedTool {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("python", "make")][string]$Tool
    )
    if (Test-NativeCommand "winget") {
        $Id = if ($Tool -eq "python") { "Python.Python.3.9" } else { "GnuWin32.Make" }
        & winget install --exact --id $Id --accept-package-agreements --accept-source-agreements
    } elseif (Test-NativeCommand "choco") {
        $Package = if ($Tool -eq "python") { "python39" } else { "make" }
        & choco install $Package -y
    } elseif (Test-NativeCommand "scoop") {
        $Package = if ($Tool -eq "python") { "python39" } else { "make" }
        & scoop install $Package
    } else {
        throw "No working supported package manager was found. Repair winget/App Installer or install the tool manually."
    }
    if ($LASTEXITCODE -ne 0) {
        throw "The package manager could not install $Tool."
    }
}

if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = "py"
    $PythonArguments = @("-3.9")
} else {
    $PythonArguments = @()
}
$PythonReady = $false
try {
    & $Python @PythonArguments -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)"
    $PythonReady = ($LASTEXITCODE -eq 0)
} catch {
    $PythonReady = $false
}
if (-not $PythonReady -and
    [string]::IsNullOrWhiteSpace($PSBoundParameters["Python"]) -and
    (Confirm-Install -Purpose "CPython 3.9 x64" -Requested:$InstallPython)) {
    Install-RecommendedTool -Tool "python"
    $Python = Join-Path $env:LOCALAPPDATA "Programs\Python\Python39\python.exe"
    $PythonArguments = @()
    if (Test-Path -LiteralPath $Python -PathType Leaf) {
        & $Python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)"
        $PythonReady = ($LASTEXITCODE -eq 0)
    }
}
if (-not $PythonReady) {
    throw "CPython 3.9 x64 is required. Rerun with -InstallPython, repair a supported package manager, or pass -Python <path>."
}
if (-not (Test-NativeCommand "make") -and
    (Confirm-Install -Purpose "GNU Make" -Requested:$InstallMake)) {
    Install-RecommendedTool -Tool "make"
}
if (-not (Test-Path -LiteralPath $Venv)) {
    & $Python @PythonArguments -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Virtual-environment creation failed." }
}
$VenvPython = Join-Path $Venv "Scripts\python.exe"
if ($Offline) {
    & $VenvPython -m pip install --no-index --require-hashes -r $Lock
} else {
    & $VenvPython -m pip install --require-hashes -r $Lock
}
if ($LASTEXITCODE -ne 0) { throw "Locked dependency installation failed." }
& $VenvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw "Installed dependencies are inconsistent." }
if ($Offline) {
    if (-not (Test-Path -LiteralPath $BrowserRoot)) {
        throw "Offline mode requires the staged Chromium payload in browser-win\."
    }
} else {
    $env:PLAYWRIGHT_BROWSERS_PATH = $BrowserRoot
    & $VenvPython -m playwright install --only-shell chromium
    if ($LASTEXITCODE -ne 0) { throw "Chromium acquisition failed." }
}
if (-not (Test-Path -LiteralPath (Join-Path $BrowserRoot "chromium_headless_shell-1223"))) {
    throw "The required Chromium headless-shell revision 1223 is missing."
}
$env:PLAYWRIGHT_BROWSERS_PATH = $BrowserRoot
& $VenvPython tools\verify_locked_environment.py --lock $Lock
& $VenvPython -m libremark_pdf doctor --json
Write-Host "Ready: $VenvPython"
if (Test-NativeCommand "make") {
    Write-Host "Next: make test"
} else {
    Write-Host "GNU Make is optional and is not currently on PATH."
    Write-Host "Install it with: .\bootstrap-windows.ps1 -InstallMake"
    Write-Host "You may need to reopen PowerShell after installation changes PATH."
}
