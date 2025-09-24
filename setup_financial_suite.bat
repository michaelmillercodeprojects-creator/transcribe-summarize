@echo off
REM Complete Financial Transcription Suite Setup
REM Includes both manual and email-automated transcription tools

echo.
echo ========================================================
echo Financial Transcription Suite - Complete Setup
echo ========================================================
echo.
echo This will install:
echo 1. Manual Financial Transcription Tool
echo 2. Email-Automated Financial Transcription Tool  
echo 3. All required dependencies
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found:
python --version

REM Check if ffmpeg is available
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ffmpeg not found in PATH
    echo ffmpeg is required for audio processing
    echo.
    echo Options to install ffmpeg:
    echo 1. Download from https://ffmpeg.org/download.html
    echo 2. Use Chocolatey: choco install ffmpeg
    echo 3. Use winget: winget install ffmpeg
    echo.
    echo Continue anyway? The tool may not work without ffmpeg.
    pause
)

REM Create directory for the tools
if not exist "%USERPROFILE%\financial-transcribe-suite" (
    mkdir "%USERPROFILE%\financial-transcribe-suite"
    echo Created directory: %USERPROFILE%\financial-transcribe-suite
)

cd /d "%USERPROFILE%\financial-transcribe-suite"

REM Install required packages
echo.
echo Installing required packages...
echo This may take a few minutes...
pip install openai python-dotenv requests yt-dlp

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

REM Download the transcription scripts
echo.
echo Downloading transcription scripts...

REM Download the transcription scripts from GitHub
curl -o transcribe_financial.py https://raw.githubusercontent.com/michaelmillercodeprojects-creator/transcribe-summarize/main/transcribe_financial.py
curl -o email_transcribe_financial.py https://raw.githubusercontent.com/michaelmillercodeprojects-creator/transcribe-summarize/main/email_transcribe_financial.py

if not exist transcribe_financial.py (
    echo ERROR: Failed to download transcribe_financial.py
    echo Please check your internet connection and try again
    echo Or manually download from GitHub repository
    pause
)

REM Create output directory
if not exist "output" (
    mkdir "output"
    echo Created output directory
)

REM Setup OpenAI API key
echo.
echo ========================================================
echo OpenAI API Key Setup
echo ========================================================
if not exist ".env" (
    echo.
    echo You need an OpenAI API key to use this tool.
    echo Get one from: https://platform.openai.com/api-keys
    echo.
    set /p api_key="Enter your OpenAI API key: "
    echo OPENAI_API_KEY=%api_key%> .env
    echo API key saved to .env file
) else (
    echo .env file already exists
    echo Checking for OpenAI API key...
    findstr "OPENAI_API_KEY" .env >nul
    if errorlevel 1 (
        echo OpenAI API key not found in .env file
        set /p api_key="Enter your OpenAI API key: "
        echo OPENAI_API_KEY=%api_key%>> .env
    ) else (
        echo OpenAI API key found in .env file
    )
)

REM Setup email integration (optional)
echo.
echo ========================================================
echo Email Integration Setup (Optional)
echo ========================================================
echo.
echo The email integration allows you to:
echo - Send audio files via email and get analysis back automatically
echo - Monitor a mailbox for audio attachments
echo - Automatically reply with financial analysis
echo.
set /p setup_email="Set up email integration? (y/n): "
if /i "%setup_email%"=="y" (
    echo.
    echo For Gmail users:
    echo 1. Enable 2-factor authentication on your Google account
    echo 2. Create an App Password specifically for this tool
    echo 3. Use the App Password below, not your regular password
    echo.
    set /p email_addr="Enter your email address: "
    set /p email_pass="Enter your email password or app password: "
    echo.
    echo EMAIL_ADDRESS=%email_addr%>> .env
    echo EMAIL_PASSWORD=%email_pass%>> .env
    echo IMAP_SERVER=imap.gmail.com>> .env
    echo SMTP_SERVER=smtp.gmail.com>> .env
    echo.
    echo Email integration configured!
)

REM Create run scripts
echo.
echo Creating run scripts...

REM Manual transcription script
(
echo @echo off
echo cd /d "%USERPROFILE%\financial-transcribe-suite"
echo echo Financial Audio Transcription Tool
echo echo.
echo python transcribe_financial.py %%*
echo if errorlevel 1 (
echo     echo.
echo     echo An error occurred. Check the messages above.
echo     pause
echo ^)
) > run_financial_transcribe.bat

REM Email monitoring script
(
echo @echo off
echo cd /d "%USERPROFILE%\financial-transcribe-suite"
echo echo Email Financial Transcription Monitor
echo echo.
echo python email_transcribe_financial.py %%*
echo if errorlevel 1 (
echo     echo.
echo     echo An error occurred. Check the messages above.
echo     pause
echo ^)
) > run_email_monitor.bat

