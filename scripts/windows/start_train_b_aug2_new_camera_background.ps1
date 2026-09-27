$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$Branch = "b_5"
if (Test-Path (Join-Path $Root "outputs\B_series\training\$Branch")) {
    throw "Output already exists for $Branch; refusing duplicate launch."
}
if (Test-Path (Join-Path $Root "logs\B_series\${Branch}_train.log")) {
    throw "Training log already exists for $Branch; refusing duplicate launch."
}

$Process = Start-Process powershell.exe -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
    "$Root\scripts\windows\run_train_b_aug2_new_camera.ps1"
) -WindowStyle Hidden -PassThru
Write-Output "B_AUG2_NEW_CAMERA_PID=$($Process.Id)"
