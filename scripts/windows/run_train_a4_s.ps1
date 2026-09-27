$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$LogDir = Join-Path $Root "logs\A_series"
$LogFile = Join-Path $LogDir "a4_s_train.log"
$ExitFile = Join-Path $LogDir "a4_s_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
Set-Location $Root

$Command = '"' + $Python + '" -u "src\train_a4_s_camera_synthetic.py" > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
