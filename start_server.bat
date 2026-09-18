@echo off
setlocal enabledelayedexpansion
title Arohan ISDP — Campus LMS Server

:: Navigate to the directory where this batch file is located (works from anywhere)
cd /d "%~dp0"

echo ================================================================
echo   AROHAN ISDP — CAMPUS LMS SERVER LAUNCHER
echo   Institute of Management Research and Development, Shirpur
echo ================================================================
echo.
echo Current Directory: %CD%
echo Checking environment...

:: 1. Check if Python is available in PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Python detected. Starting institutional server...
    python start_server.py
    goto end
)

:: 2. If Python is not in PATH, check python in common locations or use standalone exe
if exist "dist\Arohan-LMS\Arohan-LMS.exe" (
    echo [OK] Standalone Executable found at dist\Arohan-LMS\Arohan-LMS.exe
    echo Launching Arohan Desktop Executable...
    start "" "dist\Arohan-LMS\Arohan-LMS.exe"
    goto end
)

:: 3. Check Python launcher (py)
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Python launcher detected. Starting server...
    py start_server.py
    goto end
)

echo [ERROR] Neither Python nor dist\Arohan-LMS\Arohan-LMS.exe was found!
echo Please ensure Python is installed or run the build command to generate the executable.
pause

:end
