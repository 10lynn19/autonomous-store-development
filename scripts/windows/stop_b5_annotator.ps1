$Listener = Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue
if ($Listener) {
    Stop-Process -Id $Listener.OwningProcess -Force
    Write-Output "Stopped annotation server PID=$($Listener.OwningProcess)"
} else {
    Write-Output "No annotation server was listening on port 8771"
}
