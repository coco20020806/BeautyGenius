param(
  [string]$VideoPath,
  [ValidateSet('full', 'fast')]
  [string]$Mode = 'full',
  [switch]$SkipKeyframeQa,
  [switch]$SkipReplicationRefs,
  [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

function Find-Ffmpeg {
  $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $local = Join-Path $env:USERPROFILE '.local\ffmpeg\bin\ffmpeg.exe'
  if (Test-Path $local) { return $local }
  return $null
}

$ffmpeg = Find-Ffmpeg
if (-not $ffmpeg) {
  Write-Host '未找到 ffmpeg。请先安装并加入 PATH，或运行 scripts/install-ffmpeg-watch.ps1'
  exit 1
}

if (-not $VideoPath) {
  $VideoPath = Read-Host '请输入美妆教程视频的完整路径'
}
$VideoPath = $VideoPath.Trim().Trim('"')
if (-not (Test-Path -LiteralPath $VideoPath)) {
  Write-Host "视频不存在: $VideoPath"
  exit 1
}

$venv = Join-Path $RepoRoot '.venv'
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host '创建虚拟环境并安装依赖...'
  python -m venv $venv
  & $python -m pip install -q --upgrade pip
  & $python -m pip install -q -r (Join-Path $RepoRoot 'requirements.txt')
}

$script = Join-Path $RepoRoot 'scripts\parse_beauty_video.py'
$pyArgs = @($script, '--video', $VideoPath, '--mode', $Mode)
if ($SkipKeyframeQa) {
  $pyArgs += '--skip-keyframe-qa'
}
if ($SkipReplicationRefs) {
  $pyArgs += '--skip-replication-refs'
}
if ($Quiet) {
  $pyArgs += '--quiet'
}
& $python @pyArgs
exit $LASTEXITCODE
