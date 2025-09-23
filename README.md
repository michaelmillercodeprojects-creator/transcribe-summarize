# Transcribe-Summarize

[![CI](https://github.com/michaelmillercodeprojects-creator/transcribe-summarize/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelmillercodeprojects-creator/transcribe-summarize/actions/workflows/ci.yml)

A command-line tool to transcribe audio/video content and generate summaries using OpenAI's APIs.

## Features

- Transcribe audio/video files using OpenAI's Whisper API
- Generate concise summaries using GPT-4
- Support for various input formats:
  - Local audio files (mp3, wav, m4a, etc.)
  - Local video files (mp4, mov, mkv, etc.)
  - YouTube URLs (automatic download)
  - Direct HTTP/HTTPS links
- Automatic handling of long content through chunking
- Configurable summary length (short, medium, detailed)

## Installation

### Prerequisites

- Python 3.8 or higher
- ffmpeg (for audio/video processing)
- An OpenAI API key

### Installing ffmpeg

On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install ffmpeg
```

On macOS with Homebrew:
```bash
brew install ffmpeg
```

On Windows with Chocolatey:
```bash
choco install ffmpeg
```

### Installing the Package

```bash
pip install transcribe-summarize
```

Or install from source:
```bash
git clone https://github.com/michaelmillercodeprojects-creator/transcribe-summarize.git
cd transcribe-summarize
pip install -e .
```

### Configuration

Set up your OpenAI API key using one of these methods:
1. Environment variable: `export OPENAI_API_KEY=your-key`
2. Create a `.env` file with: `OPENAI_API_KEY=your-key`
3. Create `~/.openai/api_key` file with just the key
4. Create `api_key` file in the current directory

## Usage

### Basic Usage

```bash
transcribe-summarize --input=path/to/file.mp3
```

### Options

```bash
transcribe-summarize --help
```

- `--input`: Path or URL to audio/video file
- `--summary-length`: Choose summary detail level (short, medium, detailed)
- `--transcribe-model`: Choose OpenAI model for transcription
- `--summary-model`: Choose OpenAI model for summarization

### Examples

Transcribe a local video file:
```bash
transcribe-summarize --input=video.mp4
```

Transcribe from YouTube:
```bash
transcribe-summarize --input="https://youtube.com/watch?v=..."
```

Generate a detailed summary:
```bash
transcribe-summarize --input=audio.mp3 --summary-length=detailed
```

## Output

The tool creates two files in the `output` directory:
- `{input}_transcript.txt`: Full transcription
- `{input}_summary.txt`: Generated summary

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
