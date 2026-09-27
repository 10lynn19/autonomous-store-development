$Root = "C:\Market\autonomous-store-development"
$LogFile = Join-Path $Root "logs\B_series\b0_train.log"
$ExitFile = Join-Path $Root "logs\B_series\b0_exit_code.txt"

while (-not (Test-Path $LogFile)) {
    Write-Host "Waiting for B0 training log..."
    Start-Sleep -Seconds 2
}

Get-Content $LogFile -Wait | ForEach-Object {
    Write-Host $_
    if ($_ -match "TRAIN_EXIT_CODE=") { break }
}

if (Test-Path $ExitFile) {
    exit [int](Get-Content $ExitFile -Raw)
}
