@echo off
title Vatican Browser Agent
echo Starting Vatican Browser Agent...
echo.
echo This will open Chrome automatically when a slot is detected.
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
python backend\local_browser_agent.py
pause
