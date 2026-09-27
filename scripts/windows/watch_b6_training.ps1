$Root = "C:\Market\autonomous-store-development"
$LogFile = Join-Path $Root "logs\B_series\b_6_train.log"
$ExitFile = Join-Path $Root "logs\B_series\b_6_exit_code.txt"

while ($true) {
    Clear-Host
    Write-Output "B_6 six-product training"
    Write-Output "Updated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    if (Test-Path $ExitFile) {
        Write-Output "Exit code: $(Get-Content $ExitFile)"
    }
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 18
    } else {
        Write-Output "Waiting for training to start"
    }
    Start-Sleep -Seconds 5
}
