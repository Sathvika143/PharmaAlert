@echo off
REM Quick Setup Script for PharmaAlert

echo.
echo ========================================
echo PharmaAlert - Quick Start
echo ========================================
echo.

REM Check if venv exists
where python >nul 2>nul
if %errorlevel%==0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=py"
    ) else (
        echo ERROR: Neither Python nor py launcher found in PATH.
        echo Install Python and ensure it is available from command line.
        pause
        exit /b 1
    )
)

if not exist venv (
    echo Creating virtual environment...
    %PY_CMD% -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Starting PharmaAlert...
echo ========================================
echo.
echo Open your browser: http://127.0.0.1:5000
echo Login: admin / admin123
echo.
echo Press CTRL+C to stop
echo.

%PY_CMD% app.py

pause
