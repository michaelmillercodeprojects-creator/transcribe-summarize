@echo off
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
echo Installation Complete!
echo ========================================
echo.
echo You can now run the application:
echo - Double-click "run_app.py" to start the GUI
echo - Or run: python run_app.py
echo.
echo Make sure to:
echo 1. Create a .env file with your OpenAI API key
echo 2. Add: OPENAI_API_KEY=your_key_here
echo.
pause