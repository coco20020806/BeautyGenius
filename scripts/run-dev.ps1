# Start FastAPI (background) + Vite dev server (foreground) in one terminal.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Get-NpmCmdPath {
    $cmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        $candidate = Join-Path (Split-Path $node.Source -Parent) "npm.cmd"
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "npm.cmd not found on PATH. Install Node.js and ensure npm is available."
}

$npmCmd = Get-NpmCmdPath

$venv = Join-Path $Root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating Python venv and installing requirements..."
    python -m venv $venv
    & $python -m pip install -U pip
    & $python -m pip install -r requirements.txt
}

$frontend = Join-Path $Root "frontend"
if (-not (Test-Path $frontend)) {
    throw "Missing frontend/ directory. Clone or sync the frontend first."
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend dependencies (npm install)..."
    Push-Location $frontend
    & $npmCmd install
    Pop-Location
}

$envExample = Join-Path $frontend ".env.example"
$envFile = Join-Path $frontend ".env"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "Created frontend/.env from .env.example"
}

$apiProcess = $null
try {
    & (Join-Path $PSScriptRoot "Stop-ApiPort.ps1") -Port 8000

    Write-Host "Starting API (http://127.0.0.1:8000)..."
    if (-not $env:ENABLE_DEV_SHORTCUTS) {
        $env:ENABLE_DEV_SHORTCUTS = "1"
    }
    $apiProcess = Start-Process `
        -FilePath $python `
        -ArgumentList "scripts/run_api.py" `
        -WorkingDirectory $Root `
        -PassThru `
        -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 45; $i++) {
        Start-Sleep -Seconds 1
        if ($apiProcess.HasExited) {
            throw "API exited early (code $($apiProcess.ExitCode)). Check DASHSCOPE_API_KEY or run .\scripts\run-api.ps1 alone for errors."
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            # still booting
        }
    }
    if (-not $ready) {
        throw "API did not respond on /health within 45 seconds."
    }

    Write-Host "API ready."
    Write-Host "Starting frontend (http://127.0.0.1:5174)..."
    Write-Host "Open http://127.0.0.1:5174 in your browser. Press Ctrl+C to stop both."
    Push-Location $frontend
    & $npmCmd run dev
} finally {
    Pop-Location -ErrorAction SilentlyContinue
    if ($null -ne $apiProcess -and -not $apiProcess.HasExited) {
        Write-Host "`nStopping API..."
        Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
