@echo off
title AsterBot - Web Interface
echo.
echo ==========================================
echo          ASTERBOT - WEB INTERFACE
echo ==========================================
echo.
echo Starting web interface...
echo Access: http://localhost:5000
echo.
echo To stop, close this window or press Ctrl+C
echo.

cd /d "%~dp0"
python run_web.py

echo.
echo Interface closed. Press any key to exit.
pause > nul
