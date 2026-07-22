param(
  [string]$Video,
  [string]$ParseRun,
  [string]$UserPhoto,
  [string]$ReferenceImage,
  [switch]$UseBaseline,
  [ValidateSet('female', 'male')]
  [string]$Baseline = 'female',
  [string]$ReferenceStep,
  [ValidateSet('full', 'fast')]
  [string]$Mode = 'full',
  [switch]$SkipKeyframeQa,
  [switch]$SkipReplicationRefs,
  [switch]$SkipTutorialMap,
  [switch]$SkipTextEnrich,
  [switch]$SkipVisionEnrich,
  [switch]$SkipPreview,
  [switch]$SkipTransfer,
  [switch]$StrictReplication,
  [switch]$Quiet
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

$script = Join-Path $RepoRoot 'scripts\run_beauty_replicate.py'
$argsList = @()
if ($Video) { $argsList += '--video'; $argsList += $Video }
if ($ParseRun) { $argsList += '--parse-run'; $argsList += $ParseRun }
if ($UserPhoto) { $argsList += '--user-photo'; $argsList += $UserPhoto }
if ($ReferenceImage) { $argsList += '--reference-image'; $argsList += $ReferenceImage }
if ($UseBaseline) { $argsList += '--use-baseline' }
if ($Baseline) { $argsList += '--baseline'; $argsList += $Baseline }
if ($ReferenceStep) { $argsList += '--reference-step'; $argsList += $ReferenceStep }
if ($Mode) { $argsList += '--mode'; $argsList += $Mode }
if ($SkipKeyframeQa) { $argsList += '--skip-keyframe-qa' }
if ($SkipReplicationRefs) { $argsList += '--skip-replication-refs' }
if ($SkipTutorialMap) { $argsList += '--skip-tutorial-map' }
if ($SkipTextEnrich) { $argsList += '--skip-text-enrich' }
if ($SkipVisionEnrich) { $argsList += '--skip-vision-enrich' }
if ($SkipPreview) { $argsList += '--skip-preview' }
if ($SkipTransfer) { $argsList += '--skip-transfer' }
if ($StrictReplication) { $argsList += '--strict-replication' }
if ($Quiet) { $argsList += '--quiet' }

& $python $script @argsList
exit $LASTEXITCODE
