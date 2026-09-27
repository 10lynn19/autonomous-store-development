$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Log = Join-Path $Root "logs\B_series\b2_auto_label.log"
Set-Location $Root
Remove-Item $Log -Force -ErrorAction SilentlyContinue

$Command = '"' + $Python + '" -u "src\pseudo_label_b2_phone.py" > "' + $Log + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE
"AUTO_LABEL_EXIT_CODE=$Code" | Add-Content -Path $Log
exit $Code
