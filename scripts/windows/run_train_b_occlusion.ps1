$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$LogDir = Join-Path $Root "logs\B_series"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $Root

foreach ($Branch in @("b_c0_clean_control", "b_c2_real_pickup")) {
    $LogFile = Join-Path $LogDir ($Branch + "_train.log")
    $ExitFile = Join-Path $LogDir ($Branch + "_exit_code.txt")
    if (Test-Path (Join-Path $Root "outputs\B_series\training\$Branch")) {
        throw "Output already exists for $Branch; refusing to overwrite it."
    }
    if (Test-Path $LogFile) {
        throw "Training log already exists for $Branch; refusing duplicate launch."
    }
    $Command = '"' + $Python + '" -u "src\train_b_occlusion.py" ' + $Branch + ' > "' + $LogFile + '" 2>&1'
    & cmd.exe /d /c $Command
    $Code = $LASTEXITCODE
    "TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
    Set-Content -Path $ExitFile -Value $Code
    if ($Code -ne 0) { exit $Code }
}
