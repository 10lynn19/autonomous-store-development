$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$LogDir = Join-Path $Root "logs\A_series"
$LogFile = Join-Path $LogDir "a1_a2_train.log"
$ExitFile = Join-Path $LogDir "a1_a2_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
Set-Location $Root

function Run-Step([string]$Name, [string]$Arguments) {
    "===== $Name =====" | Add-Content -Path $LogFile
    $Command = '"' + $Python + '" -u ' + $Arguments + ' >> "' + $LogFile + '" 2>&1'
    & cmd.exe /d /c $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$Code = 0
try {
    $A1Images = Get-ChildItem (Join-Path $Root "data\datasets_A\a1_synthetic_addition\images\train") -File -ErrorAction SilentlyContinue
    $A1Labels = Get-ChildItem (Join-Path $Root "data\datasets_A\a1_synthetic_addition\labels\train") -File -ErrorAction SilentlyContinue
    if ($A1Images.Count -ne 144 -or $A1Labels.Count -ne 144) {
        Run-Step "PREPARE A1" '"src\prepare_a1_synthetic.py" --overwrite'
    }
    else {
        "===== A1 DATA ALREADY VERIFIED: 144 images + 144 labels =====" | Add-Content -Path $LogFile
    }
    Run-Step "TRAIN A1" '"src\train_a1_synthetic.py"'
    Run-Step "TRAIN A2" '"src\train_a2_phone.py"'
}
catch {
    $_ | Out-String | Add-Content -Path $LogFile
    $Code = 1
}

"TRAIN_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
