[CmdletBinding()]
param(
    [string]$EvidenceRoot = "",

    [string]$Python = "",

    [switch]$RequireOffline
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = Join-Path $RepoRoot ".venv-windows-py39\Scripts\python.exe"
}
if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
    $Version = (Get-Content -LiteralPath (Join-Path $RepoRoot "VERSION") -Raw).Trim()
    $EvidenceRoot = Join-Path $RepoRoot "dist\$Version\windows-x64"
}
if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    throw "This evidence harness must run on native Windows."
}
$NativeArchitecture = if ([string]::IsNullOrWhiteSpace($env:PROCESSOR_ARCHITEW6432)) {
    $env:PROCESSOR_ARCHITECTURE
} else {
    $env:PROCESSOR_ARCHITEW6432
}
if (-not [Environment]::Is64BitOperatingSystem -or $NativeArchitecture -ne "AMD64") {
    throw "The mandatory candidate lane requires native Windows x64 (AMD64)."
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "The locked CPython 3.9 executable is unavailable: $Python"
}

$EvidenceRoot = [IO.Path]::GetFullPath($EvidenceRoot)
if ($EvidenceRoot.StartsWith($RepoRoot, [StringComparison]::OrdinalIgnoreCase) -and
    -not $EvidenceRoot.StartsWith((Join-Path $RepoRoot "dist"), [StringComparison]::OrdinalIgnoreCase)) {
    throw "EvidenceRoot must be outside the repository or under dist\."
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$LogDir = New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot "logs")
$ArtifactDir = New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot "artifacts")
$WorkDir = New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot "build-work")
$RuntimeDir = New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceRoot "runtime")
$Transcript = Join-Path $LogDir "windows-validation-transcript.txt"
$Started = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$OldEnvironment = $null

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Arguments = @(),
        [int[]]$AllowedExitCodes = @(0)
    )
    Write-Host ("> " + $File + " " + ($Arguments -join " "))
    & $File @Arguments
    $Code = $LASTEXITCODE
    Write-Host ("exit=" + $Code)
    if ($AllowedExitCodes -notcontains $Code) {
        throw "Command failed with exit $Code`: $File"
    }
    return $Code
}

function Invoke-CliCase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][int]$ExpectedExit
    )
    $StdoutPath = Join-Path $LogDir ($Name + ".stdout.json")
    $StderrPath = Join-Path $LogDir ($Name + ".stderr.txt")
    $Output = & $script:CliPath @Arguments 2> $StderrPath | Out-String
    $Code = $LASTEXITCODE
    [IO.File]::WriteAllText($StdoutPath, $Output, [Text.UTF8Encoding]::new($false))
    Write-Host ("CLI " + $Name + " exit=" + $Code)
    if ($Code -ne $ExpectedExit) {
        throw "CLI case $Name returned $Code; expected $ExpectedExit"
    }
    if ((Get-Item -LiteralPath $StderrPath).Length -ne 0) {
        throw "CLI case $Name emitted unexpected stderr."
    }
    try {
        return $Output | ConvertFrom-Json
    } catch {
        throw "CLI case $Name did not emit one valid JSON document."
    }
}

