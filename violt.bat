@echo off
REM Windows Batch Script for Violt Core Lite
REM This script provides a convenient way to manage Violt Core Lite on Windows

setlocal enabledelayedexpansion

REM Set default paths
set "INSTALL_DIR=%ProgramFiles%\VioltCoreLite"
set "DATA_DIR=%ProgramData%\VioltCoreLite"
set "CONFIG_DIR=%DATA_DIR%\config"
set "LOG_DIR=%DATA_DIR%\logs"
set "DB_DIR=%DATA_DIR%\db"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.11 or higher from https://www.python.org/downloads/
    exit /b 1
)

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    exit /b 1
)

REM Parse command line arguments
if "%1"=="" goto :usage
if "%1"=="install" goto :install
if "%1"=="uninstall" goto :uninstall
if "%1"=="start" goto :start
if "%1"=="stop" goto :stop
if "%1"=="restart" goto :restart
if "%1"=="status" goto :status
if "%1"=="help" goto :usage
goto :usage

:install
    echo Installing Violt Core Lite...
    
    REM Check if already installed
    if exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is already installed.
        echo To reinstall, please uninstall first.
        exit /b 1
    )
    
    REM Run the Python installer script
    python "%~dp0windows_install.py" %2 %3 %4 %5 %6 %7 %8 %9
    if %ERRORLEVEL% NEQ 0 (
        echo Installation failed.
        exit /b 1
    )
    
    echo Installation completed successfully.
    goto :eof

:uninstall
    echo Uninstalling Violt Core Lite...
    
    REM Check if installed
    if not exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is not installed.
        exit /b 1
    )
    
    REM Run the Python uninstaller script
    python "%INSTALL_DIR%\uninstall.py"
    if %ERRORLEVEL% NEQ 0 (
        echo Uninstallation failed.
        exit /b 1
    )
    
    echo Uninstallation completed successfully.
    goto :eof

:start
    echo Starting Violt Core Lite service...
    
    REM Check if installed
    if not exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is not installed.
        exit /b 1
    )
    
    REM Start the service
    sc start VioltCoreLite
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to start service.
        echo Trying alternative method...
        python "%INSTALL_DIR%\backend\windows_service.py" start
    ) else (
        echo Service started successfully.
    )
    goto :eof

:stop
    echo Stopping Violt Core Lite service...
    
    REM Check if installed
    if not exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is not installed.
        exit /b 1
    )
    
    REM Stop the service
    sc stop VioltCoreLite
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to stop service.
        echo Trying alternative method...
        python "%INSTALL_DIR%\backend\windows_service.py" stop
    ) else (
        echo Service stopped successfully.
    )
    goto :eof

:restart
    echo Restarting Violt Core Lite service...
    
    REM Check if installed
    if not exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is not installed.
        exit /b 1
    )
    
    REM Restart the service
    sc stop VioltCoreLite
    timeout /t 5 /nobreak >nul
    sc start VioltCoreLite
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to restart service.
        echo Trying alternative method...
        python "%INSTALL_DIR%\backend\windows_service.py" restart
    ) else (
        echo Service restarted successfully.
    )
    goto :eof

:status
    echo Checking Violt Core Lite service status...
    
    REM Check if installed
    if not exist "%INSTALL_DIR%\backend\windows_service.py" (
        echo Violt Core Lite is not installed.
        exit /b 1
    )
    
    REM Check service status
    sc query VioltCoreLite
    goto :eof

:usage
    echo.
    echo Violt Core Lite Management Script
    echo.
    echo Usage:
    echo   violt.bat install [options]   - Install Violt Core Lite
    echo   violt.bat uninstall           - Uninstall Violt Core Lite
    echo   violt.bat start               - Start the service
    echo   violt.bat stop                - Stop the service
    echo   violt.bat restart             - Restart the service
    echo   violt.bat status              - Check service status
    echo   violt.bat help                - Show this help message
    echo.
    echo Install options:
    echo   --install-dir PATH            - Specify installation directory
    echo   --data-dir PATH               - Specify data directory
    echo   --no-service                  - Don't install as a Windows service
    echo   --no-shortcuts                - Don't create shortcuts
    echo.
    goto :eof

endlocal
