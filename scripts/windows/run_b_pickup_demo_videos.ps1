$ErrorActionPreference = "Stop"

$Root = "C:\Market\autonomous-store-development"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root
$Videos = @(
    "test_pickup_coke.mp4",
    "test_pickup_goodwipes.mov",
    "multiple_new1.mov",
    "multiple_new2.mov"
)
foreach ($Video in $Videos) {
    $Stem = [System.IO.Path]::GetFileNameWithoutExtension($Video)
    & $Python "src\run_b_pickup_demo.py" "data\videos_B\test\$Video" `
        --sample-fps 5 --output "outputs\B_series\pickup_demo\rendered\$Stem.mp4"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
