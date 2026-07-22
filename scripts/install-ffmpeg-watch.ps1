# Finish FFmpeg install for /watch skill (run once after download completes)
$ErrorActionPreference = 'Stop'
$binDir = Join-Path $env:USERPROFILE '.local\ffmpeg\bin'
$zip = Join-Path $env:USERPROFILE '.local\ffmpeg\ffmpeg-essentials.zip'
if (Test-Path (Join-Path $binDir 'ffmpeg.exe')) {
  Write-Host "FFmpeg already installed at $binDir"
  exit 0
}
if (-not (Test-Path $zip)) {
  Write-Host "Missing zip: $zip"
  Write-Host "Download: curl.exe -L -o `"$zip`" https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-essentials_build.zip"
  exit 1
}
$minBytes = 80MB
if ((Get-Item $zip).Length -lt $minBytes) {
  Write-Host "Zip incomplete ($(Get-Item $zip).Length bytes). Wait for download or re-run curl."
  exit 2
}
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$extract = Join-Path $env:TEMP 'ffmpeg-extract-beauty'
if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $extract -Force
$innerBin = Get-ChildItem -Path $extract -Recurse -Directory -Filter 'bin' | Select-Object -First 1
Copy-Item -Path (Join-Path $innerBin.FullName '*') -Destination $binDir -Force
& (Join-Path $binDir 'ffmpeg.exe') -version | Select-Object -First 1
Write-Host "Done. Restart Cursor/terminal so PATH includes $binDir"
