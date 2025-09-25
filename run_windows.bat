@echo off
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
    echo You need to create a .env file with your OpenAI API key:
    echo 1. Create a file named ".env" in this folder
    echo 2. Add this line: OPENAI_API_KEY=your_api_key_here
    echo 3. Replace "your_api_key_here" with your actual OpenAI API key
    echo.
    echo Get your API key from: https://platform.openai.com/api-keys
    echo.
    pause
)

:: Run the application
python run_app.py
pause