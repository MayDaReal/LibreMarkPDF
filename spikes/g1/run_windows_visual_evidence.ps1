param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Prepare", "Run")]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$FontRoot,

    [string]$Python = "python",
    [string]$BrowserRoot,
    [string]$EvidenceRoot
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $SourceRoot

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if ($Mode -eq "Prepare") {
    Invoke-Checked {
        & $Python spikes/g1/fetch_font_candidates.py --output-dir $FontRoot
    }
    Write-Host "Preparation complete. Disconnect the test host from the network before Run."
    exit 0
}

if (-not $BrowserRoot) {
    throw "Run mode requires -BrowserRoot pointing to Playwright Chromium revision 1223."
}
if (-not $EvidenceRoot) {
    throw "Run mode requires a new -EvidenceRoot outside the repository."
}
if (Test-Path $EvidenceRoot) {
    throw "EvidenceRoot already exists; use a new empty directory."
}
New-Item -ItemType Directory -Path $EvidenceRoot | Out-Null
$EvidenceRoot = (Resolve-Path $EvidenceRoot).Path
$Transcript = Join-Path $EvidenceRoot "windows-visual-transcript.txt"
Start-Transcript -Path $Transcript | Out-Null
$TranscriptStarted = $true

try {
    $SourceCommit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Could not record the source commit."
    }
    $SourceStatus = @(git status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not record the source status."
    }

    Invoke-Checked {
        & $Python -c "import importlib.metadata as m, platform, sys; assert sys.version_info[:2] == (3, 9); expected={'Markdown':'3.9','playwright':'1.60.0','Pillow':'11.3.0','pypdfium2':'5.11.0'}; actual={k:m.version(k) for k in expected}; assert actual == expected, actual; print(platform.platform(), platform.machine(), platform.python_version(), actual)"
    }
    Invoke-Checked {
        & $Python spikes/g1/fetch_font_candidates.py --output-dir $FontRoot --verify-only
    }

    $env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path $BrowserRoot).Path
    $Current = Join-Path $EvidenceRoot "windows-current"
    $Candidate = Join-Path $EvidenceRoot "windows-candidate"
    $Repeat = Join-Path $EvidenceRoot "windows-candidate-repeat"

    Invoke-Checked {
        & $Python spikes/g1/visual_probe.py --profile current --output-dir $Current
    }
    Invoke-Checked {
        & $Python spikes/g1/visual_probe.py --profile candidate --font-root $FontRoot --output-dir $Candidate
    }
    Invoke-Checked {
        & $Python spikes/g1/visual_probe.py --profile candidate --font-root $FontRoot --output-dir $Repeat
    }
    Invoke-Checked {
        & $Python spikes/g1/visual_compare.py --comparison appearance `
            --reference-dir $Current --candidate-dir $Candidate `
            --output (Join-Path $EvidenceRoot "windows-appearance.json") `
            --diff-dir (Join-Path $EvidenceRoot "windows-appearance-diffs")
    }
    Invoke-Checked {
        & $Python spikes/g1/visual_compare.py --comparison cross-os `
            --reference-dir $Candidate --candidate-dir $Repeat `
            --output (Join-Path $EvidenceRoot "windows-repeat-comparison.json") `
            --diff-dir (Join-Path $EvidenceRoot "windows-repeat-diffs")
    }

    $Context = [ordered]@{
        schema = 1
        source_commit = $SourceCommit
        source_status = $SourceStatus
        computer = $env:COMPUTERNAME
        user = $env:USERNAME
        os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture
        processor = Get-CimInstance Win32_Processor | Select-Object Name, Architecture
        network_adapters = @(Get-NetAdapter | Select-Object Name, Status, LinkSpeed, InterfaceDescription)
        firewall = @(Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction)
        browser_root = $env:PLAYWRIGHT_BROWSERS_PATH
        font_root = (Resolve-Path $FontRoot).Path
    }
    $Context | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 `
        (Join-Path $EvidenceRoot "windows-execution-context.json")
}
finally {
    if ($TranscriptStarted) {
        Stop-Transcript | Out-Null
    }
}

$ManifestPath = Join-Path $EvidenceRoot "WINDOWS_VISUAL_EVIDENCE.sha256"
$ManifestLines = Get-ChildItem -Path $EvidenceRoot -File -Recurse |
    Where-Object { $_.FullName -ne $ManifestPath } |
    Sort-Object FullName |
    ForEach-Object {
        $Relative = $_.FullName.Substring($EvidenceRoot.Length + 1).Replace("\", "/")
        $Hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLowerInvariant()
        "$Hash  $Relative"
    }
$ManifestLines | Set-Content -Encoding ASCII $ManifestPath

$Archive = "$EvidenceRoot.zip"
Compress-Archive -Path (Join-Path $EvidenceRoot "*") -DestinationPath $Archive
$ArchiveHash = (Get-FileHash -Algorithm SHA256 $Archive).Hash.ToLowerInvariant()
Write-Host "Evidence archive: $Archive"
Write-Host "Evidence archive SHA-256: $ArchiveHash"
exit 0
