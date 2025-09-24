# Financial Audio Transcription Suite

A desktop application for transcribing and analyzing financial audio/video content using OpenAI's APIs.

## Quick Start

Launch the GUI application:
```bash
python3 run_app.py
```

Or run the GUI directly:
```bash
python3 financial_transcribe_gui.py
```

## Features

### GUI Application
- Process local audio/video files
- Process URLs from YouTube, Dropbox, Google Drive, Zoom
- Real-time processing feedback with status indicators
- Email delivery of results
- Configurable API keys and settings
- Professional institutional-style analysis output

### Financial Analysis
- AI-powered transcription using OpenAI Whisper
- GPT-4 analysis focused on investment insights
- Supporting quotes from original audio included
- Clean, actionable summaries in professional format
- HTML-formatted email reports

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Launch the GUI and configure:
- OpenAI API key in Settings > API & Email tab
- Email credentials (optional, for sending reports)
- Output email address for receiving results

### 3. Alternative: Manual Configuration
Create `.env` file:
```
OPENAI_API_KEY=your_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
OUTPUT_EMAIL=recipient@example.com
```

## Usage

### GUI Mode (Recommended)
1. Run `python3 run_app.py`
2. Click "Process File" to select audio/video files
3. Click "Process URL" to enter YouTube, Dropbox, etc. links
4. Toggle email delivery if desired
5. Watch real-time progress in the activity log

### Command Line
```bash
# Process local file
python3 transcribe_financial.py --input audio.mp3

# Process URL
python3 transcribe_financial.py --input "https://youtube.com/watch?v=..."

# Send results via email
python3 transcribe_financial.py --input audio.mp3 --email recipient@example.com
```

## Requirements

- Python 3.7 or higher
- OpenAI API key (approximately $0.006 per minute of audio)
- tkinter (usually included with Python)
- ffmpeg (for audio processing)

## Supported Formats

- **Audio Files**: MP3, WAV, M4A
- **Video Files**: MP4, MOV, AVI, WEBM, FLV
- **URLs**: YouTube, Dropbox share links, Google Drive, Zoom recordings
- **File Sources**: Local files, web URLs, sharing service links

## Output Format

The analysis provides:
- Market views and economic trends
- Trade ideas with supporting rationale
- Risk assessment and timing considerations
- Strategic takeaways for portfolio positioning
- Supporting quotes from the original audio
- Full transcript for reference

All output is saved to the `output/` directory and optionally emailed in HTML format.

## Project Structure

```
transcribe-summarize/
├── run_app.py                    # Application launcher
├── financial_transcribe_gui.py  # Main GUI application
├── transcribe_financial.py      # Core transcription engine
├── requirements.txt             # Python dependencies
├── audio/                       # Audio file storage
└── output/                      # Generated analysis reports
```

## Troubleshooting

### Common Issues
- **Python not found**: Ensure Python 3.7+ is installed and in PATH
- **tkinter not available**: Install python3-tk package on Linux
- **ffmpeg missing**: Install ffmpeg for audio processing
- **API errors**: Verify OpenAI API key is valid and has credits

### GUI Issues
- Use "Tools > Check Dependencies" to verify system requirements
- Check the activity log for detailed error information
- Try command line mode if GUI fails to start

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.7 or higher with tkinter support
- **Internet**: Required for OpenAI API calls
- **Storage**: Temporary space for audio processing
- **Memory**: 1GB+ recommended for large audio files
