# ProseForge Agent one-line installer for Windows (Task 187).
#
#   iex (irm https://raw.githubusercontent.com/<org>/ProseForge-Agent/main/scripts/install.ps1)
#
# Installs uv (preferred) or uses pipx, ensures Python 3.10+, installs the
# proseforge-agent package, and registers pf-agent on PATH.
#
# PowerShell 5.1 compatible: no ??, ?:, or ternary operators.
[CmdletBinding()]
param(
    [string] $Git = "",
    [switch] $System,
    [switch] $AllowVenv,
    [ValidateSet("", "uv", "pipx")] [string] $Manager = "",
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"

function Write-Log { param([string] $Message) Write-Host "[pf-agent-install] $Message" }
function Write-Err { param([string] $Message) Write-Host "[pf-agent-install] ERROR: $Message" -ForegroundColor Red }
function Test-Have { param([string] $Name) $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }

function Invoke-Step {
    param([string] $Command)
    if ($DryRun) {
        Write-Log "DRY-RUN: $Command"
    } else {
        Write-Log "+ $Command"
        Invoke-Expression $Command
    }
}

$package = "proseforge-agent"

if ($env:VIRTUAL_ENV -and -not $AllowVenv) {
    Write-Err "refusing to install inside an active virtualenv; deactivate or pass -AllowVenv"
    exit 3
}

# ensure a package manager (uv preferred)
$useManager = "uv"
if ($Manager -eq "pipx" -or ($Manager -eq "" -and -not (Test-Have "uv") -and (Test-Have "pipx"))) {
    $useManager = "pipx"
}
if ($useManager -eq "uv" -and -not (Test-Have "uv")) {
    Write-Log "installing uv"
    Invoke-Step "irm https://astral.sh/uv/install.ps1 | iex"
}
Write-Log "using manager: $useManager"

# ensure python
if ($useManager -eq "uv" -and -not (Test-Have "python")) {
    Invoke-Step "uv python install 3.11"
}

# install package
if ($Git -ne "") {
    $target = "git+https://github.com/NousResearch/proseforge-agent@$Git"
} else {
    $target = $package
}
if ($useManager -eq "uv") {
    Invoke-Step "uv tool install $target"
} else {
    Invoke-Step "pipx install $target"
}

# register PATH
$installDir = Join-Path $env:LOCALAPPDATA "Programs\ProseForge Agent"
if (-not $DryRun) {
    $current = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($current -notlike "*$installDir*") {
        Write-Log "adding $installDir to user PATH"
        [Environment]::SetEnvironmentVariable("PATH", "$installDir;$current", "User")
    }
}

# verify
if (-not $DryRun -and (Test-Have "pf-agent")) {
    Invoke-Step "pf-agent doctor --format json"
}

Write-Log "done. Next: run 'pf-agent'"
