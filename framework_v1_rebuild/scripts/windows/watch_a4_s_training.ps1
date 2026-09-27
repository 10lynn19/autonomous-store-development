$Root = "C:\Market\framework_v1_rebuild"
$LogFile = Join-Path $Root "logs\A_series\a4_s_train.log"

Write-Host "A4-S live training log - Control-C stops watching only." -ForegroundColor Cyan
while (-not (Test-Path $LogFile)) {
    Start-Sleep -Seconds 1
}
Get-Content $LogFile -Wait
