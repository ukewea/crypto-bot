@echo off
REM Crypto Trading Dashboard Startup Script (Windows)
REM This script starts both the API server and React frontend

setlocal enabledelayedexpansion

echo.
echo 🚀 Crypto Trading Dashboard Startup Script
echo ===========================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "DASHBOARD_DIR=%SCRIPT_DIR%\dashboard\crypto-dashboard"

REM Check if we're in the right directory (crypto-bot root)
if not exist "%SCRIPT_DIR%\trade_loop.py" (
    echo ❌ Error: This script must be run from the crypto-bot repository root
    echo    Expected files: trade_loop.py, asset-positions\ directory  
    echo    Current directory: %SCRIPT_DIR%
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%\asset-positions" (
    echo ❌ Error: asset-positions directory not found
    echo    Expected: %SCRIPT_DIR%\asset-positions
    pause
    exit /b 1
)

REM Check if dashboard directory exists
if not exist "%DASHBOARD_DIR%" (
    echo ❌ Error: Dashboard directory not found
    echo    Expected: %DASHBOARD_DIR%
    echo    Please make sure the dashboard is properly installed
    pause
    exit /b 1
)

REM Check if package.json exists
if not exist "%DASHBOARD_DIR%\package.json" (
    echo ❌ Error: package.json not found in dashboard directory
    echo    Expected: %DASHBOARD_DIR%\package.json
    pause
    exit /b 1
)

REM Check if node_modules exists, if not, install dependencies
if not exist "%DASHBOARD_DIR%\node_modules" (
    echo 📦 Dependencies not found. Installing...
    cd /d "%DASHBOARD_DIR%"
    call npm install
    if errorlevel 1 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
    
    REM Also install server dependencies
    if exist "server" (
        if not exist "server\node_modules" (
            echo 📦 Installing server dependencies...
            cd server
            call npm install
            if errorlevel 1 (
                echo ❌ Error: Failed to install server dependencies
                pause
                exit /b 1
            )
            cd ..
        )
    )
    cd /d "%SCRIPT_DIR%"
)

REM Count asset files
set "ASSET_COUNT=0"
for %%f in ("%SCRIPT_DIR%\asset-positions\*.json") do (
    set /a ASSET_COUNT+=1
)

if !ASSET_COUNT! equ 0 (
    echo ⚠️  Warning: No asset position files found in asset-positions\
    echo    The dashboard will show empty data until you have trading positions
) else (
    echo ✅ Found !ASSET_COUNT! asset position files
)

REM Check if custom port is requested
if not "%1"=="" (
    set "CUSTOM_PORT=%1"
    REM Basic validation - check if it's a number
    echo !CUSTOM_PORT! | findstr /r "^[0-9][0-9]*$" >nul
    if errorlevel 1 (
        echo ❌ Error: Invalid port number '%1'
        echo    Port must be a number between 1024-65535
        pause
        exit /b 1
    )
    if !CUSTOM_PORT! lss 1024 (
        echo ❌ Error: Port number too low '%1'
        echo    Port must be between 1024-65535
        pause
        exit /b 1
    )
    if !CUSTOM_PORT! gtr 65535 (
        echo ❌ Error: Port number too high '%1'  
        echo    Port must be between 1024-65535
        pause
        exit /b 1
    )
    echo 🔧 Using custom port: !CUSTOM_PORT!
)

echo.
echo 🎯 Starting Dashboard Services...
echo 📍 Script location: %SCRIPT_DIR%
echo 📍 Dashboard location: %DASHBOARD_DIR%
echo 📍 Asset positions: %SCRIPT_DIR%\asset-positions

REM Display startup information
echo.
echo 📊 Dashboard will be available at:
if not "%CUSTOM_PORT%"=="" (
    echo    🌐 Frontend: http://localhost:5173 ^(or next available port^)
    echo    🔗 API Server: http://localhost:!CUSTOM_PORT!
    echo.
    echo ⏳ Starting servers with custom port !CUSTOM_PORT!...
) else (
    echo    🌐 Frontend: http://localhost:5173 ^(or next available port^)
    echo    🔗 API Server: http://localhost:39583
    echo.
    echo ⏳ Starting servers with default ports...
)

echo 💡 Press Ctrl+C to stop both servers
echo.

REM Change to dashboard directory and start the servers
cd /d "%DASHBOARD_DIR%"

if not "%CUSTOM_PORT%"=="" (
    REM Start with custom port
    set "PORT=!CUSTOM_PORT!"
    set "VITE_API_PORT=!CUSTOM_PORT!"
    call npm run dev:port
) else (
    REM Start with default ports
    call npm run dev:full
)

pause