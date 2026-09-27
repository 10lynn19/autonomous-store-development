$Root = "C:\Market\framework_v1_rebuild"
$LogFile = Join-Path $Root "logs\A_series\a0_train.log"
$ExitFile = Join-Path $Root "logs\A_series\a0_exit_code.txt"
$Seen = 0

Write-Host "Waiting for A0 log: $LogFile"
while (-not (Test-Path $LogFile)) {
    Start-Sleep -Seconds 1
}

while ($true) {
    $Lines = @(Get-Content -Path $LogFile -ErrorAction SilentlyContinue)
    if ($Lines.Count -gt $Seen) {
        $Lines[$Seen..($Lines.Count - 1)] | ForEach-Object { Write-Host $_ }
        $Seen = $Lines.Count
    }
    if ((Test-Path $ExitFile) -and $Lines.Count -le $Seen) {
        $Code = Get-Content $ExitFile
        Write-Host ""
        Write-Host "A0 training finished with exit code $Code"
        exit [int]$Code
    }
    Start-Sleep -Seconds 2
}
