@echo off
setlocal enabledelayedexpansion
title Arohan ISDP — Campus LMS Platform Launcher
color 0b

:: 1. Navigate to directory where this batch file is located
cd /d "%~dp0"

echo ======================================================================
echo   AROHAN ISDP — INSTITUTIONAL CAMPUS LMS LAUNCHER
echo   RC Patel Educational Trust's IMRD, Shirpur
echo ======================================================================
echo.

:: 2. Detect Python installation
set "PYTHON_CMD="

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
    goto python_found
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=py"
    goto python_found
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python3"
    goto python_found
)

:: Search common Windows installation paths
for /d %%I in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%I\python.exe" (
        set "PYTHON_CMD=%%I\python.exe"
        goto python_found
    )
)

for /d %%I in ("C:\Python3*") do (
    if exist "%%I\python.exe" (
        set "PYTHON_CMD=%%I\python.exe"
        goto python_found
    )
)

for /d %%I in ("%ProgramFiles%\Python3*") do (
    if exist "%%I\python.exe" (
        set "PYTHON_CMD=%%I\python.exe"
        goto python_found
    )
)

:: Python not found
echo [ERROR] Python 3 was not detected on this system!
echo Arohan LMS requires Python 3.10 or higher.
echo.
echo Please download and install Python from:
echo   https://www.python.org/downloads/
echo.
echo *** CRITICAL: Check the box "Add python.exe to PATH" during setup! ***
echo.
set /p OPEN_BROWSER="Would you like to open the Python download page now? (Y/N): "
if /i "%OPEN_BROWSER%"=="Y" (
    start https://www.python.org/downloads/
)
pause
exit /b 1

:python_found
echo [OK] Python runtime detected: %PYTHON_CMD%
%PYTHON_CMD% --version

:: 3. Setup Virtual Environment (.venv) for portability
set "PYTHON_EXEC=%PYTHON_CMD%"
if exist ".venv\Scripts\python.exe" (
    echo [OK] Using virtual environment in .venv
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
    goto check_deps
)

echo [INFO] Creating virtual environment in .venv ...
%PYTHON_CMD% -m venv .venv >nul 2>nul
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual environment created successfully.
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
) else (
    echo [WARN] Virtual environment creation skipped. Using system Python.
)

:check_deps
:: 4. Verify & Install Python Dependencies
echo [INFO] Checking platform dependencies...
"%PYTHON_EXEC%" -c "import fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, pydantic_settings, jwt, bcrypt, httpx" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] All Python requirements are satisfied.
    goto check_storage
)

echo.
echo ======================================================================
echo   DOWNLOADING AND INSTALLING REQUIRED PACKAGES
echo   This happens only on first setup. Please wait a moment...
echo ======================================================================
"%PYTHON_EXEC%" -m pip install --upgrade pip
if exist "requirements.txt" (
    "%PYTHON_EXEC%" -m pip install -r requirements.txt
) else (
    "%PYTHON_EXEC%" -m pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic pydantic-settings email-validator python-multipart PyJWT bcrypt httpx pytest pytest-asyncio pywebview
)

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    echo Please verify your internet connection and try running again.
    pause
    exit /b 1
)
echo [OK] All dependencies successfully installed.

:check_storage
:: 5. Ensure Storage Directories Exist
if not exist "local_storage" mkdir "local_storage"
if not exist "local_storage\assignments" mkdir "local_storage\assignments"
if not exist "local_storage\submissions" mkdir "local_storage\submissions"
if not exist "local_storage\resources" mkdir "local_storage\resources"
if not exist "local_storage\backups" mkdir "local_storage\backups"
if not exist "local_storage\temp" mkdir "local_storage\temp"
if not exist "local_storage\logs" mkdir "local_storage\logs"

:: 6. Verify Frontend Distribution
if exist "frontend\dist\index.html" goto launch_server

echo [INFO] Frontend build missing. Checking for Node.js...
where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Building frontend distribution package...
    cd frontend
    call npm install
    call npm run build
    cd ..
) else (
    echo [WARN] Node.js not detected and frontend\dist\index.html missing.
)

:launch_server
:: 7. Launch Arohan Server
echo.
echo ======================================================================
echo   STARTING AROHAN ISDP SERVER
echo ======================================================================
"%PYTHON_EXEC%" start_server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [INFO] Server stopped.
    pause
)
