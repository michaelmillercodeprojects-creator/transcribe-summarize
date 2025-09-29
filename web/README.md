# Financial Transcription Web Application

A modern web-based interface for financial audio transcription and analysis using OpenAI Whisper and GPT-4.

## Features

- **File Upload**: Support for MP3, WAV, M4A, MP4, MOV, AVI, WEBM, FLV, MKV files (up to 500MB)
- **URL Processing**: Direct processing of YouTube, Vimeo, Dropbox, Google Drive URLs
- **Real-time Progress**: Live updates during transcription and analysis
- **Financial Analysis**: GPT-4 powered analysis focused on market insights and trade ideas
- **Email Reports**: Optional HTML email delivery with PDF attachments
- **Professional Interface**: Clean, responsive design with Bootstrap 5
- **API Key Management**: Secure configuration through web interface

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Navigate to the web directory:**
   ```bash
   cd web
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your OpenAI API key:**
   - Start the application (see below)
   - Go to Settings in the web interface
   - Enter your OpenAI API key
   - Save settings

4. **Start the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open http://localhost:5000 in your browser

## Configuration

### API Key Setup

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Enter it in the Settings page of the web application

### Email Configuration (Optional)

For automatic email reports:

1. Use a Gmail account with 2-factor authentication enabled
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Configure in Settings:
   - Sender Email: your Gmail address
   - App Password: the generated app password
   - Default Recipient: where to send reports

## Usage

### File Upload

1. Click "Choose File" or drag and drop an audio/video file
2. Optionally enter an email address for results
3. Click "Upload & Process"
4. Monitor real-time progress
5. Download results when complete

### URL Processing

1. Paste a YouTube, Vimeo, or other video URL
2. Optionally enter an email address for results
3. Click "Process URL"
4. Monitor real-time progress
5. Download results when complete

## File Structure

```
web/
├── app.py                    # Main Flask application
├── transcription_service.py  # Core transcription logic
├── templates/               # HTML templates
│   ├── base.html
│   ├── index.html
│   └── settings.html
├── static/                  # Static assets
│   ├── css/style.css
│   └── js/app.js
├── uploads/                 # File upload directory
├── output/                  # Generated reports
└── requirements.txt         # Python dependencies
```

## API Endpoints

- `GET /` - Main interface
- `GET /settings` - Configuration page
- `POST /upload` - File upload
- `POST /process_url` - URL processing
- `GET /job_status/<job_id>` - Job status check
- `GET /download/<job_id>/<file_type>` - Download results
- `GET /health` - Health check

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Adding New Features

The application is built with Flask and follows a modular structure:

- `app.py`: Main application routes and configuration
- `transcription_service.py`: Core business logic
- `templates/`: HTML templates using Jinja2
- `static/`: CSS, JavaScript, and other static assets

## Production Deployment

For production deployment, consider:

1. Using a production WSGI server (e.g., Gunicorn)
2. Setting up a reverse proxy (e.g., Nginx)
3. Using environment variables for configuration
4. Setting up proper logging and monitoring
5. Using a database for job persistence (currently uses in-memory storage)

Example production command:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Security Considerations

- API keys are stored in `.env` files (ensure they're in `.gitignore`)
- File uploads are limited to 500MB and specific file types
- Input validation is performed on all user inputs
- Session management uses Flask's built-in security

## Support

For issues or questions:

1. Check that your OpenAI API key is configured correctly
2. Ensure you have sufficient API credits
3. Verify that uploaded files are in supported formats
4. Check the browser console for any JavaScript errors

## Cost Estimation

- Transcription: ~$0.006 per minute of audio
- Analysis: Variable based on transcript length and GPT-4 usage
- Total: Typically $0.01-0.05 per minute depending on content complexity