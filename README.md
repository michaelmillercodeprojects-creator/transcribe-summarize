# Financial Transcription Suite 🎤💰

A specialized audio transcription and financial analysis tool that focuses on extracting macro themes and trade ideas from financial conversations, earnings calls, and trading discussions.

## 🎯 Key Features

**Financial Focus:**
- **Verbatim Transcription** - Captures exactly what was said
- **Macro Themes Extraction** - Economic trends, market conditions, geopolitical impacts
- **Trade Ideas Analysis** - Specific stocks, entry/exit points, price targets, risk management
- **Filters Out Fluff** - Ignores pleasantries, filler words, off-topic discussions

**Large File Support:**
- **File Sharing Links** - Dropbox, Google Drive, Zoom recordings, YouTube
- **No Size Limits** - Process multi-GB files via sharing links  
- **Email Integration** - Send links via email, get analysis back automatically
- **Progress Tracking** - Real-time download and processing updates

## 🚀 Quick Start

### Windows Installation
1. Download and run `setup_financial_suite.bat`
2. Enter your OpenAI API key when prompted
3. Use the desktop shortcuts or command line

### Manual Installation
```bash
# Install dependencies
pip install openai python-dotenv requests yt-dlp

# Set up API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Run transcription
python transcribe_financial.py --input "your-file-or-link"
```

## 💡 Usage Examples

### Local Files
```bash
python transcribe_financial.py --input "earnings_call.mp3"
```

### Sharing Links
```bash
# Dropbox
python transcribe_financial.py --input "https://dropbox.com/s/abc123/call.mp3?dl=0"

# Google Drive  
python transcribe_financial.py --input "https://drive.google.com/file/d/1abc123/view"

# Zoom Recording
python transcribe_financial.py --input "https://zoom.us/rec/share/xyz789"
```

### Email Integration
```bash
# Setup email monitoring
python email_transcribe_financial.py --setup

# Start monitoring (auto-processes emailed links)
python email_transcribe_financial.py
```

### With Email Results
```bash
python transcribe_financial.py --input "file.mp3" --email "you@email.com"
```

## 📊 Output Format

The tool generates focused financial analysis:

```
## MACRO THEMES
• Economic outlook and Fed policy impacts
• Sector rotation themes and cyclical trends  
• Geopolitical events affecting markets

## TRADE IDEAS
• XYZ Corp (NYSE: XYZ) - Target $150, Stop $120
• Technology sector overweight recommendation
• Duration trade: Long 10-year treasuries

## KEY TAKEAWAYS
• "Expecting 25bp rate cut by December" - Speaker A
• Strong conviction on energy sector outperformance
• Risk-off positioning recommended for Q4
```

## 🔗 Supported Platforms

- **Dropbox** - Automatic link conversion (`?dl=0` → `?dl=1`)
- **Google Drive** - Direct download URL generation
- **Zoom Recordings** - Cloud recording processing
- **YouTube** - Audio extraction from videos
- **OneDrive, Box, WeTransfer** - Basic support

## 📧 Email Workflow

1. **Send** sharing link to your configured email address
2. **Tool automatically** extracts link, downloads file, processes audio
3. **Receive** financial analysis via email reply with:
   - Focused summary (macro themes + trade ideas)
   - Complete verbatim transcript
   - Timestamp and source information

## 📁 Project Structure

```
transcribe_financial.py          # Main transcription tool
email_transcribe_financial.py    # Email automation
setup_financial_suite.bat        # Windows installer
LINK_SUPPORT.md                  # Detailed platform guide
```

## ⚙️ Configuration

Create `.env` file:
```
OPENAI_API_KEY=your-openai-key
EMAIL_ADDRESS=your-email@gmail.com  # For email integration
EMAIL_PASSWORD=your-app-password    # Gmail app password
```

## 🎯 Perfect For

- **Earnings Calls** - Extract guidance and margin commentary
- **Trading Discussions** - Capture specific trade recommendations  
- **Economic Briefings** - Identify macro themes and policy impacts
- **Investment Research** - Process long-form financial content
- **Team Meetings** - Share analysis automatically via email

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- ffmpeg (for audio processing)
- Optional: Email account for automation

## 🤝 Contributing

Pull requests welcome! See `CONTRIBUTING.md` for guidelines.

## 📄 License

MIT License - see `LICENSE` file for details.
