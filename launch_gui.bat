@echo off
REM Financial Email Transcription - Easy Launcher (Windows)
REM This script launches the GUI application and finds Python automatically

setlocal enabledelayedexpansion

echo Starting Financial Email Transcription GUI...
echo ===============================================

REM Function to find Python executable
set "PYTHON_CMD="

REM Common Python locations to check
set "PYTHON_PATHS=python python3 py"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Python39\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Python310\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Python311\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Python312\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\ProgramData\Anaconda3\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\Anaconda3\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Users\%USERNAME%\Miniconda3\python.exe"

REM Check each Python path
for %%p in (!PYTHON_PATHS!) do (
    %%p --version >nul 2>&1
    if not errorlevel 1 (
        REM Check if it's Python 3
        %%p -c "import sys; exit(0 if sys.version_info[0] >= 3 else 1)" >nul 2>&1
        if not errorlevel 1 (
            echo Found Python 3 at: %%p
            set "PYTHON_CMD=%%p"
            goto :found_python
        )
    )
)

REM Try Windows Python Launcher
py -3 --version >nul 2>&1
if not errorlevel 1 (
    echo Found Python 3 via py launcher
    set "PYTHON_CMD=py -3"
    goto :found_python
)

:python_not_found
echo ❌ Error: Could not find Python 3 installation
echo.
echo Please install Python 3 from one of these sources:
echo   • Official Python: https://www.python.org/downloads/
echo   • Microsoft Store: Search for "Python 3"
echo   • Anaconda: https://www.anaconda.com/products/distribution
echo.
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:found_python
REM Check if GUI script exists
if not exist "financial_transcribe_gui.py" (
    echo ❌ Error: financial_transcribe_gui.py not found
    echo Please ensure all files are in the correct location: %CD%
    pause
    exit /b 1
)

REM Check tkinter availability
echo Checking GUI dependencies...
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: tkinter (GUI library) is not available
    echo.
    echo tkinter should be included with Python on Windows
    echo Try reinstalling Python with "tcl/tk and IDLE" option checked
    echo.
    pause
    exit /b 1
)

REM Launch the GUI application
echo ✅ All dependencies found
echo 🚀 Launching GUI application...
echo.

%PYTHON_CMD% financial_transcribe_gui.py

echo.
echo Application closed.
pause