$Root = "C:\Market\autonomous-store-development"
$LogFile = Join-Path $Root "logs\A_series\a4_p_train.log"

Write-Host "A4-P live training log - Control-C stops watching only." -ForegroundColor Cyan
while (-not (Test-Path $LogFile)) {
    Start-Sleep -Seconds 1
}
Get-Content $LogFile -Wait
