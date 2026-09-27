$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$LogDir = Join-Path $Root "logs\B_series"
$LogFile = Join-Path $LogDir "b_occlusion_test.log"
$ExitFile = Join-Path $LogDir "b_occlusion_test_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
if (Test-Path $LogFile) { throw "Test log already exists; refusing duplicate launch." }
Set-Location $Root
$Command = '"' + $Python + '" -u "src\test_b_branches.py" b_c0_clean_control b_c2_real_pickup --device 0 > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"TEST_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
