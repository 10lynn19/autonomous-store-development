$Root = "C:\Market\autonomous-store-development"
$LogFile = Join-Path $Root "logs\A_series\a1_a2_train.log"
$ExitFile = Join-Path $Root "logs\A_series\a1_a2_exit_code.txt"

Write-Host "A1/A2 live training log - Control-C stops watching only." -ForegroundColor Cyan
while (-not (Test-Path $LogFile)) {
    Start-Sleep -Seconds 1
}
Get-Content $LogFile -Wait
