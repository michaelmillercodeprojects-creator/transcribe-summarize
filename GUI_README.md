# Financial Email Transcription - GUI Application

## 🚀 Easy-to-Use Desktop Application

A user-friendly desktop application for automatically monitoring emails and transcribing financial webinars and audio content.

## 📱 Features

✅ **Simple GUI Interface** - No command line needed!  
✅ **One-Click Start/Stop** - Easy service control  
✅ **Real-Time Logging** - See what's happening live  
✅ **Auto-Start Option** - Launch with service running  
✅ **Settings Management** - Configure email and intervals  
✅ **Manual Processing** - Process files and URLs directly  
✅ **Built-in Help** - Documentation and troubleshooting  

## 🏃‍♂️ Quick Start

### Windows Users:
1. Double-click `launch_gui.bat`
2. The GUI application will open

### Mac/Linux Users:
1. Double-click `launch_gui.sh` or run in terminal:
   ```bash
   ./launch_gui.sh
   ```

### Direct Python Launch:
```bash
python3 financial_transcribe_gui.py
```

## 🎛️ How to Use

### 1. **Setup** (First Time)
- Enter your email address in the Settings panel
- Set your preferred check interval (default: 300 seconds)
- Click "Save Settings"

### 2. **Start Monitoring**
- Click the "Start Service" button
- Status will show "Running" in green
- Watch the Activity Log for real-time updates

### 3. **Manual Processing**
- **Test Once**: Run a single email check
- **Tools → Process File**: Transcribe a local audio/video file
- **Tools → Process URL**: Transcribe from a web URL

### 4. **Monitor Activity**
- Activity Log shows all service activity
- Status bar shows latest activity
- Green status = Service running
- Red status = Service stopped

## 🔧 GUI Controls

### Service Control Panel:
- **Start Service**: Begin email monitoring
- **Stop Service**: Stop email monitoring  
- **Restart**: Restart the service
- **Test Once**: Run single check without starting service

### Settings Panel:
- **Email**: Your email address for monitoring
- **Check Interval**: How often to check for emails (60-3600 seconds)
- **Auto-start**: Automatically start service when GUI opens
- **Save Settings**: Save your configuration

### Menu Options:
- **File → Open Output Folder**: View generated transcriptions
- **Tools → Process File**: Transcribe local files
- **Tools → Process URL**: Transcribe from URLs
- **Tools → Check Dependencies**: Verify all components
- **Help → About**: Application information
- **Help → Documentation**: Detailed usage guide

## 📁 Output Files

Transcriptions are saved to the `output/` folder with:
- Original transcript text
- Financial analysis and insights
- Formatted for easy reading

## 🛠️ Troubleshooting

### Service Won't Start:
1. Check that `email_transcribe_financial.py` exists
2. Use **Tools → Check Dependencies**
3. Review Activity Log for error messages

### No Emails Processed:
1. Verify email settings are correct
2. Check that emails contain audio/video links
3. Use "Test Once" to check manually

### GUI Doesn't Open:
1. Ensure Python 3 is installed
2. Run from command line to see error messages:
   ```bash
   python3 financial_transcribe_gui.py
   ```

## 🔄 Auto-Start Setup

To have the service start automatically:
1. Check "Auto-start service on launch" in Settings
2. Save Settings
3. Next time you open the GUI, service will start automatically

## 💾 Configuration

Settings are automatically saved to `gui_config.json` including:
- Email address
- Check interval
- Auto-start preference
- Window size and position

## 📋 System Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- All dependencies from the main transcription service

## 🎯 Perfect For:

- **Non-technical users** who want a simple interface
- **Desktop environments** where GUI is preferred
- **Monitoring scenarios** where you want visual feedback
- **Testing and debugging** with real-time logs
- **Manual processing** of individual files/URLs

## 🚀 Advanced Features

- **Background Processing**: Service runs independently
- **Thread Safety**: GUI remains responsive during processing
- **Error Recovery**: Automatic restart on service failure
- **Resource Monitoring**: Built-in process management
- **Extensible**: Easy to add new features

---

**Easy to use, powerful, and reliable!** 🎉