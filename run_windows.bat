@echo off
setlocal enabledelayedexpansion
echo Starting Financial Transcription Tool...
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please run install_windows.bat first.
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo.
    echo You need an OpenAI API key to use this tool.
    echo Would you like to add it now?
    echo.
    set /p ADD_KEY="Enter your OpenAI API key (or press Enter to continue without): "
    
    if not "!ADD_KEY!"=="" (
        echo OPENAI_API_KEY=!ADD_KEY! > .env
        echo API key saved to .env file!
        echo.
    ) else (
        echo.
        echo You can add your API key later by:
        echo 1. Creating a .env file in this folder
        echo 2. Adding: OPENAI_API_KEY=your_key_here
        echo.
        echo Get your API key from: https://platform.openai.com/api-keys
        echo.
    )
    pause
)

:: Run the application
python run_app.py
pause