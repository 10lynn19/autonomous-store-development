$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root

if (-not (Test-Path "data\datasets_B\b1_camera_addition\manifest.json")) {
    & $Python "src\annotate_test_videos.py" `
        --videos "data\videos_B\camera" `
        --dataset "data\datasets_B\b1_camera_addition" `
        --pattern "camera_clean_*" `
        --frames-per-video 48 `
        --split train `
        --classes coke_zero oreo goodwipes `
        --prepare --prepare-only
}

if (-not (Test-Path "data\datasets_B\b2_phone_addition\manifest.json")) {
    & $Python "src\annotate_test_videos.py" `
        --videos "data\videos_B\phone_video" `
        --dataset "data\datasets_B\b2_phone_addition" `
        --frames-per-video 24 `
        --split train `
        --classes coke_zero oreo goodwipes `
        --prepare --prepare-only
}

Write-Output "B1/B2 annotation frames are ready."
