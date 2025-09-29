# Financial Audio Transcription Suite - Web Version

A web-based version of the Financial Audio Transcription Suite for transcribing and analyzing financial audio/video content using OpenAI's APIs.

## Features

- **Web Interface**: Modern, responsive web interface accessible from any browser
- **File Upload**: Support for audio/video files up to 500MB
- **URL Processing**: Process content from YouTube, Vimeo, Dropbox, Google Drive, and more
- **Real-time Progress**: Live status updates during processing
- **Financial Analysis**: AI-powered analysis focused on investment insights and market themes
- **Email Reports**: Optional email delivery of analysis reports
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Prerequisites**
   - Docker and Docker Compose installed
   - OpenAI API key

2. **Deploy**
   ```bash
   cd web
   cp .env.example .env
   # Edit .env file with your OpenAI API key
   ./deploy.sh
   ```

3. **Access**
   - Open http://localhost:5000 in your browser
   - Go to Settings to configure API keys and email
   - Upload files or provide URLs for processing

### Option 2: Manual Installation

1. **Install Dependencies**
   ```bash
   cd web
   pip install -r requirements.txt
   ```

2. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Install yt-dlp
   pip install yt-dlp
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run Application**
   ```bash
   python app.py
   ```

## Configuration

### Required Settings
- **OpenAI API Key**: Required for transcription and analysis
  - Get your key at https://platform.openai.com/api-keys

### Optional Settings
- **Email Configuration**: For sending analysis reports
  - Gmail address and app password
  - Output email address for recipients
- **Vimeo API**: For processing private Vimeo videos
  - Client ID, Client Secret, and Access Token

## API Endpoints

- `POST /api/upload` - Upload and process file
- `POST /api/process-url` - Process URL
- `GET /api/job-status/<job_id>` - Get processing status
- `POST /api/save-settings` - Save user settings
- `GET /api/get-settings` - Get user settings
- `POST /api/test-email` - Test email configuration

## Supported Formats

### Audio Files
- MP3, WAV, M4A, AAC, OGG

### Video Files
- MP4, AVI, MOV, MKV, FLV, WebM

### URL Sources
- YouTube
- Vimeo (public and private with API key)
- Dropbox share links
- Google Drive share links
- Zoom recordings
- Direct file URLs

## Docker Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
EMAIL_ADDRESS=your-gmail@gmail.com
EMAIL_PASSWORD=your-app-password
OUTPUT_EMAIL=recipient@example.com
```

### Volumes
- `./uploads:/app/uploads` - Temporary file uploads
- `./audio:/app/audio` - Downloaded audio files
- `./output:/app/output` - Generated reports

### Ports
- `5000:5000` - Web application port

## Security Considerations

- Change the `SECRET_KEY` in production
- Use HTTPS in production environments
- Store sensitive configuration in environment variables
- Regularly update dependencies
- Consider using a reverse proxy (nginx) for production

## Monitoring and Management

### Docker Commands
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# View running containers
docker-compose ps

# Access container shell
docker-compose exec transcription-web bash
```

### Health Checks
- Built-in health check endpoint at `/`
- Docker health checks configured
- Monitor container status with `docker-compose ps`

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure sufficient credits

2. **File Upload Failures**
   - Check file size (max 500MB)
   - Verify file format is supported
   - Ensure sufficient disk space

3. **Email Issues**
   - Use Gmail app passwords, not regular passwords
   - Enable 2-factor authentication on Gmail
   - Check Gmail security settings

4. **URL Processing Failures**
   - Some platforms may block automated downloads
   - Private videos require appropriate API credentials
   - Check internet connectivity

### Log Analysis
```bash
# View application logs
docker-compose logs transcription-web

# View specific service logs
docker-compose logs -f transcription-web

# View system resource usage
docker stats
```

## Development

### Local Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py
```

### Project Structure
```
web/
├── app.py                  # Main Flask application
├── transcription_service.py # Core transcription logic
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   └── settings.html
├── static/                 # Static assets
│   ├── css/style.css
│   └── js/main.js
├── uploads/                # Temporary uploads
├── audio/                  # Downloaded files
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── deploy.sh              # Deployment script
```

## License

Same license as the parent project.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Check system dependencies