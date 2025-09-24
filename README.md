# 🎯 Financial Email Transcription Suite

**Professional desktop application for automatically transcribing and analyzing financial audio content from emails, URLs, and files.**

Transform webinars, earnings calls, and financial presentations into actionable investment insights with AI-powered analysis. No technical knowledge required - just double-click to start!

## 🚀 **Quick Start - Just Double-Click!**

### **Option 1: One-Click Launch (Easiest!)**
```
📂 Double-click: run_app.py
```
**Works on all systems** - automatically finds Python and launches the GUI!

### **Option 2: Platform-Specific Launchers**
- **Windows**: Double-click `launch_gui.bat`
- **Mac/Linux**: Double-click `launch_gui.sh`

**✨ No Python setup required - launchers handle everything!**

---

## 🎛️ **GUI Application Features**

### **📧 Email Automation**
- **Intelligent Webinar Detection** - Finds audio/video content in emails automatically
- **Corporate Security URLs** - Unwraps Microsoft Defender, Proofpoint links
- **Marketing Link Following** - Processes redirect chains to find actual media
- **24/7 Monitoring** - Continuously checks for new content
- **Professional Reports** - HTML-formatted analysis sent back via email

### **🎯 Manual Processing Tools**
- **File Processing** - Drag & drop audio/video files
- **URL Processing** - YouTube, Dropbox, Google Drive, Zoom recordings
- **Real-Time Logging** - Watch processing happen live
- **Output Management** - Easy access to generated reports

### **⚙️ Smart Configuration**
- **Auto-Save Settings** - Remembers your preferences
- **Flexible Intervals** - Set custom email check frequency
- **Auto-Start Option** - Launch with service running
- **Dependency Checking** - Verifies all components work

---

## 📊 **What You Get**

### **📈 Financial Analysis Engine**
```
MACRO INVESTMENT THEMES
• Federal Reserve policy shift indicating potential rate cuts in Q2
• Emerging market opportunities in Asian tech sector  
• Dollar weakness creating commodity investment tailwinds

TRADE ANALYSIS & OPPORTUNITIES  
• Long XLE (Energy ETF) - Supply constraints + geopolitical factors
• Short duration bonds - Rate volatility expected
• Defensive positioning in REIT sector with focus on data centers

STRATEGIC TAKEAWAYS
• Position for reflation trade with 60/40 equity/commodity allocation
• Hedge currency exposure in international holdings
• Monitor Fed minutes for timing on duration trades
```

### **🎵 Supports All Major Platforms**
- **✅ YouTube** - Full video/audio extraction
- **✅ Dropbox** - Direct share link processing  
- **✅ Google Drive** - Public share links
- **✅ Zoom** - Recording links
- **✅ Local Files** - MP3, MP4, WAV, M4A, MOV, AVI, WEBM
- **✅ Email Attachments** - Automatic processing

---

## 🎯 **Perfect For**

### **Investment Professionals**
- Earnings calls and analyst presentations
- Fed meetings and policy discussions
- Market outlook and strategy webinars
- Corporate board meetings

### **Anyone Who Needs**  
- **No Technical Skills** - GUI handles everything
- **Email Integration** - Send links, get analysis back
- **Professional Reports** - Clean, actionable insights
- **24/7 Operation** - Continuous monitoring

---

## ⚡ **How It Works**

### **1. Setup (One Time)**
1. Double-click `run_app.py` to launch
2. Enter your email address in Settings
3. Set check interval (default: 5 minutes)
4. Save settings

### **2. Email Processing**
- Send webinar links to your configured email
- AI detects financial content automatically
- Transcribes and analyzes in the background
- Sends back professional HTML report

### **3. Manual Processing**
- **Tools → Process File**: Upload audio/video files
- **Tools → Process URL**: Enter YouTube, Dropbox, etc. links
- **Test Once**: Run single email check

### **4. Monitor & Manage**
- Real-time activity log shows all processing
- Start/Stop/Restart service as needed
- View output files with one click

---

## 🔧 **Installation & Setup**

### **Automatic Installation (Windows)**
```bash
# Download and run complete installer
setup_financial_suite.bat
```

### **Manual Setup (All Platforms)**
```bash
# 1. Install Python dependencies
pip install openai python-dotenv requests yt-dlp beautifulsoup4

# 2. Set up OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# 3. Optional - Email credentials (for automation)
echo "EMAIL_ADDRESS=your_email@gmail.com" >> .env
echo "EMAIL_PASSWORD=your_app_password" >> .env

# 4. Launch GUI
python3 run_app.py
```

### **🔑 API Requirements**
- **OpenAI API Key** (get from: https://platform.openai.com/api-keys)
- **Cost**: ~$0.006 per minute of audio (very affordable)
- **Gmail App Password** (optional, for email automation)

---

## 📁 **Project Structure**

```
Financial-Transcription-Suite/
├── 🚀 run_app.py                    # One-click launcher
├── 🖥️ financial_transcribe_gui.py   # Main GUI application  
├── 📧 email_transcribe_financial.py # Email automation engine
├── 🎵 transcribe_financial.py       # Core transcription tool
├── 📋 LAUNCH_GUIDE.md               # Complete launcher guide
├── 🎛️ GUI_README.md                 # GUI usage instructions
├── 🔗 LINK_SUPPORT.md               # File sharing platforms
└── 📊 output/                       # Generated reports
```

---

## 🛟 **Support & Troubleshooting**

### **Common Issues**
| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3 with PATH option |
| "tkinter not available" | Install `python3-tk` package |
| Email not working | Verify Gmail app password & 2FA |
| GUI won't start | Try: `python3 financial_transcribe_gui.py` |

### **Get Help**
- **📖 Documentation**: Check GUI_README.md and LAUNCH_GUIDE.md  
- **🔧 Dependencies**: Use "Tools → Check Dependencies" in GUI
- **📝 Logs**: Activity log shows detailed processing information
- **🆘 Manual**: Try command line if GUI fails

---

## 🎉 **Key Benefits**

### **🎯 For Non-Technical Users**
- **No Command Line** - Complete GUI interface
- **Auto-Detection** - Finds Python installations automatically  
- **One-Click Launch** - Double-click to start
- **Professional Results** - Investment-grade analysis

### **🔧 For Power Users**
- **24/7 Automation** - Continuous email monitoring
- **Advanced Processing** - Handles large files, complex URLs
- **Corporate Compatible** - Works with security URLs
- **Service Management** - systemd, screen sessions

### **� For Everyone**
- **Cost Effective** - Pennies per hour of audio
- **Time Saving** - Minutes instead of hours for analysis
- **Professional Output** - Clean, actionable reports
- **Flexible Input** - Files, URLs, emails, attachments

---

**Transform your financial audio into actionable insights - no technical knowledge required!** 🚀

**Just double-click `run_app.py` and start processing financial content immediately.**
