@echo off
title Print Recovery
cd /d "%~dp0"

REM Prefer the standalone executable if it exists
if exist "PrintRecovery.exe" (
    start "" "PrintRecovery.exe"
    exit /b 0
)

REM Fallback: run from source with Python (development / portable folder)
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python was not found.
    echo.
    echo Option 1: Install the finished PrintRecovery-Setup.exe
    echo Option 2: Install Python 3.11+ from https://www.python.org
    echo           (tick "Add python.exe to PATH") then run this again.
    pause
    exit /b 1
)

set PRINT_RECOVERY_HOST=127.0.0.1
set PRINT_RECOVERY_PORT=5173
if not exist "data" mkdir data
if not exist "outputs" mkdir outputs

echo Starting Print Recovery on http://127.0.0.1:5173
echo Close this window to stop the application.
echo.
python app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo The application exited with an error.
    pause
)
