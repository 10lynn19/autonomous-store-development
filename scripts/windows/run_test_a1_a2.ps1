$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$LogDir = Join-Path $Root "logs\A_series"
$LogFile = Join-Path $LogDir "a1_a2_test.log"
$ExitFile = Join-Path $LogDir "a1_a2_test_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
Set-Location $Root

$Command = '"' + $Python + '" -u "src\test_branches.py" a1_synthetic a2_phone > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"TEST_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
