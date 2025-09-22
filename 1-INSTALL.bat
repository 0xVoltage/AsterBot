@echo off
chcp 65001 > nul
title AsterBot - Automatic Installer

cls
echo.
echo ==========================================
echo     ASTERBOT - AUTOMATIC INSTALLER
echo ==========================================
echo.
echo This installer will:
echo - Check if Python is installed
echo - Install all dependencies
echo - Prepare the bot for use
echo.

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo X ERROR: Python not found!
    echo.
    echo Please install Python 3.8 or higher:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During Python installation,
    echo check the option "Add Python to PATH"
    echo.
    pause
    exit
)

echo Python found! Continuing installation...
echo.

:: Run the Python installer
echo Running automatic installation...
python install.py

if errorlevel 1 (
    echo.
    echo X Error during installation!
    echo.
    echo Try running as administrator:
    echo - Right click on this file
    echo - Select "Run as administrator"
    echo.
    pause
    exit
)

echo.
echo ==========================================
echo       INSTALLATION COMPLETED!
echo ==========================================
echo.
echo Now you can:
echo 1. Double click on "START_ASTERBOT.bat"
echo 2. Or run "python run_web.py"
echo.
echo The bot will open at: http://localhost:5000
echo.

pause