# ACC Monitor Agent - Windows Service Installation Script
# Run as Administrator

$ServiceName = "ACC-Monitor-Agent"
$ServiceDescription = "ACC Monitoring Agent - Collects server metrics"
$ScriptPath = "$PSScriptRoot\acc_agent.py"
$PythonPath = "python"  # Or full path to python.exe

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "Service $ServiceName already exists. Stopping and removing..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName
    Start-Sleep -Seconds 2
}

# Install NSSM (Non-Sucking Service Manager) if not present
$nssmPath = "C:\tools\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "NSSM not found. Please download from https://nssm.cc/download"
    Write-Host "and place nssm.exe in C:\tools\"
    exit 1
}

# Install service using NSSM
Write-Host "Installing $ServiceName service..."

& $nssmPath install $ServiceName $PythonPath $ScriptPath
& $nssmPath set $ServiceName Description $ServiceDescription
& $nssmPath set $ServiceName AppDirectory $PSScriptRoot
& $nssmPath set $ServiceName Start SERVICE_AUTO_START
& $nssmPath set $ServiceName AppStdout "$PSScriptRoot\service_stdout.log"
& $nssmPath set $ServiceName AppStderr "$PSScriptRoot\service_stderr.log"
& $nssmPath set $ServiceName AppRotateFiles 1
& $nssmPath set $ServiceName AppRotateOnline 1
& $nssmPath set $ServiceName AppRotateBytes 10485760

# Start the service
Write-Host "Starting $ServiceName service..."
Start-Service -Name $ServiceName

# Check status
$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Host "Service $ServiceName installed and running successfully!" -ForegroundColor Green
} else {
    Write-Host "Service installed but not running. Check logs for errors." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Service Management Commands:"
Write-Host "  Start:   Start-Service $ServiceName"
Write-Host "  Stop:    Stop-Service $ServiceName"
Write-Host "  Status:  Get-Service $ServiceName"
Write-Host "  Remove:  & $nssmPath remove $ServiceName confirm"
