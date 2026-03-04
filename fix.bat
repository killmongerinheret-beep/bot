@echo off
echo ========================================
echo Vatican Bot - Quick Fix
echo ========================================
echo.

echo Step 1: Restarting worker...
docker-compose restart worker_vatican
echo Done!
echo.

echo Step 2: Waiting 15 seconds...
timeout /t 15 /nobreak
echo.

echo Step 3: Checking logs...
docker-compose logs --tail=30 worker_vatican
echo.

echo Step 4: Triggering check...
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; orchestrate_all_tasks()"
echo.

echo ========================================
echo Fix Complete!
echo ========================================
echo.
echo Next: Wait 2-3 minutes, then check:
echo   1. Backend API: http://localhost:8000/api/tasks/
echo   2. Dashboard: https://bot-pl2x.vercel.app/
echo.
echo To monitor logs: docker-compose logs -f worker_vatican
echo.
pause