REM Interactive launcher
(
echo @echo off
echo cd /d "%USERPROFILE%\financial-transcribe-suite"
echo :menu
echo cls
echo.
echo ========================================================
echo Financial Transcription Suite
echo ========================================================
echo.
echo Choose an option:
echo.
echo 1. Transcribe a single audio/video file
echo 2. Transcribe from YouTube URL
echo 3. Start email monitoring ^(automatic processing^)
echo 4. Setup email configuration
echo 5. View recent output files
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "
echo.
if "%%choice%%"=="1" goto single_file
if "%%choice%%"=="2" goto youtube
if "%%choice%%"=="3" goto email_monitor
if "%%choice%%"=="4" goto email_setup
if "%%choice%%"=="5" goto view_output
if "%%choice%%"=="6" goto exit
echo Invalid choice. Please try again.
pause
goto menu
echo.
:single_file
set /p file_path="Enter path to audio/video file: "
set /p email_to="Send results to email ^(optional, press Enter to skip^): "
if "%%email_to%%"=="" (
    python transcribe_financial.py --input "%%file_path%%"
^) else (
    python transcribe_financial.py --input "%%file_path%%" --email "%%email_to%%"
^)
echo.
echo Results saved to output folder
pause
goto menu
echo.
:youtube
set /p youtube_url="Enter YouTube URL: "
set /p email_to="Send results to email ^(optional, press Enter to skip^): "
if "%%email_to%%"=="" (
    python transcribe_financial.py --input "%%youtube_url%%"
^) else (
    python transcribe_financial.py --input "%%youtube_url%%" --email "%%email_to%%"
^)
echo.
echo Results saved to output folder
pause
goto menu
echo.
:email_monitor
echo Starting email monitoring...
echo Send audio files to your configured email address.
echo The tool will automatically process them and reply with analysis.
echo Press Ctrl+C to stop monitoring.
echo.
python email_transcribe_financial.py
pause
goto menu
echo.
:email_setup
python email_transcribe_financial.py --setup
pause
goto menu
echo.
:view_output
echo Recent output files:
echo.
dir /b /od output\*.txt 2^>nul
if errorlevel 1 (
    echo No output files found.
^) else (
    echo.
    set /p open_file="Enter filename to open ^(or press Enter to continue^): "
    if not "%%open_file%%"=="" (
        if exist "output\%%open_file%%" (
            notepad "output\%%open_file%%"
        ^) else (
            echo File not found.
        ^)
    ^)
^)
pause
goto menu
echo.
:exit
exit /b 0
) > "Financial Transcription Suite.bat"

REM Create desktop shortcuts
echo.
echo Creating desktop shortcuts...

REM Main launcher shortcut
copy "Financial Transcription Suite.bat" "%USERPROFILE%\Desktop\Financial Transcription Suite.bat" >nul

REM Quick transcribe shortcut
(
echo @echo off
echo cd /d "%USERPROFILE%\financial-transcribe-suite"
echo echo Quick Financial Transcription
echo echo.
echo set /p input_file="Drag and drop audio file here, then press Enter: "
echo set /p email_addr="Send results to email ^(optional^): "
echo echo.
echo echo Processing... Please wait.
echo if "%%email_addr%%"=="" (
echo     python transcribe_financial.py --input %%input_file%%
echo ^) else (
echo     python transcribe_financial.py --input %%input_file%% --email "%%email_addr%%"
echo ^)
echo echo.
echo echo Processing complete! Check the output folder.
echo pause
) > "%USERPROFILE%\Desktop\Quick Financial Transcribe.bat"

echo.
echo ========================================================
echo Setup Complete!
echo ========================================================
echo.
echo The Financial Transcription Suite has been installed to:
echo %USERPROFILE%\financial-transcribe-suite
echo.
echo Available tools:
echo.
echo 1. DESKTOP SHORTCUT: "Financial Transcription Suite"
echo    - Interactive menu with all options
echo    - Easy to use for all features
echo.
echo 2. DESKTOP SHORTCUT: "Quick Financial Transcribe"  
echo    - Drag-and-drop single file processing
echo    - Fast transcription for individual files
echo.
echo 3. COMMAND LINE TOOLS:
echo    - run_financial_transcribe.bat [options]
echo    - run_email_monitor.bat [options]
echo.
echo FEATURES:
echo - Focuses on macro themes and trade ideas
echo - Ignores filler content and pleasantries  
echo - Supports audio/video files and YouTube URLs
echo - Email integration for automated processing
echo - Results saved to output folder
echo - Optional email delivery of results
echo.
echo USAGE EXAMPLES:
echo   Local file:   python transcribe_financial.py --input "recording.mp3"
echo   YouTube:      python transcribe_financial.py --input "https://youtube.com/watch?v=..."
echo   Dropbox:      python transcribe_financial.py --input "https://dropbox.com/s/abc123/recording.mp3"
echo   Google Drive: python transcribe_financial.py --input "https://drive.google.com/file/d/abc123/view"
echo   Zoom:         python transcribe_financial.py --input "https://zoom.us/rec/share/..."
echo   With email:   python transcribe_financial.py --input "file.mp3" --email "you@email.com"
echo   Email monitor: python email_transcribe_financial.py
echo.
echo TIP: Use the desktop shortcut "Financial Transcription Suite" 
echo      for an easy interactive menu!
echo.
pause