# Get the directory of this script
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $DIR

# SILENT CLEANUP: Kill any existing backup server processes first
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*backup_server.py*" } | ForEach-Object { Stop-Process $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting PhoenixVault Backup Infrastructure..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Start Server 1 (Port 8001)
Write-Host "-> Starting Backup Server 1 (Port 8001)..." -ForegroundColor Yellow
$p1 = Start-Process python -ArgumentList "backup_servers/server_1/backup_server.py --port 8001" -PassThru -NoNewWindow
Write-Host "   [Started] PID: $($p1.Id)" -ForegroundColor Green

# Start Server 2 (Port 8002)
Write-Host "-> Starting Backup Server 2 (Port 8002)..." -ForegroundColor Yellow
$p2 = Start-Process python -ArgumentList "backup_servers/server_2/backup_server.py --port 8002" -PassThru -NoNewWindow
Write-Host "   [Started] PID: $($p2.Id)" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All backup servers are running in the background." -ForegroundColor Cyan
Write-Host "To stop the servers, use: Stop-Process -Id $($p1.Id), $($p2.Id)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
