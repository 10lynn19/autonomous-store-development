$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
Set-Location $Root
if ((Test-Path "outputs\B_series\training\b_aug1_light") -or
    (Test-Path "outputs\B_series\training\b_aug2_mosaic_copy")) {
    throw "One or more augmentation output folders already exist."
}

$Process = Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "$Root\scripts\windows\run_train_b_augmentation.ps1"
) -WindowStyle Hidden -PassThru

Write-Output "AUGMENTATION_PID=$($Process.Id)"
