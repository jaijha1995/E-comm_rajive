@echo off
title Celery Worker & Beat Launcher

echo ============================================
echo     Starting Celery Worker and Beat
echo ============================================
echo.

REM ---- Start Celery Worker ----
echo Starting Celery Worker...
start "Celery Worker" cmd /k "celery -A restserver worker --pool=eventlet -c 1000 --loglevel=info"

REM ---- Start Celery Beat ----
echo Starting Celery Beat...
start "Celery Beat" cmd /k "celery -A restserver beat --loglevel=info"

echo.
echo ============================================
echo  Celery Worker and Beat are now running
echo ============================================
echo Press any key to close this launcher window...
pause > nul
