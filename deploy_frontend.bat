@echo off
echo 🚀 Deploying Multi-Tenant Dashboard to hydrasnipe.it
echo ==================================================

REM Step 1: Build frontend for production
echo 📦 Building frontend for production...
cd frontend

REM Install dependencies
echo Installing dependencies...
call npm install

REM Build for production
echo Building static files...
call npm run build

REM Check if build was successful
if %errorlevel% equ 0 (
    echo ✅ Frontend build successful!
    echo.
    echo 📁 Static files ready in: frontend/out/
    echo.
    echo 🎯 NEXT STEPS:
    echo 1. Upload all files from 'frontend/out/' folder to hydrasnipe.it
    echo 2. Replace existing files in your web server directory
    echo 3. Test: https://hydrasnipe.it/
    echo.
    echo 📋 Files to upload:
    dir out\
    echo.
    echo 🔧 Backend is already configured for hydrasnipe.it
    echo ✅ CORS settings updated
    echo ✅ Port 8000 exposed publicly
    echo.
    echo 🧪 Test backend access:
    echo curl http://151.25.69.162:8000/api/v1/agencies/
    echo.
    echo 📁 Upload these files to hydrasnipe.it:
    echo - All contents of frontend\out\ folder
    echo - Replace existing files in public_html or www folder
) else (
    echo ❌ Frontend build failed!
    pause
    exit /b 1
)

pause