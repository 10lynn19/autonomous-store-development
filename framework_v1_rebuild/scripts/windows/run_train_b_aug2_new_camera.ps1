$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$Branch = "b_5"
$LogDir = Join-Path $Root "logs\B_series"
$LogFile = Join-Path $LogDir ($Branch + "_train.log")
$ExitFile = Join-Path $LogDir ($Branch + "_exit_code.txt")
$Python = Join-Path $Root ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $Root

if (Test-Path (Join-Path $Root "outputs\B_series\training\$Branch")) {
    throw "Output already exists for $Branch; refusing to overwrite it."
}
if (Test-Path $LogFile) {
    throw "Training log already exists for $Branch; refusing duplicate launch."
}

$Command = '"' + $Python + '" -u "src\train_b_aug2_new_camera.py" > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
