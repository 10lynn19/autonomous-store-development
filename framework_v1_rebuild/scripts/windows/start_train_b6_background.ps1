$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$Branch = "b_6"
if (Test-Path (Join-Path $Root "outputs\B_series\training\$Branch")) {
    throw "Output already exists for $Branch; refusing duplicate launch."
}
if (Test-Path (Join-Path $Root "logs\B_series\${Branch}_train.log")) {
    throw "Training log already exists for $Branch; refusing duplicate launch."
}

$Process = Start-Process powershell.exe -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
    "$Root\scripts\windows\run_train_b6.ps1"
) -WindowStyle Hidden -PassThru
Write-Output "B6_TRAIN_PID=$($Process.Id)"
