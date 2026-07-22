$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

& (Join-Path $PSScriptRoot "Stop-ApiPort.ps1") -Port 8000

$venv = Join-Path $Root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    python -m venv $venv
    & $python -m pip install -U pip
    & $python -m pip install -r requirements.txt
}

if (-not $env:ENABLE_DEV_SHORTCUTS) {
    $env:ENABLE_DEV_SHORTCUTS = "1"
}

& $python scripts/run_api.py
