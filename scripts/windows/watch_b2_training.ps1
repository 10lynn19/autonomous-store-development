$Root = "C:\Market\autonomous-store-development"
$LogFile = Join-Path $Root "logs\B_series\b2_train.log"
$ExitFile = Join-Path $Root "logs\B_series\b2_exit_code.txt"

while (-not (Test-Path $LogFile)) {
    Write-Host "Waiting for B2 training log..."
    Start-Sleep -Seconds 2
}
Get-Content $LogFile -Wait | ForEach-Object {
    Write-Host $_
    if ($_ -match "TRAIN_EXIT_CODE=") { break }
}
if (Test-Path $ExitFile) { exit [int](Get-Content $ExitFile -Raw) }
