$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$LogDir = Join-Path $Root "logs\A_series"
$LogFile = Join-Path $LogDir "a3_train.log"
$ExitFile = Join-Path $LogDir "a3_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
Set-Location $Root

$Command = '"' + $Python + '" -u "src\train_a3_camera.py" > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
