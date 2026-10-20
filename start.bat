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
set HOST=0.0.0.0
set PORT=8050
set APP_MODULE=src.api.app:app

echo [INFO] Python version:
python --version
echo [INFO] Local PC Access  : http://localhost:%PORT%/landing
echo [INFO] Same Wi-Fi Access: http://192.168.0.113:%PORT%/landing
echo [INFO] Global Internet  : Run "share_online.bat" for instant public HTTPS link!
echo [INFO] API Swagger Docs : http://localhost:%PORT%/docs
echo.
echo [DEMO PERSONAS - 1-Click Quick Login on http://localhost:%PORT%/login]
echo  - Business Owner   : demo_owner@smefinance.local      / DemoPass123!
echo  - Business Manager : demo_manager@smefinance.local    / DemoPass123!
echo  - Accountant Staff : demo_accountant@smefinance.local / DemoPass123!
echo  - Sales Executive  : demo_sales@smefinance.local      / DemoPass123!
echo  - Inventory Officer: demo_inventory@smefinance.local  / DemoPass123!
echo  - Financial Auditor: demo_auditor@smefinance.local    / DemoPass123!
echo  - Super Admin HUD  : demo_superadmin@smefinance.local / DemoPass123!
echo.
echo [INFO] Launching browser in 2 seconds...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:%PORT%/landing"

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