Set-Location $RepoRoot
Start-Transcript -LiteralPath $Transcript -Force | Out-Null
try {
    $StatusBefore = & git status --short --branch
    $PorcelainBefore = & git status --porcelain
    $Commit = (& git rev-parse HEAD).Trim()
    $Signature = & git log -1 --show-signature
    $StatusBefore | Set-Content -LiteralPath (Join-Path $LogDir "git-status-before.txt") -Encoding UTF8
    $Signature | Set-Content -LiteralPath (Join-Path $LogDir "git-signature.txt") -Encoding UTF8
    if ($PorcelainBefore) {
        throw "The native candidate checkout must be clean before building."
    }

    $Computer = Get-ComputerInfo | Select-Object WindowsProductName, WindowsEditionId,
        WindowsVersion, OsBuildNumber, OsArchitecture, CsSystemType
    $Computer | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "windows-environment.json"
    ) -Encoding UTF8
    [ordered]@{
        PROCESSOR_ARCHITECTURE = $env:PROCESSOR_ARCHITECTURE
        PROCESSOR_ARCHITEW6432 = $env:PROCESSOR_ARCHITEW6432
        native_architecture = $NativeArchitecture
        Is64BitProcess = [Environment]::Is64BitProcess
        Is64BitOperatingSystem = [Environment]::Is64BitOperatingSystem
        started_utc = $Started
    } | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "architecture.json"
    ) -Encoding UTF8

    Invoke-Native $Python @("--version")
    $VersionProbe = & $Python -c "import platform,sys; print(platform.platform()); print(sys.version); raise SystemExit(0 if sys.version_info[:2] == (3,9) else 1)"
    if ($LASTEXITCODE -ne 0) { throw "CPython 3.9 is mandatory." }
    $VersionProbe | Set-Content -LiteralPath (Join-Path $LogDir "python.txt") -Encoding UTF8
    Invoke-Native $Python @("-m", "pip", "freeze")
    Invoke-Native $Python @("-m", "libremark_pdf", "--version")
    Invoke-Native $Python @("-m", "libremark_pdf", "doctor", "--json")

    $HashInputs = @(
        "requirements\locks\windows-x64-py39.txt",
        "style.css",
        "tests\fixtures\canonical\manifest.json",
        "tests\goldens\canonical\expected.json",
        "tests\fixtures\themes\community-blue\theme.json"
    )
    $HashInputs += Get-ChildItem -LiteralPath (Join-Path $RepoRoot "fonts") -File |
        ForEach-Object { $_.FullName }
    $HashInputs += Get-ChildItem -LiteralPath (Join-Path $RepoRoot "icons") -File |
        ForEach-Object { $_.FullName }
    $HashInputs | ForEach-Object {
        $Resolved = Resolve-Path -LiteralPath $_
        $Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $Resolved
        [PSCustomObject]@{ path = $Resolved.Path; sha256 = $Hash.Hash.ToLowerInvariant() }
    } | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "source-input-hashes.json"
    ) -Encoding UTF8

    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $RepoRoot "browser-win"
    Invoke-Native $Python @("-m", "unittest", "discover", "-s", "tests", "-v")

    $env:LIBREMARK_PDF_DISTPATH = $ArtifactDir.FullName
    $env:LIBREMARK_PDF_WORKPATH = $WorkDir.FullName
    $env:LIBREMARK_PDF_PYTHON = $Python
    Invoke-Native (Join-Path $RepoRoot "tools\build-windows-artifact.bat")

    $Candidate = Join-Path $ArtifactDir "LibreMarkPDF"
    $GuiPath = Join-Path $Candidate "LibreMarkPDF.exe"
    $script:CliPath = Join-Path $Candidate "LibreMarkPDF-cli.exe"
    $DebugPath = Join-Path $Candidate "LibreMarkPDF-debug.exe"
    foreach ($Path in @($GuiPath, $script:CliPath, $DebugPath)) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            throw "Candidate entry point is missing: $Path"
        }
    }
    foreach ($Manual in @("MANUAL_EN.pdf", "MANUEL_FR.pdf")) {
        $ManualPath = Join-Path $Candidate "_internal\docs\$Manual"
        if (-not (Test-Path -LiteralPath $ManualPath -PathType Leaf) -or
            (Get-Item -LiteralPath $ManualPath).Length -eq 0) {
            throw "Packaged localized manual is missing or empty: $ManualPath"
        }
    }
    if (Test-Path -LiteralPath (Join-Path $Candidate "_internal\browsers\.links")) {
        throw "Playwright source-link metadata must not enter the candidate."
    }

    # Windows PowerShell 5.1 may decode a UTF-8 script without a BOM through the
    # active ANSI code page. Build the non-ASCII test character explicitly so
    # this remains a genuine Unicode-path probe on every supported host.
    $EAcute = [char]0x00E9
    $ExternalRoot = Join-Path $RuntimeDir ("LibreMark PDF validation " + $EAcute + "preuve")
    $ExternalCandidate = Join-Path $ExternalRoot "LibreMarkPDF"
    New-Item -ItemType Directory -Force -Path $ExternalRoot | Out-Null
    Copy-Item -LiteralPath $Candidate -Destination $ExternalCandidate -Recurse
    $GuiPath = Join-Path $ExternalCandidate "LibreMarkPDF.exe"
    $script:CliPath = Join-Path $ExternalCandidate "LibreMarkPDF-cli.exe"
    $DebugPath = Join-Path $ExternalCandidate "LibreMarkPDF-debug.exe"

    $IsolatedProfile = New-Item -ItemType Directory -Force -Path (
        Join-Path $RuntimeDir "empty-profile"
    )
    $IsolatedCache = New-Item -ItemType Directory -Force -Path (
        Join-Path $RuntimeDir "empty-localappdata"
    )
    $OldEnvironment = [ordered]@{
        PATH = $env:PATH
        USERPROFILE = $env:USERPROFILE
        HOME = $env:HOME
        LOCALAPPDATA = $env:LOCALAPPDATA
        VIRTUAL_ENV = $env:VIRTUAL_ENV
        PLAYWRIGHT_BROWSERS_PATH = $env:PLAYWRIGHT_BROWSERS_PATH
    }
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    $env:USERPROFILE = $IsolatedProfile.FullName
    $env:HOME = $IsolatedProfile.FullName
    $env:LOCALAPPDATA = $IsolatedCache.FullName
    $env:VIRTUAL_ENV = $null
    $env:PLAYWRIGHT_BROWSERS_PATH = $null
    if (Get-Command python -ErrorAction SilentlyContinue) {
        throw "The isolated artifact runtime still resolves Python on PATH."
    }

    $NetworkBefore = Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
        Select-Object Name, InterfaceDescription, Status, LinkSpeed
    $NetworkBefore | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "network-state-before-runtime.json"
    ) -Encoding UTF8
    $OnlineBefore = @($NetworkBefore | Where-Object Status -eq "Up")
    if ($RequireOffline -and $OnlineBefore.Count -ne 0) {
        throw "RequireOffline was selected but a physical network adapter is up before runtime tests."
    }

    $Input = Join-Path $ExternalRoot ("rapport " + $EAcute + " avec espace.md")
    $Image = Join-Path $ExternalRoot "blue-square.svg"
    Copy-Item -LiteralPath (
        Join-Path $RepoRoot "tests\fixtures\canonical\resources\blue-square.svg"
    ) -Destination $Image
    ("# Rapport " + $EAcute + "`n`n![Blue](blue-square.svg)`n") |
        Set-Content -LiteralPath $Input -Encoding UTF8
    $Output = Join-Path $ExternalRoot ("rapport " + $EAcute + " avec espace.pdf")
    $SuccessTimer = [Diagnostics.Stopwatch]::StartNew()
    $Success = Invoke-CliCase "success" @(
        "convert", $Input, "--output", $Output, "--date", "2026-07-14", "--json"
    ) 0
    $SuccessTimer.Stop()
    if ($Success.status -ne "ok" -or -not (Test-Path -LiteralPath $Output)) {
        throw "External Unicode-and-space success case failed."
    }
    $Missing = Invoke-CliCase "missing" @(
        "convert", (Join-Path $ExternalRoot "missing.md"), "--json"
    ) 1
    if ($Missing.error_code -ne "INPUT_NOT_FOUND") {
        throw "Missing-input error code changed."
    }

    $PartialDir = New-Item -ItemType Directory -Force -Path (
        Join-Path $ExternalRoot "partial outputs"
    )
    $Partial = Invoke-CliCase "partial-batch" @(
        "convert", $Input, (Join-Path $ExternalRoot "missing.md"),
        "--out-dir", $PartialDir.FullName, "--date", "2026-07-14", "--json"
    ) 1
    if ($Partial.results.Count -ne 2 -or $Partial.results[0].status -ne "ok" -or
        $Partial.results[1].error_code -ne "INPUT_NOT_FOUND") {
        throw "Partial batch did not preserve one result per input."
    }

    $DuplicateOne = New-Item -ItemType Directory -Force -Path (
        Join-Path $ExternalRoot "duplicate one"
    )
    $DuplicateTwo = New-Item -ItemType Directory -Force -Path (
        Join-Path $ExternalRoot "duplicate two"
    )
    Copy-Item -LiteralPath $Input -Destination (Join-Path $DuplicateOne "same.md")
    Copy-Item -LiteralPath $Input -Destination (Join-Path $DuplicateTwo "same.md")
    $Collision = Invoke-CliCase "collision" @(
        "convert", (Join-Path $DuplicateOne "same.md"),
        (Join-Path $DuplicateTwo "same.md"),
        "--out-dir", (Join-Path $ExternalRoot "collision output"), "--json"
    ) 1
    if (($Collision.results | Where-Object error_code -eq "DUPLICATE_OUTPUT").Count -ne 2) {
        throw "Duplicate-output collision contract changed."
    }

    $ThemePackage = Join-Path $ExternalRoot "community theme"
    Copy-Item -LiteralPath (
        Join-Path $RepoRoot "tests\fixtures\themes\community-blue"
    ) -Destination $ThemePackage -Recurse
    $InstalledTheme = Invoke-CliCase "theme-install" @(
        "theme", "install", $ThemePackage, "--json"
    ) 0
    if ($InstalledTheme.reference -ne "community-blue@1") {
        throw "Theme installation identity changed."
    }
    $ThemeOutput = Join-Path $ExternalRoot "theme output.pdf"
    $ThemeResult = Invoke-CliCase "theme-convert" @(
        "convert", $Input, "--output", $ThemeOutput,
        "--theme", "community-blue@1", "--date", "2026-07-14", "--json"
    ) 0
    if ($ThemeResult.theme -ne "community-blue@1") {
        throw "Theme selection was not reported."
    }

    $PermissionDir = New-Item -ItemType Directory -Force -Path (
        Join-Path $ExternalRoot "permission denied"
    )
    $OriginalAcl = Get-Acl -LiteralPath $PermissionDir
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $DenyRule = [Security.AccessControl.FileSystemAccessRule]::new(
        $Identity,
        [Security.AccessControl.FileSystemRights]::CreateFiles,
        [Security.AccessControl.InheritanceFlags]"ContainerInherit,ObjectInherit",
        [Security.AccessControl.PropagationFlags]::None,
        [Security.AccessControl.AccessControlType]::Deny
    )
    try {
        $DeniedAcl = Get-Acl -LiteralPath $PermissionDir
        [void]$DeniedAcl.AddAccessRule($DenyRule)
        Set-Acl -LiteralPath $PermissionDir -AclObject $DeniedAcl
        $Permission = Invoke-CliCase "permission" @(
            "convert", $Input, "--output", (Join-Path $PermissionDir "denied.pdf"),
            "--json"
        ) 1
        if ($Permission.error_code -notin @("OUTPUT_UNAVAILABLE", "OUTPUT_REPLACE_FAILED")) {
            throw "Permission failure did not retain an output-integrity code."
        }
    } finally {
        Set-Acl -LiteralPath $PermissionDir -AclObject $OriginalAcl
    }

    $NetworkAfter = Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
        Select-Object Name, InterfaceDescription, Status, LinkSpeed
    $NetworkAfter | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "network-state-after-runtime.json"
    ) -Encoding UTF8
    $OnlineAfter = @($NetworkAfter | Where-Object Status -eq "Up")
    if ($RequireOffline -and $OnlineAfter.Count -ne 0) {
        throw "RequireOffline was selected but a physical network adapter is up after runtime tests."
    }
    [ordered]@{
        require_offline = [bool]$RequireOffline
        physical_adapters_up_before = $OnlineBefore.Count
        physical_adapters_up_after = $OnlineAfter.Count
        accepted_offline_evidence = (
            [bool]$RequireOffline -and
            $OnlineBefore.Count -eq 0 -and
            $OnlineAfter.Count -eq 0
        )
    } | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "offline-verdict.json"
    ) -Encoding UTF8

    $GuiProcess = Start-Process -FilePath $GuiPath -PassThru
    Start-Sleep -Seconds 5
    if ($GuiProcess.HasExited) { throw "Windowed GUI exited during startup smoke." }
    Stop-Process -Id $GuiProcess.Id
    $DebugProcess = Start-Process -FilePath $DebugPath -PassThru
    Start-Sleep -Seconds 5
    if ($DebugProcess.HasExited) { throw "Diagnostic GUI exited during startup smoke." }
    Stop-Process -Id $DebugProcess.Id

    $env:PATH = $OldEnvironment.PATH
    $env:USERPROFILE = $OldEnvironment.USERPROFILE
    $env:HOME = $OldEnvironment.HOME
    $env:LOCALAPPDATA = $OldEnvironment.LOCALAPPDATA
    $env:VIRTUAL_ENV = $OldEnvironment.VIRTUAL_ENV
    $env:PLAYWRIGHT_BROWSERS_PATH = $OldEnvironment.PLAYWRIGHT_BROWSERS_PATH

    $CanonicalFixtureRoot = Join-Path $RuntimeDir "canonical fixtures"
    Copy-Item -LiteralPath (Join-Path $RepoRoot "tests\fixtures\canonical") `
        -Destination $CanonicalFixtureRoot -Recurse
    $CanonicalActual = Join-Path $EvidenceRoot "canonical-actual"
    $CanonicalReport = Join-Path $EvidenceRoot "canonical-report.json"
    $CanonicalDiff = Join-Path $EvidenceRoot "canonical-diff"
    Invoke-Native $Python @(
        "tools\artifact_visual_regression.py",
        "--converter", $script:CliPath,
        "--manifest", (Join-Path $CanonicalFixtureRoot "manifest.json"),
        "--expected", (Join-Path $RepoRoot "tests\goldens\canonical\expected.json"),
        "--actual-dir", $CanonicalActual,
        "--report", $CanonicalReport,
        "--diff-dir", $CanonicalDiff
    ) @(0, 1)

    $Created = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $Sbom = Join-Path $EvidenceRoot "LibreMarkPDF-Windows-x64.spdx.json"
    Invoke-Native $Python @(
        "tools\generate_windows_sbom.py",
        "--lock", (Join-Path $RepoRoot "requirements\locks\windows-x64-py39.txt"),
        "--artifact-dir", $ExternalCandidate,
        "--commit", $Commit,
        "--created", $Created,
        "--output", $Sbom
    )

    Get-AuthenticodeSignature -LiteralPath @($GuiPath, $script:CliPath, $DebugPath) |
        Select-Object Path, Status, StatusMessage, SignerCertificate, TimeStamperCertificate |
        ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
            Join-Path $LogDir "authenticode.json"
        ) -Encoding UTF8
    if (Get-Command Get-MpComputerStatus -ErrorAction SilentlyContinue) {
        Get-MpComputerStatus | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (
            Join-Path $LogDir "windows-defender-status.json"
        ) -Encoding UTF8
        Get-MpThreatDetection -ErrorAction SilentlyContinue |
            ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
                Join-Path $LogDir "windows-defender-detections.json"
            ) -Encoding UTF8
    }

    $CandidateSize = (Get-ChildItem -LiteralPath $ExternalCandidate -File -Recurse |
        Measure-Object -Property Length -Sum).Sum
    [ordered]@{
        candidate_bytes = $CandidateSize
        cli_success_milliseconds = $SuccessTimer.ElapsedMilliseconds
        gui_startup_smoke_seconds = 5
    } | ConvertTo-Json | Set-Content -LiteralPath (
        Join-Path $LogDir "size-performance.json"
    ) -Encoding UTF8

    $CandidateZip = Join-Path $ArtifactDir (
        "LibreMarkPDF-Windows-x64-unsigned-" + $Commit.Substring(0, 12) + ".zip"
    )
    Compress-Archive -LiteralPath $ExternalCandidate -DestinationPath $CandidateZip -Force
    Get-FileHash -Algorithm SHA256 -LiteralPath $CandidateZip |
        Select-Object Path, Algorithm, Hash | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $LogDir "candidate-zip-sha256.json") -Encoding UTF8

    @"
# Native GUI and accessibility review

Candidate commit: `$Commit`
Candidate GUI: `$GuiPath`

- [ ] Windowed GUI starts with no console; diagnostic GUI starts with a console.
- [ ] Sample and source previews render while physically disconnected.
- [ ] Preview is scrollable and zoom works at every offered level.
- [ ] Rapid edits debounce; an older preview never replaces a newer request.
- [ ] Minimum window size keeps files, preview, status, and actions operable.
- [ ] Batch progress advances; cancellation finishes the active item and marks remaining items cancelled.
- [ ] Closing during preview/conversion waits safely and leaves no corrupt PDF.
- [ ] Collision and overwrite choices are presented before rendering.
- [ ] Open-PDF and open-folder actions appear only for successful results.
- [ ] EN and FR labels/status remain localized during operations.
- [ ] User manual opens the packaged EN/FR PDF matching the active language; headings, code, links, Unicode, pagination, selectable text, page footer, and supplied styling are correct, with no clipping or remote resource.
- [ ] Tab order, focus visibility, Ctrl+O/Ctrl+R/Ctrl+G/Escape, labels, contrast, and Windows high-DPI scaling are acceptable.
- [ ] Drag-and-drop works; source tests also passed with tkinterdnd2 blocked.
- [ ] Theme cards, default@1, installed community theme selection, and themed preview work.
- [ ] External Unicode-and-space path, empty profile/cache, no Python on PATH, and offline state are visibly confirmed.

Reviewer: ____________________
Windows display scale(s): ____________________
Evidence screenshots/video paths: ____________________
Result: PASS / FAIL
"@ | Set-Content -LiteralPath (Join-Path $EvidenceRoot "manual-gui-review.md") -Encoding UTF8

    $StatusAfter = & git status --short --branch
    $PorcelainAfter = & git status --porcelain
    $StatusAfter | Set-Content -LiteralPath (Join-Path $LogDir "git-status-after.txt") -Encoding UTF8
    if ($PorcelainAfter) {
        throw "The native source checkout changed during evidence collection."
    }
} finally {
    if ($null -ne $OldEnvironment) {
        $env:PATH = $OldEnvironment.PATH
        $env:USERPROFILE = $OldEnvironment.USERPROFILE
        $env:HOME = $OldEnvironment.HOME
        $env:LOCALAPPDATA = $OldEnvironment.LOCALAPPDATA
        $env:VIRTUAL_ENV = $OldEnvironment.VIRTUAL_ENV
        $env:PLAYWRIGHT_BROWSERS_PATH = $OldEnvironment.PLAYWRIGHT_BROWSERS_PATH
    }
    Stop-Transcript | Out-Null
}

$ManifestPath = Join-Path $EvidenceRoot "WINDOWS_VALIDATION_MANIFEST.sha256"
$ManifestLines = Get-ChildItem -LiteralPath $EvidenceRoot -File -Recurse |
    Where-Object FullName -ne $ManifestPath |
    Sort-Object FullName |
    ForEach-Object {
        $Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
        $Relative = $_.FullName.Substring($EvidenceRoot.TrimEnd("\").Length + 1)
        $Hash.Hash.ToLowerInvariant() + "  " + $Relative.Replace("\", "/")
    }
[IO.File]::WriteAllLines(
    $ManifestPath,
    [string[]]$ManifestLines,
    [Text.UTF8Encoding]::new($false)
)

$EvidenceArchive = $EvidenceRoot.TrimEnd("\") + ".zip"
Compress-Archive -LiteralPath $EvidenceRoot -DestinationPath $EvidenceArchive -Force
$EvidenceHash = Get-FileHash -Algorithm SHA256 -LiteralPath $EvidenceArchive
Write-Host ("Evidence archive: " + $EvidenceArchive)
Write-Host ("Evidence SHA-256: " + $EvidenceHash.Hash.ToLowerInvariant())
Write-Host "Automation complete. Windows validation still requires the signed manual GUI review and integrator evaluation."
