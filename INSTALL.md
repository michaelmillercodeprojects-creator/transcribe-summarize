# 🚀 Easy Installation Guide

This guide will help you install and run the Financial Transcription Tool, even if you don't have Python installed.

## 📦 Quick Installation

### Windows Users
1. **Double-click** `install_windows.bat`
2. Follow the on-screen instructions
3. If Python isn't installed, the script will guide you to install it
4. After installation, double-click `run_windows.bat` to start the app

### Mac/Linux Users
1. **Double-click** `install_mac_linux.sh` (or run in terminal)
2. Follow the on-screen instructions  
3. If Python isn't installed, the script will show you how to install it
4. After installation, double-click `run_mac_linux.sh` to start the app

### Universal Python Method
If you have Python installed:
1. **Double-click** `install.py`
2. This works on all platforms and provides detailed feedback
3. After installation, run `python run_app.py`

## 🔑 API Key Setup

After installation, you need an OpenAI API key:

1. **Get your API key**: Visit https://platform.openai.com/api-keys
2. **Create `.env` file**: In the project folder, create a file named `.env`
3. **Add your key**: Put this line in the `.env` file:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

## 🛠️ What Gets Installed

The installer will automatically install these free, open-source packages:
- `openai` - For AI transcription and analysis
- `python-dotenv` - For managing your API key securely
- `requests` - For web requests
- `yt-dlp` - For downloading audio from URLs
- `beautifulsoup4` - For web content parsing
- `reportlab` - For PDF generation (completely free, no account needed)

## ❓ Troubleshooting

### "Python not found"
- **Windows**: Download Python from python.org and check "Add Python to PATH" during installation
- **Mac**: Install via Homebrew (`brew install python`) or download from python.org
- **Linux**: Use your package manager (`sudo apt install python3 python3-pip`)

### "Installation failed"
- Check your internet connection
- On Linux/Mac: You might need development tools:
  - Mac: `xcode-select --install`
  - Ubuntu/Debian: `sudo apt install build-essential python3-dev`
  - CentOS/RHEL: `sudo yum groupinstall 'Development Tools'`

### "Module not found" errors
- Re-run the installer script
- Try: `pip install -r requirements.txt --user`

## 🎯 Ready to Use!

Once installed:
1. **GUI Mode**: Double-click the launcher script for your platform
2. **Command Line**: Run `python run_app.py` in the project folder
3. **Load audio files** or **paste YouTube URLs** to get detailed financial analysis
4. **Export to PDF** for professional reports

## 💡 No Accounts Needed!

This tool uses only free, open-source libraries. You don't need accounts for:
- ❌ ReportLab (we use the free version)
- ❌ Any PDF services
- ❌ Any transcription services beyond OpenAI

You only need:
- ✅ An OpenAI API key (pay-per-use, no monthly fees)
- ✅ Python (free)
- ✅ The packages we install (all free)

Happy analyzing! 📈