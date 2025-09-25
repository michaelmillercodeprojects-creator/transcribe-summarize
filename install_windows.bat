@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Financial Transcription Tool Installer
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo.
    echo Please install Python first:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download Python 3.8 or later
    echo 3. During installation, CHECK "Add Python to PATH"
    echo 4. After installation, run this script again
    echo.
    pause
    exit /b 1
)

echo Python found! Installing requirements...
echo.

:: Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo Installing required packages...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install requirements!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setting Up OpenAI API Key
echo ========================================
echo.
echo You need an OpenAI API key to use this tool.
echo Get one from: https://platform.openai.com/api-keys
echo.
set /p API_KEY="Enter your OpenAI API key: "

if "%API_KEY%"=="" (
    echo.
    echo No API key entered. You can add it later by:
    echo 1. Creating a .env file in this folder
    echo 2. Adding: OPENAI_API_KEY=your_key_here
) else (
    echo OPENAI_API_KEY=%API_KEY% > .env
    echo.
    echo API key saved to .env file!
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run the application:
echo - Double-click "run_windows.bat" to start the GUI
echo - Or run: python run_app.py
echo.
if "%API_KEY%"=="" (
    echo Remember to add your OpenAI API key to the .env file!
    echo.
)
pause