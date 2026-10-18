@echo off
title SME Finance Copilot - Server Runner
cd /d "%~dp0"

echo ==============================================================================
echo                SME FINANCE COPILOT - AUTONOMOUS AI PORTAL
echo ==============================================================================
echo.

:: 1. Check for Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: venv
    call venv\Scripts\activate.bat
)

:: 2. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please ensure Python 3.10+ is installed and added to PATH.
    echo.
    pause
    exit /b 1
)

:: 3. Server Configuration
set HOST=127.0.0.1
set PORT=8050
set APP_MODULE=src.api.app:app

echo [INFO] Python version:
python --version
echo [INFO] Target Server : http://%HOST%:%PORT%
echo [INFO] Login Portal  : http://%HOST%:%PORT%/login
echo [INFO] Documentation : http://%HOST%:%PORT%/docs
echo.
echo [DEMO PERSONAS]
echo  - Store Owner  : demo_owner  / demo12345 or 1-Click quick login
echo  - Accountant   : demo_accountant / password123
echo  - Cashier      : demo_cashier    / password123
echo  - Bank Auditor : demo_auditor    / password123
echo.
echo [INFO] Launching browser in 2 seconds...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://%HOST%:%PORT%/login"

echo ==============================================================================
echo  Server is running! Press CTRL+C in this terminal window to stop the server.
echo ==============================================================================
echo.

python -m uvicorn %APP_MODULE% --host %HOST% --port %PORT%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server terminated with error code %errorlevel%.
    pause
)
