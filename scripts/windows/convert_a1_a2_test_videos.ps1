$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development\outputs\A_series\tests"
$Branches = @("a1_synthetic_img1024_conf035", "a2_phone_img1024_conf035")

foreach ($Branch in $Branches) {
    $Source = Join-Path $Root "$Branch\videos"
    $Output = Join-Path $Root "$Branch\videos_mp4"
    New-Item -ItemType Directory -Force -Path $Output | Out-Null
    foreach ($Video in Get-ChildItem $Source -Recurse -Filter *.avi) {
        $Target = Join-Path $Output ($Video.BaseName + ".mp4")
        & ffmpeg -y -nostdin -hide_banner -loglevel error -i $Video.FullName `
            -c:v libx264 -preset fast -crf 24 -pix_fmt yuv420p -movflags +faststart $Target
        if ($LASTEXITCODE -ne 0) {
            throw "ffmpeg failed for $($Video.FullName)"
        }
    }
}

Write-Output "Converted A1/A2 test videos to H.264 MP4."
