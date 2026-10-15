@echo off
REM Nepali Diet Recommendation System - One-Click Launcher (Windows)
title Nepali Diet Recommendation System

echo ==========================================================
echo   Starting Nepali Diet Recommendation System (DFTQC 2012)
echo ==========================================================

cd /d "%~dp0"

REM Find Python executable in virtual environment or system PATH
set "PYTHON_EXE="
if exist "%~dp0backend\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0backend\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0backend\venv\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%

echo.
echo [1/4] Running backend database migrations...
"%PYTHON_EXE%" "%~dp0backend\manage.py" migrate
if errorlevel 1 (
    echo Error running migrations.
    pause
    exit /b 1
)

echo.
echo [2/4] Seeding Nepali food database...
"%PYTHON_EXE%" "%~dp0backend\manage.py" seed_data
if errorlevel 1 (
    echo Error seeding data.
    pause
    exit /b 1
)

echo.
echo [3/4] Training Decision Tree model...
"%PYTHON_EXE%" "%~dp0backend\manage.py" train_decision_tree
if errorlevel 1 (
    echo Error training decision tree model.
    pause
    exit /b 1
)

echo.
echo [4/4] Launching Backend and Frontend servers...
start "Django Backend Server" cmd /k "cd /d "%~dp0backend" && "%PYTHON_EXE%" manage.py runserver 8000"

start "React Vite Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ==========================================================
echo   Backend running at:  http://127.0.0.1:8000/
echo   Frontend running at: http://localhost:5173/
echo ==========================================================
echo Press any key to close this launcher window (servers will continue running).
pause >nul
