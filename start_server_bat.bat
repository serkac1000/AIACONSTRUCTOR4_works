@echo off
title MIT App Inventor AIA Generator Server
color 0A

echo.
echo ========================================
echo  MIT App Inventor AIA Generator Server
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version

:: Check if Flask is installed
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Flask not found. Installing dependencies...
    echo.
    pip install flask requests
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo [INFO] Flask already installed
)

:: Check if requests is installed
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing requests library...
    pip install requests
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requests
        pause
        exit /b 1
    )
)

echo.
echo [INFO] All dependencies installed successfully!
echo [INFO] Starting server...
echo.
echo ========================================
echo  Server will start on: http://127.0.0.1:5000
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

:: Start the Flask application
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server failed to start
    echo Check if port 5000 is already in use
    echo.
)

echo.
echo Server stopped.
pause