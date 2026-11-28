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
$Venv = Join-Path $RepoRoot ".venv-windows-py314"
$Lock = Join-Path $RepoRoot "requirements\locks\windows-x64-py314.txt"
$BrowserRoot = if ($env:LIBREMARK_PDF_BROWSER_SOURCE) {
    [IO.Path]::GetFullPath($env:LIBREMARK_PDF_BROWSER_SOURCE)
} else {
    Join-Path $RepoRoot "browser-win"
}
$PythonProbe = "import sys, sysconfig; raise SystemExit(not (sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 14) and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')))"

$NativeArchitecture = if ($env:PROCESSOR_ARCHITEW6432) {
    $env:PROCESSOR_ARCHITEW6432
} else {
    $env:PROCESSOR_ARCHITECTURE
}
if ($env:OS -ne "Windows_NT" -or $NativeArchitecture -ne "AMD64") {
    throw "bootstrap-windows.ps1 requires native Windows x64."
}

function Confirm-Install {
    param(
        [Parameter(Mandatory = $true)][string]$Purpose,
        [switch]$Requested
    )
    if ($Offline) { return $false }
    if ($Requested) { return $true }
    if ($NonInteractive -or -not [Environment]::UserInteractive) {
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
        $Id = if ($Tool -eq "python") { "Python.Python.3.14" } else { "GnuWin32.Make" }
        & winget install --exact --id $Id --accept-package-agreements --accept-source-agreements
    } elseif (Test-NativeCommand "choco") {
        $Package = if ($Tool -eq "python") { "python314" } else { "make" }
        & choco install $Package -y
    } elseif (Test-NativeCommand "scoop") {
        $Package = if ($Tool -eq "python") { "python314" } else { "make" }
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
    $PythonArguments = @("-3.14")
} else {
    $PythonArguments = @()
}
$PythonReady = $false
try {
    & $Python @PythonArguments -c $PythonProbe
    $PythonReady = ($LASTEXITCODE -eq 0)
} catch {
    $PythonReady = $false
}
if (-not $PythonReady -and
    [string]::IsNullOrWhiteSpace($PSBoundParameters["Python"]) -and
    (Confirm-Install -Purpose "standard CPython 3.14 x64" -Requested:$InstallPython)) {
    Install-RecommendedTool -Tool "python"
    foreach ($Candidate in @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"),
        (Join-Path $env:ProgramFiles "Python314\python.exe"),
        (Join-Path $env:USERPROFILE "scoop\apps\python314\current\python.exe")
    )) {
        if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
        & $Candidate -c $PythonProbe
        $PythonReady = ($LASTEXITCODE -eq 0)
        if ($PythonReady) {
            $Python = $Candidate
            $PythonArguments = @()
            break
        }
    }
}
if (-not $PythonReady) {
    throw "Standard CPython 3.14 x64 is required. Rerun with -InstallPython or pass -Python <path>."
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
& $VenvPython -c $PythonProbe
if ($LASTEXITCODE -ne 0) { throw "The environment at $Venv must use standard CPython 3.14 x64." }
if ($Offline) {
    & $VenvPython -m pip install --no-index --only-binary=:all: --require-hashes -r $Lock
} else {
    & $VenvPython -m pip install --only-binary=:all: --require-hashes -r $Lock
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
$env:PLAYWRIGHT_BROWSERS_PATH = $BrowserRoot
Push-Location -LiteralPath $RepoRoot
try {
    & $VenvPython -m tools.verify_locked_environment --lock $Lock --check-browser
    if ($LASTEXITCODE -ne 0) { throw "Locked environment verification failed." }
    & $VenvPython -m libremark_pdf doctor --json
    if ($LASTEXITCODE -ne 0) { throw "Resource verification failed." }
} finally {
    Pop-Location
}
Write-Host "Ready: $VenvPython"
if (Test-NativeCommand "make") {
    Write-Host "Next: make test"
} else {
    Write-Host "GNU Make is optional and is not currently on PATH."
    Write-Host "Install it with: .\bootstrap-windows.ps1 -InstallMake"
    Write-Host "You may need to reopen PowerShell after installation changes PATH."
}
