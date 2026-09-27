$ErrorActionPreference = "Stop"

$Root = "C:\Market\framework_v1_rebuild"
$Data = Join-Path $Root "data"
$OldVideos = Join-Path $Data "videos"
$VideosA = Join-Path $Data "videos_A"
$VideosB = Join-Path $Data "videos_B"

function Ensure-Directory([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Move-MatchingFiles([string]$Source, [string[]]$Patterns, [string]$Destination) {
    Ensure-Directory $Destination
    if (-not (Test-Path $Source)) { return }
    foreach ($Pattern in $Patterns) {
        Get-ChildItem $Source -File -Filter $Pattern -ErrorAction SilentlyContinue |
            Move-Item -Destination $Destination -Force
    }
}

foreach ($SeriesRoot in @($VideosA, $VideosB)) {
    foreach ($Category in @("clean_background", "phone_video", "camera", "test")) {
        Ensure-Directory (Join-Path $SeriesRoot $Category)
    }
}

if (Test-Path $OldVideos) {
    $Clean = Join-Path $OldVideos "clean_background"
    Move-MatchingFiles $Clean @("*coke*", "*thinkbar*", "*ziploc*") (Join-Path $VideosA "clean_background")
    Move-MatchingFiles $Clean @("*oreo*", "*goodwipe*") (Join-Path $VideosB "clean_background")

    $Phone = Join-Path $OldVideos "phone_video"
    Move-MatchingFiles $Phone @("*coke*", "*thinkbar*", "*ziploc*") (Join-Path $VideosA "phone_video")
    Move-MatchingFiles $Phone @("*oreo*", "*goodwipe*") (Join-Path $VideosB "phone_video")
    Move-MatchingFiles $Phone @("*paperwiper*") (Join-Path $VideosB "phone_video")

    $Camera = Join-Path $OldVideos "camera"
    Move-MatchingFiles $Camera @("*coke*", "*thinkbar*", "*ziploc*") (Join-Path $VideosA "camera")
    Move-MatchingFiles $Camera @("*oreo*", "*goodwipe*") (Join-Path $VideosB "camera")
    foreach ($Folder in @("more_thinkbar", "more_ziploc")) {
        $SourceFolder = Join-Path $Camera $Folder
        if (Test-Path $SourceFolder) {
            Move-Item $SourceFolder (Join-Path (Join-Path $VideosA "camera") $Folder) -Force
        }
    }

    $Test = Join-Path $OldVideos "test"
    Move-MatchingFiles $Test @("multiple1.*", "multiple2.*", "*coke*", "*thinkbar*", "*ziploc*") (Join-Path $VideosA "test")
    Move-MatchingFiles $Test @("multiple_new*", "*oreo*", "*goodwipe*") (Join-Path $VideosB "test")
}

# Coke is shared by both series. Copying keeps the folders self-contained.
foreach ($Category in @("clean_background", "phone_video", "camera", "test")) {
    Get-ChildItem (Join-Path $VideosA $Category) -File -Filter "*coke*" -ErrorAction SilentlyContinue |
        Copy-Item -Destination (Join-Path $VideosB $Category) -Force
}

$OldDatasets = Join-Path $Data "datasets"
$DatasetsA = Join-Path $Data "datasets_A"
if ((Test-Path $OldDatasets) -and -not (Test-Path $DatasetsA)) {
    Move-Item $OldDatasets $DatasetsA
}
Ensure-Directory (Join-Path $Data "datasets_B")

$Outputs = Join-Path $Root "outputs"
$OutputsA = Join-Path $Outputs "A_series"
$OutputsB = Join-Path $Outputs "B_series"
Ensure-Directory $OutputsA
Ensure-Directory $OutputsB
foreach ($Folder in @("training", "tests", "presentations")) {
    $Source = Join-Path $Outputs $Folder
    if (Test-Path $Source) { Move-Item $Source (Join-Path $OutputsA $Folder) -Force }
}
Ensure-Directory (Join-Path $OutputsA "dataset_review")
Ensure-Directory (Join-Path $OutputsB "dataset_review")
$Review = Join-Path $Outputs "dataset_review"
foreach ($Folder in @("camera_more_contact_sheets", "test_ground_truth")) {
    $Source = Join-Path $Review $Folder
    if (Test-Path $Source) { Move-Item $Source (Join-Path (Join-Path $OutputsA "dataset_review") $Folder) -Force }
}
$BReview = Join-Path $Review "oreo_goodwipes_contact_sheets"
if (Test-Path $BReview) {
    Move-Item $BReview (Join-Path (Join-Path $OutputsB "dataset_review") "oreo_goodwipes_contact_sheets") -Force
}

$Logs = Join-Path $Root "logs"
$LogsA = Join-Path $Logs "A_series"
Ensure-Directory $LogsA
Ensure-Directory (Join-Path $Logs "B_series")
Get-ChildItem $Logs -File -ErrorAction SilentlyContinue | Move-Item -Destination $LogsA -Force

Write-Output "A/B series migration completed."
