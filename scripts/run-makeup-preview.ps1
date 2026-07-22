param(
  [string]$ParseRun,
  [string]$ReferenceImage,
  [string]$UserPhoto,
  [switch]$UseBaseline,
  [ValidateSet('female', 'male')]
  [string]$Baseline = 'female',
  [string]$ReferenceStep,
  [switch]$ValidateOnly,
  [switch]$SkipTransfer
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$venv = Join-Path $RepoRoot '.venv'
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host '创建虚拟环境并安装依赖...'
  python -m venv $venv
  & $python -m pip install -q --upgrade pip
  & $python -m pip install -q -r (Join-Path $RepoRoot 'requirements.txt')
}

$script = Join-Path $RepoRoot 'scripts\run_makeup_preview.py'
$argsList = @()
if ($ParseRun) { $argsList += '--parse-run'; $argsList += $ParseRun }
if ($ReferenceImage) { $argsList += '--reference-image'; $argsList += $ReferenceImage }
if ($UserPhoto) { $argsList += '--user-photo'; $argsList += $UserPhoto }
if ($UseBaseline) { $argsList += '--use-baseline' }
if ($Baseline) { $argsList += '--baseline'; $argsList += $Baseline }
if ($ReferenceStep) { $argsList += '--reference-step'; $argsList += $ReferenceStep }
if ($ValidateOnly) { $argsList += '--validate-only' }
if ($SkipTransfer) { $argsList += '--skip-transfer' }

& $python $script @argsList
exit $LASTEXITCODE
