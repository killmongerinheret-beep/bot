@echo off
echo ==========================================
echo Starting ngrok tunnel for backend
echo ==========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X ngrok is not installed
    echo.
    echo Please install ngrok:
    echo   1. Go to: https://ngrok.com/download
    echo   2. Download for Windows
    echo   3. Extract and add to PATH
    echo.
    pause
    exit /b 1
)

echo [OK] ngrok is installed
echo.

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:8000/api/v1/tasks/ >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Backend is not running on port 8000
    echo.
    echo Please start your backend first:
    echo   docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo [OK] Backend is running on port 8000
echo.

echo ==========================================
echo Starting ngrok tunnel...
echo ==========================================
echo.
echo IMPORTANT:
echo   1. Copy the HTTPS URL from below
echo   2. Go to Vercel Dashboard
echo   3. Settings -^> Environment Variables
echo   4. Set: NEXT_PUBLIC_API_URL = ^<ngrok-url^>/api/v1
echo   5. Redeploy your frontend
echo.
echo Press Ctrl+C to stop the tunnel
echo.

REM Start ngrok
ngrok http 8000
