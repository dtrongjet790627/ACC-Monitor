@echo off
REM =====================================================================
REM ACC Monitor Agent - Windows Service Installation
REM
REM This script registers the ACC Monitor Agent as a Windows Service
REM using either pywin32 (preferred) or NSSM (fallback).
REM
REM Run as Administrator!
REM =====================================================================

setlocal EnableDelayedExpansion

set SERVICE_NAME=AccMonitorAgent
set SERVICE_DISPLAY=ACC Monitor Agent
set SCRIPT_DIR=%~dp0
set AGENT_SCRIPT=%SCRIPT_DIR%acc_monitor_agent_windows.py

echo =====================================================
echo  ACC Monitor Agent - Windows Service Installer
echo =====================================================
echo.

REM --- Check Administrator privileges ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator.
    echo         Right-click and select "Run as administrator".
    pause
    exit /b 1
)

REM --- Check Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo         Please install Python 3.6+ and add it to PATH.
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM --- Check agent script exists ---
if not exist "%AGENT_SCRIPT%" (
    echo [ERROR] Agent script not found: %AGENT_SCRIPT%
    pause
    exit /b 1
)

REM --- Check config file ---
if not exist "%SCRIPT_DIR%agent_config.json" (
    echo [WARN] agent_config.json not found. A default will be created on first run.
    echo        Please edit it with the correct server_id before starting the service.
)

echo.
echo Choose installation method:
echo   1. pywin32 (recommended, requires: pip install pywin32)
echo   2. NSSM (requires nssm.exe in PATH or C:\tools\nssm.exe)
echo   3. sc.exe (basic, no auto-restart)
echo.
set /p METHOD="Enter choice (1/2/3): "

if "%METHOD%"=="1" goto :INSTALL_PYWIN32
if "%METHOD%"=="2" goto :INSTALL_NSSM
if "%METHOD%"=="3" goto :INSTALL_SC
echo [ERROR] Invalid choice.
pause
exit /b 1


:INSTALL_PYWIN32
echo.
echo [INFO] Installing via pywin32...
echo.

REM Check pywin32
python -c "import win32serviceutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pywin32...
    pip install pywin32
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pywin32. Try method 2 or 3.
        pause
        exit /b 1
    )
)

REM Stop existing service if running
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Stopping existing service...
    net stop %SERVICE_NAME% >nul 2>&1
    python "%AGENT_SCRIPT%" remove >nul 2>&1
    timeout /t 2 >nul
)

REM Install service
echo [INFO] Registering service...
python "%AGENT_SCRIPT%" install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install service via pywin32.
    pause
    exit /b 1
)

REM Start service
echo [INFO] Starting service...
python "%AGENT_SCRIPT%" start
if %errorlevel% neq 0 (
    echo [WARN] Service installed but failed to start. Check Event Viewer.
)

echo.
echo [OK] Service installed successfully.
echo.
echo Management commands:
echo   Start:   net start %SERVICE_NAME%
echo   Stop:    net stop %SERVICE_NAME%
echo   Remove:  python "%AGENT_SCRIPT%" remove
echo   Status:  sc query %SERVICE_NAME%
echo.
pause
exit /b 0


:INSTALL_NSSM
echo.
echo [INFO] Installing via NSSM...
echo.

REM Find nssm
set NSSM_PATH=
where nssm >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where nssm') do set NSSM_PATH=%%i
) else if exist "C:\tools\nssm.exe" (
    set NSSM_PATH=C:\tools\nssm.exe
) else (
    echo [ERROR] NSSM not found. Download from https://nssm.cc/download
    echo         Place nssm.exe in C:\tools\ or add to PATH.
    pause
    exit /b 1
)

echo [INFO] Using NSSM: %NSSM_PATH%

REM Remove existing
"%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
timeout /t 2 >nul

REM Find python path
for /f "tokens=*" %%i in ('where python') do set PYTHON_PATH=%%i

REM Install
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%AGENT_SCRIPT%"
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "%SERVICE_DISPLAY%"
"%NSSM_PATH%" set %SERVICE_NAME% Description "Lightweight monitoring agent for ACC servers"
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%SCRIPT_DIR%"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%service_stdout.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%service_stderr.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateOnline 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 10485760

REM Start
echo [INFO] Starting service...
"%NSSM_PATH%" start %SERVICE_NAME%

echo.
echo [OK] Service installed via NSSM.
echo.
echo Management commands:
echo   Start:   "%NSSM_PATH%" start %SERVICE_NAME%
echo   Stop:    "%NSSM_PATH%" stop %SERVICE_NAME%
echo   Remove:  "%NSSM_PATH%" remove %SERVICE_NAME% confirm
echo   Status:  "%NSSM_PATH%" status %SERVICE_NAME%
echo.
pause
exit /b 0


:INSTALL_SC
echo.
echo [INFO] Installing via sc.exe (basic mode)...
echo.

REM Find python path
for /f "tokens=*" %%i in ('where python') do set PYTHON_PATH=%%i

REM Remove existing
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1
timeout /t 2 >nul

REM Create service
sc create %SERVICE_NAME% binPath= "\"%PYTHON_PATH%\" \"%AGENT_SCRIPT%\"" start= auto DisplayName= "%SERVICE_DISPLAY%"
sc description %SERVICE_NAME% "Lightweight monitoring agent for ACC servers"

REM Start
echo [INFO] Starting service...
sc start %SERVICE_NAME%

echo.
echo [OK] Service installed via sc.exe.
echo [WARN] Note: sc.exe method does not auto-restart on crash.
echo        For production use, prefer pywin32 or NSSM.
echo.
echo Management commands:
echo   Start:   sc start %SERVICE_NAME%
echo   Stop:    sc stop %SERVICE_NAME%
echo   Remove:  sc delete %SERVICE_NAME%
echo   Status:  sc query %SERVICE_NAME%
echo.
pause
exit /b 0
