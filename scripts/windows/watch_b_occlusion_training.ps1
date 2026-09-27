$Root = "C:\Market\autonomous-store-development"
$LogDir = Join-Path $Root "logs\B_series"
$Branches = @("b_c0_clean_control", "b_c2_real_pickup")

while ($true) {
    Clear-Host
    Write-Output "B occlusion training: C0 clean control, then C2 real pickup"
    Write-Output "Updated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    foreach ($Branch in $Branches) {
        $LogFile = Join-Path $LogDir ($Branch + "_train.log")
        $ExitFile = Join-Path $LogDir ($Branch + "_exit_code.txt")
        Write-Output ""
        Write-Output "=== $Branch ==="
        if (Test-Path $ExitFile) {
            Write-Output "Exit code: $(Get-Content $ExitFile)"
        }
        if (Test-Path $LogFile) {
            Get-Content $LogFile -Tail 12
        } else {
            Write-Output "Waiting to start"
        }
    }
    Start-Sleep -Seconds 5
}
