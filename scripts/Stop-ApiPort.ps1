# Stop any process listening on the API port (default 8000) so a stale server is not left running.
param(
    [int]$Port = 8000
)

$listeners = @(
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
) | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($procId in $listeners) {
    if (-not $procId) { continue }
    try {
        $proc = Get-Process -Id $procId -ErrorAction Stop
        Write-Host "Stopping $($proc.ProcessName) (PID $procId) on port $Port..."
        Stop-Process -Id $procId -Force -ErrorAction Stop
    } catch {
        Write-Warning "Could not stop PID ${procId} on port ${Port}: $_"
    }
}
