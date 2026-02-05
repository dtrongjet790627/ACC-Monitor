@echo off
title ACC Monitor System Launcher
echo ====================================
echo   ACC Monitor System - Starting...
echo ====================================

:: Start Backend
echo [1/2] Starting Backend Server...
cd /d D:\TechTeam\Projects\ACC-Monitor\backend
start "ACC-Monitor Backend" cmd /k "venv\Scripts\activate && python run.py"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start Frontend
echo [2/2] Starting Frontend Server...
cd /d D:\TechTeam\Projects\ACC-Monitor\frontend
start "ACC-Monitor Frontend" cmd /k "npm run dev"

echo ====================================
echo   System Started!
echo   Backend:  http://localhost:5002
echo   Frontend: http://localhost:3000
echo ====================================

:: Open browser after 5 seconds
timeout /t 5 /nobreak >nul
start http://localhost:3000

exit
