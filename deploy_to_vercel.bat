@echo off
REM Deploy Frontend to Vercel (Windows)
REM This script prepares and pushes the frontend to GitHub for Vercel deployment

echo =========================================
echo HYDRA Monitor - Vercel Deployment
echo =========================================
echo.

REM Check if we're in the right directory
if not exist "frontend" (
    echo Error: frontend directory not found
    echo Please run this script from the project root
    exit /b 1
)

REM Navigate to frontend
cd frontend

echo Step 1: Installing dependencies...
call npm install

echo.
echo Step 2: Building frontend...
call npm run build

if errorlevel 1 (
    echo Build failed! Please fix errors and try again.
    exit /b 1
)

echo.
echo Build successful!
echo.

REM Check if git is initialized
if not exist ".git" (
    echo Step 3: Initializing git repository...
    git init
    git branch -M main
) else (
    echo Git repository already initialized
)

REM Check if remote exists
git remote | findstr "origin" >nul
if errorlevel 1 (
    echo Step 4: Adding GitHub remote...
    git remote add origin https://github.com/killmongerinheret-beep/bot-front.git
) else (
    echo GitHub remote already configured
)

echo.
echo Step 5: Committing changes...
git add .
git commit -m "Deploy to Vercel - %date% %time%" 2>nul || echo No changes to commit

echo.
echo Step 6: Pushing to GitHub...
git push -u origin main --force

echo.
echo =========================================
echo DEPLOYMENT COMPLETE!
echo =========================================
echo.
echo Next steps:
echo 1. Go to https://vercel.com
echo 2. Import project: killmongerinheret-beep/bot-front
echo 3. Add environment variable:
echo    NEXT_PUBLIC_API_URL=http://151.25.69.162:8000/api/v1
echo 4. Deploy!
echo.
echo Your frontend will be live at:
echo https://bot-front-xxx.vercel.app
echo.
echo =========================================

cd ..
pause
