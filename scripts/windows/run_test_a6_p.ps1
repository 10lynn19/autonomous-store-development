$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$LogDir = Join-Path $Root "logs\A_series"
$LogFile = Join-Path $LogDir "a6_p_test.log"
$ExitFile = Join-Path $LogDir "a6_p_test_exit_code.txt"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Branch = "a6_p_balanced_camera_phone_img1024_conf035"
$TestOutput = Join-Path $Root "outputs\A_series\tests\$Branch"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Remove-Item $LogFile, $ExitFile -Force -ErrorAction SilentlyContinue
Set-Location $Root

$Command = '"' + $Python + '" -u "src\test_branches.py" a6_p_balanced_camera_phone > "' + $LogFile + '" 2>&1'
& cmd.exe /d /c $Command
$Code = $LASTEXITCODE

if ($Code -eq 0 -and (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $Source = Join-Path $TestOutput "videos"
    $Output = Join-Path $TestOutput "videos_mp4"
    New-Item -ItemType Directory -Force -Path $Output | Out-Null
    foreach ($Video in Get-ChildItem $Source -Recurse -Filter *.avi) {
        $Target = Join-Path $Output ($Video.BaseName + ".mp4")
        & ffmpeg -y -nostdin -hide_banner -loglevel error -i $Video.FullName `
            -c:v libx264 -preset fast -crf 24 -pix_fmt yuv420p -movflags +faststart $Target
        if ($LASTEXITCODE -ne 0) {
            "MP4 conversion failed for $($Video.FullName)" | Add-Content -Path $LogFile
            $Code = $LASTEXITCODE
            break
        }
    }
} elseif ($Code -eq 0) {
    "ffmpeg is not available in this shell; AVI results are complete and MP4 conversion is skipped." | Add-Content -Path $LogFile
}

"TEST_EXIT_CODE=$Code" | Add-Content -Path $LogFile
Set-Content -Path $ExitFile -Value $Code
exit $Code
