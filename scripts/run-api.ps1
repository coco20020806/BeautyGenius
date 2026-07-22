$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$venv = Join-Path $Root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    python -m venv $venv
    & $python -m pip install -U pip
    & $python -m pip install -r requirements.txt
}

& $python scripts/run_api.py
