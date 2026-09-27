$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$LogDir = Join-Path $Root "logs\B_series"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $Root

foreach ($Branch in @("b_aug1_light", "b_aug2_mosaic_copy")) {
    $Script = if ($Branch -eq "b_aug1_light") { "src\train_b_aug1_light.py" } else { "src\train_b_aug2_mosaic_copy.py" }
    $LogFile = Join-Path $LogDir ($Branch + "_train.log")
    $ExitFile = Join-Path $LogDir ($Branch + "_exit_code.txt")
    if (Test-Path (Join-Path $Root "outputs\B_series\training\$Branch")) {
        throw "Output already exists for $Branch; refusing to overwrite a controlled experiment."
    }
    Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
    $Command = '"' + $Python + '" -u "' + $Script + '" > "' + $LogFile + '" 2>&1'
    & cmd.exe /d /c $Command
    $Code = $LASTEXITCODE
    "TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
    Set-Content -Path $ExitFile -Value $Code
    if ($Code -ne 0) { exit $Code }
}
