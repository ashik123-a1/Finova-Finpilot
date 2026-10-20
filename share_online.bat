@echo off
title SME Finance Copilot - Live Online Sharing
cd /d "%~dp0"

echo ==============================================================================
echo                SME FINANCE COPILOT — LIVE ONLINE SHARING
echo ==============================================================================
echo.
echo [INFO] Starting application server and generating public internet link...
echo.

:: 1. Check for Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: venv
    call venv\Scripts\activate.bat
)

:: 2. Verify Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please ensure Python 3.10+ is installed and added to PATH.
    echo.
    pause
    exit /b 1
)

:: 3. Run the Online Sharing Runner
python scripts\share_online.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Server stopped.
    pause
)
