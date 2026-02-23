@echo off
REM ============================================
REM  Vatican Bot - Quick Start (Windows)
REM ============================================
REM  This script starts the Vatican bot.
REM  To stop it, press Ctrl+C in this window.
REM ============================================

title Vatican Bot Monitor

cd /d "%~dp0"

echo ==========================================
echo   Vatican Bot - Starting...
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Run the bot
python run_vatican_bot.py %*

REM If it exits, pause so the user can see the error
echo.
echo Bot has stopped. Press any key to close...
pause
