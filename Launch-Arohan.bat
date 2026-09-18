@echo off
title Arohan ISDP LMS Launcher
cd /d "%~dp0"

if exist "dist\Arohan-LMS\Arohan-LMS.exe" (
    cd /d "%~dp0dist\Arohan-LMS"
    start "" "Arohan-LMS.exe"
    exit /b
)

call "%~dp0start_server.bat"
