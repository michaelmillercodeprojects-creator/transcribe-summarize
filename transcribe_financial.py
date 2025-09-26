#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-
"""
Financial Audio Transcription Tool
Optimized for macro themes, trade ideas, and market analysis
"""
import argparse
import sys
import os

# Set UTF-8 encoding for Windows console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import subprocess
import tempfile
from typing import Optional
import mimetypes
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    import openai
    from dotenv import load_dotenv
    import requests
    import yt_dlp
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages:")
    print("pip install openai python-dotenv requests yt-dlp")
    sys.exit(1)

load_dotenv()

def load_api_key():
    """Load OpenAI API key from various sources."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    
    home_key_file = os.path.expanduser("~/.openai/api_key")
    if os.path.exists(home_key_file):
        with open(home_key_file, "r") as f:
            return f.read().strip()
    
    if os.path.exists("api_key"):
        with open("api_key", "r") as f:
            return f.read().strip()
    
    return None

def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffmpeg."""
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        raise RuntimeError("ffmpeg is not installed or not accessible. Please install ffmpeg to process audio files.")
    
    cmd = ["ffmpeg", "-i", audio_path]
    try:
        print(f"Analyzing audio duration: {os.path.basename(audio_path)}")
        sys.stdout.flush()
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=30)
        output = result.stderr.decode()
        for line in output.split('\n'):
            if 'Duration:' in line:
                time_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                duration = float(h) * 3600 + float(m) * 60 + float(s)
                print(f"Audio duration: {duration:.1f} seconds ({int(duration//60)}:{int(duration%60):02d})")
                sys.stdout.flush()
                return duration
        raise ValueError(f"Could not find duration in ffmpeg output")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffmpeg timed out while analyzing {audio_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}")

def extract_audio_chunk(video_path: str, start_time: float, duration: float) -> str:
    """Extract a chunk of audio from video using ffmpeg."""
    temp_fd, temp_audio_path = tempfile.mkstemp(suffix=".mp3")
    os.close(temp_fd)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "32k",
        temp_audio_path
    ]
    try:
        print(f"Extracting audio chunk: {start_time:.1f}s - {start_time+duration:.1f}s")
        sys.stdout.flush()
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        
        # Verify the output file was created and has content
        if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
            raise RuntimeError("Audio extraction produced empty file")
        
        print(f"Audio chunk extracted successfully: {os.path.getsize(temp_audio_path)} bytes")
        sys.stdout.flush()
        return temp_audio_path
    except subprocess.TimeoutExpired:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise RuntimeError(f"ffmpeg timed out while extracting audio chunk")
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise RuntimeError(f"ffmpeg audio extraction failed: {e.stderr.decode()}")

def get_audio_chunks(audio_path: str, max_duration: float = 600) -> list:
    """Split audio into chunks for processing."""
    duration = get_audio_duration(audio_path)
    
    if duration <= 600:  # 10 minutes
        return [(0, duration + 0.5)]
    
    chunks = []
    start = 0
    overlap = 10
    
    while start < duration:
        remaining = duration - start
        chunk_duration = min(max_duration, remaining)
        
        if remaining <= (max_duration + overlap):
            chunk_duration = remaining + 0.5
            
        chunks.append((start, chunk_duration))
        
        if start + chunk_duration >= duration:
            break
            
        start += max_duration - overlap
    
    return chunks

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url

def is_vimeo_url(url: str) -> bool:
    """Check if URL is a Vimeo video link."""
    return "vimeo.com/" in url and any(char.isdigit() for char in url.split("vimeo.com/")[-1])
def is_dropbox_url(url: str) -> bool:
    """Check if URL is a Dropbox share link."""
    return "dropbox.com" in url and ("sh/" in url or "s/" in url)

def is_google_drive_url(url: str) -> bool:
    """Check if URL is a Google Drive share link."""
    return "drive.google.com" in url and "file/d/" in url

def is_zoom_url(url: str) -> bool:
    """Check if URL is a Zoom recording link."""
    return "zoom.us" in url and ("rec/" in url or "recording" in url)

def unwrap_security_url(url: str) -> str:
    """Unwrap URLs from corporate security services."""
    import urllib.parse
    
    # Handle Microsoft Defender/Office 365 URL wrapping
    if "urldefense.com/v3/" in url:
        try:
            # Extract the wrapped URL from urldefense.com format
            # Format: https://urldefense.com/v3/__ENCODED_URL__;!!...
            wrapped_part = url.split("__")[1].split("__;")[0]
            # Replace URL encoding
            unwrapped = wrapped_part.replace("*", "%")
            unwrapped = urllib.parse.unquote(unwrapped)
            print(f"Unwrapped security URL: {unwrapped}")
            return unwrapped
        except (IndexError, ValueError):
            print(f"Failed to unwrap urldefense URL: {url}")
            return url
    
    # Handle Proofpoint URL wrapping
    if "urldefense.proofpoint.com" in url:
        try:
            # Extract URL parameter
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'u' in params:
                unwrapped = params['u'][0]
                # Replace encoding
                unwrapped = unwrapped.replace('-', '%').replace('_', '/')
                unwrapped = urllib.parse.unquote(unwrapped)
                print(f"Unwrapped Proofpoint URL: {unwrapped}")
                return unwrapped
        except (IndexError, ValueError, KeyError):
            print(f"Failed to unwrap Proofpoint URL: {url}")
            return url
    
    # Handle other common security wrappers
    for pattern in ["safelinks.protection.outlook.com", "protect-us.mimecast.com", "urlscan.io"]:
        if pattern in url:
            try:
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                # Try common parameter names for the wrapped URL
                for param in ['url', 'u', 'link', 'target']:
                    if param in params:
                        unwrapped = urllib.parse.unquote(params[param][0])
                        print(f"Unwrapped {pattern} URL: {unwrapped}")
                        return unwrapped
            except:
                pass
    
    return url

def convert_sharing_url(url: str) -> str:
    """Convert sharing URLs to direct download URLs."""
    # First unwrap any security URLs
    url = unwrap_security_url(url)
    
    # Dropbox sharing URL conversion
    if "dropbox.com/s/" in url or "dropbox.com/scl/" in url:
        # For newer format: https://www.dropbox.com/scl/fi/...?dl=0 -> ?dl=1
        if "?dl=0" in url:
            return url.replace("?dl=0", "?dl=1")
        elif "&dl=0" in url:
            return url.replace("&dl=0", "&dl=1")
        elif url.endswith("?dl=0"):
            return url[:-5] + "?dl=1"
        # If no dl parameter, add it
        elif "?" in url:
            return url + "&dl=1"
        else:
            return url + "?dl=1"
    
    # Google Drive sharing URL conversion
    if "drive.google.com/file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Default: return as-is
    return url

def download_file(url: str) -> str:
    """Download file from URL, YouTube, or file sharing services."""
    original_url = url
    
    # Handle YouTube and Vimeo URLs
    if is_youtube_url(url) or is_vimeo_url(url):
        os.makedirs("audio", exist_ok=True)
        outtmpl = "audio/%(title)s.%(ext)s"
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", outtmpl]
        try:
            subprocess.run(cmd, check=True)
            import glob
            mp3_files = glob.glob("audio/*.mp3")
            if not mp3_files:
                raise RuntimeError("yt-dlp did not produce any .mp3 files")
            return max(mp3_files, key=os.path.getctime)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"yt-dlp failed: {e.stderr.decode()}")
    
        # Handle YouTube and Vimeo URLs
        if is_youtube_url(url) or is_vimeo_url(url):
            os.makedirs("audio", exist_ok=True)
            outtmpl = "audio/%(title)s.%(ext)s"
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", outtmpl]
            try:
                subprocess.run(cmd, check=True)
                import glob
                mp3_files = glob.glob("audio/*.mp3")
                if not mp3_files:
                    raise RuntimeError("yt-dlp did not produce any .mp3 files")
                return max(mp3_files, key=os.path.getctime)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"yt-dlp failed: {e.stderr.decode()}")
    # Handle Zoom recordings with yt-dlp (often works better than direct download)
    if is_zoom_url(url):
        os.makedirs("audio", exist_ok=True)
        outtmpl = "audio/zoom_recording_%(epoch)s.%(ext)s"
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", outtmpl]
        try:
            print("Attempting to download Zoom recording...")
            subprocess.run(cmd, check=True)
            import glob
            mp3_files = glob.glob("audio/zoom_recording_*.mp3")
            if mp3_files:
                return max(mp3_files, key=os.path.getctime)
        except subprocess.CalledProcessError:
            print("yt-dlp failed for Zoom URL, trying direct download...")
    
    # Convert sharing URLs to direct download URLs
    download_url = convert_sharing_url(url)
    
    try:
        print(f"Downloading from: {download_url}")
        sys.stdout.flush()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        r = requests.get(download_url, stream=True, headers=headers, timeout=60, allow_redirects=True)
        r.raise_for_status()
        
        # Handle large files with progress indication
        total_size = int(r.headers.get('content-length', 0))
        if total_size > 100 * 1024 * 1024:  # 100MB
            print(f"Large file detected ({total_size // (1024*1024)}MB), downloading...")
        
        content_type = r.headers.get("content-type", "")
        ext = mimetypes.guess_extension(content_type.split(";")[0])
        if not ext:
            ext = os.path.splitext(url)[1]
        
        temp_fd, temp_path = tempfile.mkstemp(suffix=ext or ".tmp")
        os.close(temp_fd)
        
        downloaded = 0
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:  # Progress every 10MB
                    print(f"Downloaded {downloaded // (1024*1024)}MB of {total_size // (1024*1024)}MB")
        
        print(f"Download complete: {temp_path}")
        return temp_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to download file from {original_url}: {e}")

def transcribe_audio(input_path: str, model: str = "whisper-1") -> str:
    """Transcribe audio file with chunking support."""
    temp_paths = []
    
    if is_url(input_path):
        print(f"Downloading file from URL: {input_path}")
        try:
            input_path = download_file(input_path)
            temp_paths.append(input_path)
            print(f"Download completed: {os.path.getsize(input_path)} bytes")
        except Exception as e:
            raise RuntimeError(f"Failed to download file: {e}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check file size
    file_size = os.path.getsize(input_path)
    print(f"Processing file: {os.path.basename(input_path)} ({file_size:,} bytes)")
    sys.stdout.flush()
    
    api_key = load_api_key()
    if not api_key:
        raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or create .env file")
    
    print("Initializing OpenAI client...")
    sys.stdout.flush()
    client = openai.OpenAI(api_key=api_key)
    
    # Test API connection
    try:
        print("Testing OpenAI API connection...")
        sys.stdout.flush()
        models = client.models.list()
        print("OpenAI API connection successful")
        sys.stdout.flush()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to OpenAI API: {e}")

    try:
        chunks = get_audio_chunks(input_path)
        transcript_parts = []

        print(f"Audio will be processed in {len(chunks)} chunk(s)")
        sys.stdout.flush()
        
        for i, (start, chunk_duration) in enumerate(chunks):
            print(f"\n=== Processing chunk {i+1}/{len(chunks)} ===")
            print(f"Time range: {int(start)}s to {int(start+chunk_duration)}s ({chunk_duration:.1f}s duration)")
            sys.stdout.flush()
            
            try:
                temp_chunk_path = extract_audio_chunk(input_path, start, chunk_duration)
                temp_paths.append(temp_chunk_path)
                
                with open(temp_chunk_path, "rb") as audio_file:
                    file_size = os.path.getsize(temp_chunk_path)
                    print(f"Uploading chunk {i+1} to OpenAI for transcription... ({file_size:,} bytes)")
                    sys.stdout.flush()
                    
                    import time, threading
                    start_time = time.time()
                    
                    # Add heartbeat indicator for long-running operations
                    def heartbeat():
                        while True:
                            time.sleep(30)  # Every 30 seconds
                            elapsed = time.time() - start_time
                            print(f"Still processing chunk {i+1}... ({elapsed:.0f}s elapsed)")
                            sys.stdout.flush()
                    
                    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
                    heartbeat_thread.start()
                    
                    try:
                        transcript = client.audio.transcriptions.create(
                            model=model,
                            file=audio_file
                        )
                        
                        elapsed = time.time() - start_time
                        print(f"[SUCCESS] Chunk {i+1} transcription completed: {len(transcript.text)} characters ({elapsed:.1f}s)")
                        sys.stdout.flush()
                    
                    except Exception as api_error:
                        elapsed = time.time() - start_time
                        print(f"[ERROR] API call failed after {elapsed:.1f}s: {api_error}")
                        sys.stdout.flush()
                        raise api_error
                    transcript_parts.append(transcript.text)
                    
            except Exception as e:
                print(f"[ERROR] Error processing chunk {i+1}: {e}")
                raise RuntimeError(f"Failed to process audio chunk {i+1}/{len(chunks)}: {e}")
            
            if temp_chunk_path and os.path.exists(temp_chunk_path):
                os.remove(temp_chunk_path)
        
        return "\n\n".join(transcript_parts)
        
    finally:
        for p in temp_paths:
            if p and os.path.exists(p):
                os.remove(p)

def create_financial_summary(transcript: str, model: str = "gpt-4o") -> str:
    """Create focused financial summary with macro themes and trade ideas."""
    api_key = load_api_key()
    if not api_key:
        raise EnvironmentError("OpenAI API key not found")
    
    print(f"Initializing analysis with model: {model}")
    print(f"Transcript length: {len(transcript):,} characters")
    sys.stdout.flush()
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""You are a senior institutional investment analyst creating a comprehensive research report. Analyze this financial transcript and extract ONLY the specific investment insights, ideas, and data that the speakers actually discussed.

<b>CRITICAL REQUIREMENTS - DO NOT FABRICATE DATA:</b>
- ONLY use numbers, percentages, price targets, and timeframes explicitly mentioned in the transcript
- DO NOT invent or estimate financial figures not stated by the speakers
- DO NOT create sections if the speakers didn't discuss those topics
- Create detailed bullet points (100-150 words each) ONLY for topics that were actually covered
- Embed exact quotes naturally within the bullet point text
- Use • symbol for bullets only, no other formatting
- Write in professional institutional language

<b>CONTENT-DRIVEN ANALYSIS APPROACH:</b>

Analyze the transcript and create bullet points ONLY for the topics and insights the speakers actually discussed. Use these potential categories, but SKIP any category where speakers provided no meaningful content:

<b>MARKET INSIGHTS (if discussed):</b>
• Extract any specific market views, economic outlook, sector analysis, or macro themes mentioned
• Include exact timeframes, percentages, or targets if provided by speakers
• Quote speaker reasoning and supporting arguments

<b>SPECIFIC INVESTMENT IDEAS (if discussed):</b>
• Capture any individual stock recommendations, price targets, or specific company analysis
• Include speaker rationale, catalysts, and risk/reward perspectives mentioned
• Note any specific entry/exit levels, position sizing, or timing guidance provided

<b>SECTOR/THEMATIC OPPORTUNITIES (if discussed):</b>
• Document any sector rotations, industry trends, or thematic plays mentioned
• Include specific ETFs, sectors, or investment themes discussed
• Capture any quantitative expectations or comparative analysis provided

<b>TRADING STRATEGIES & POSITIONING (if discussed):</b>  
• Detail any specific trading approaches, options strategies, or hedging mentioned
• Include portfolio positioning, asset allocation, or tactical moves discussed
• Note any risk management approaches or defensive strategies covered

<b>GEOGRAPHIC/INTERNATIONAL THEMES (if discussed):</b>
• Capture any country-specific, regional, or international investment themes
• Include currency views, emerging market perspectives, or global allocation ideas
• Note any geopolitical factors affecting investment decisions

<b>ALTERNATIVE INVESTMENTS (if discussed):</b>
• Document any REIT, commodity, crypto, or alternative strategy discussions
• Include fixed income, credit, or yield-focused opportunities mentioned
• Note any inflation hedges or portfolio diversification strategies covered

<b>CRITICAL EXECUTION GUIDELINES:</b>
- If speakers didn't discuss a category meaningfully, SKIP IT entirely
- Focus on extracting the most valuable, actionable insights with numbers and specifics
- Each bullet should be substantive (100-150 words) with embedded quotes
- Prioritize content that includes specific data, targets, or quantitative elements
- Use speaker names if mentioned to attribute insights appropriately
- Maintain professional institutional language throughout

<b>ABSOLUTE REQUIREMENTS:</b>
- Use <b>bold tags</b> for emphasis, never asterisks
- Include exact quotes using "quotation marks"
- Never fabricate numbers, percentages, price targets, or predictions
- Skip empty or speculative analysis - stick strictly to transcript content

Transcript to analyze:
{transcript}

Generate a content-driven analysis that focuses ONLY on the specific insights and ideas the speakers actually discussed. Skip any categories where they provided no meaningful content."""

    try:
        import time, threading
        print("Sending transcript to GPT for financial analysis...")
        sys.stdout.flush()
        start_time = time.time()
        
        # Add heartbeat indicator for analysis
        def analysis_heartbeat():
            while True:
                time.sleep(15)  # Every 15 seconds
                elapsed = time.time() - start_time
                print(f"Still analyzing transcript... ({elapsed:.0f}s elapsed)")
                sys.stdout.flush()
        
        analysis_heartbeat_thread = threading.Thread(target=analysis_heartbeat, daemon=True)
        analysis_heartbeat_thread.start()
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1,
        )
        
        elapsed = time.time() - start_time
        print(f"Analysis completed in {elapsed:.1f}s")
        sys.stdout.flush()
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] Financial analysis failed: {e}")
        raise RuntimeError(f"Financial analysis failed: {e}")

def markdown_to_html(text: str) -> str:
    """Convert clean text format to HTML for email formatting."""
    import re
    
    # Convert ## headers to HTML headers
    text = re.sub(r'^##\s+(.+)$', r'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">\1</h2>', text, flags=re.MULTILINE)
    
    # Convert numbered sections to headers
    text = re.sub(r'^(\d+\.\s+[^•\n]+)$', r'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">\1</h2>', text, flags=re.MULTILINE)
    
    # Convert **text** to bold tags first
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert bold tags to proper HTML bold with styling
    text = re.sub(r'<b>(.*?)</b>', r'<strong style="color: #2c3e50; font-weight: bold;">\1</strong>', text)
    
    # Convert bullet points (• symbol)
    text = re.sub(r'^•\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Wrap consecutive <li> items in <ul>
    text = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul style="margin: 15px 0; padding-left: 20px;">\1</ul>', text, flags=re.DOTALL)
    
    # Convert line breaks
    text = text.replace('\n\n', '</p><p style="margin: 15px 0;">')
    text = text.replace('\n', '<br>')
    
    # Wrap remaining text in paragraphs
    if not text.startswith('<'):
        text = f'<p style="margin: 15px 0;">{text}</p>'
    
    return text

def send_email_summary(summary: str, transcript: str, recipient: str, subject: str = None):
    """Send summary and transcript via email with HTML formatting."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("Email credentials not found. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file")
        return False
    
    if not subject:
        subject = f"Financial Analysis Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Convert markdown summary to HTML
    html_summary = markdown_to_html(summary)
    
    # Create HTML email content
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
            h3 {{ color: #34495e; margin-top: 25px; }}
            strong {{ color: #2c3e50; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 5px 0; }}
            .transcript {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin-top: 30px; }}
            .separator {{ border-top: 3px solid #3498db; margin: 30px 0; padding-top: 20px; }}
        </style>
    </head>
    <body>
        {html_summary}
        
        <div class="separator">
            <h2>FULL TRANSCRIPT</h2>
            <div class="transcript">
                <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.4;">{transcript}</pre>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text version as fallback
    plain_text = f"""
{summary}

================================================================================
FULL TRANSCRIPT  
================================================================================

{transcript}
"""
    
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Attach both plain text and HTML versions
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        print(f"HTML-formatted summary sent to {recipient}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def sanitize_filename(s: str) -> str:
    import re
    s = s.strip().replace(' ', '_')
    s = re.sub(r'[^A-Za-z0-9_.-]', '', s)
    return s[:64]

def extract_title_from_filename(filename: str) -> str:
    """Extract a clean title from the audio filename"""
    import re
    
    # Get basename without extension
    base = os.path.splitext(os.path.basename(filename))[0]
    
    # Replace underscores and hyphens with spaces
    title = base.replace('_', ' ').replace('-', ' ')
    
    # Remove common file prefixes/suffixes
    title = re.sub(r'^(audio|video|recording|webinar|call)\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*(audio|video|recording|webinar|call)$', '', title, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and capitalize
    title = re.sub(r'\s+', ' ', title).strip()
    title = ' '.join(word.capitalize() for word in title.split())
    
    return title if title else "Financial Analysis Report"

def create_pdf_report(summary: str, transcript: str, output_path: str, source_filename: str):
    """Create a professional PDF report with title and formatted sections"""
    try:
        # Extract title from filename
        report_title = extract_title_from_filename(source_filename)
        
        # Create PDF file path
        pdf_path = output_path.replace('.txt', '.pdf')
        
        # Create document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=1*inch, bottomMargin=0.75*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='#2c3e50'
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor='#34495e'
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_LEFT
        )
        
        transcript_style = ParagraphStyle(
            'TranscriptText',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(f"<b>FINANCIAL ANALYSIS REPORT</b>", title_style))
        story.append(Paragraph(f"<b>{report_title}</b>", title_style))
        story.append(Spacer(1, 20))
        
        # Add generation info
        generation_info = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>Source: {os.path.basename(source_filename)}"
        story.append(Paragraph(generation_info, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Parse and format the summary
        lines = summary.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for ## headers
            if line.startswith('##'):
                header_text = line[2:].strip()
                story.append(Paragraph(f"<b>{header_text}</b>", section_style))
                continue
                
            # Check for section headers (numbered sections)
            if line and line[0].isdigit() and '.' in line[:5]:
                current_section = line
                story.append(Paragraph(f"<b>{line}</b>", section_style))
                continue
            
            # Check for bullet points
            if line.startswith('•'):
                # Clean up the bullet point
                bullet_text = line[1:].strip()
                
                # Convert formatting to ReportLab format
                # First convert **text** to <b>text</b>
                import re
                bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
                # Convert bold tags to ReportLab bold format
                bullet_text = bullet_text.replace('<b>', '<b>').replace('</b>', '</b>') 
                
                # Handle long bullet points by breaking into paragraphs if needed
                if len(bullet_text) > 500:
                    # Split at sentence boundaries for very long bullets
                    sentences = bullet_text.split('. ')
                    formatted_text = '. '.join(sentences[:2])
                    if len(sentences) > 2:
                        formatted_text += '. ' + '. '.join(sentences[2:])
                else:
                    formatted_text = bullet_text
                
                # Add bullet point with proper formatting
                story.append(Paragraph(f"• {formatted_text}", bullet_style))
            else:
                # Regular paragraph text
                if line:
                    story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 6))
        
        # Add page break before transcript
        story.append(PageBreak())
        
        # Add transcript section
        story.append(Paragraph("<b>FULL TRANSCRIPT</b>", section_style))
        story.append(Spacer(1, 12))
        
        # Format transcript in smaller chunks to avoid ReportLab issues
        transcript_paragraphs = transcript.split('\n\n')
        for para in transcript_paragraphs:
            if para.strip():
                # Escape HTML characters and format
                clean_para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(clean_para, transcript_style))
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        print(f"PDF report created: {pdf_path}")
        sys.stdout.flush()
        return pdf_path
        
    except Exception as e:
        print(f"Error creating PDF report: {e}")
        sys.stdout.flush()
        return None

def main():
    parser = argparse.ArgumentParser(description="Financial Audio Transcription and Analysis Tool")
    parser.add_argument("--input", required=True, help="Path, URL, or sharing link to audio/video file (supports Dropbox, Google Drive, Zoom, YouTube, Vimeo)")
    parser.add_argument("--email", help="Email address to send results to")
    parser.add_argument("--subject", help="Email subject line")
    parser.add_argument("--transcribe-model", default="whisper-1", help="Whisper model to use for transcription")
    parser.add_argument("--summary-model", default="gpt-4o", help="GPT model to use for financial analysis")
    parser.add_argument("--link", action="store_true", help="Treat input as a sharing link (Dropbox, Google Drive, etc.)")
    args = parser.parse_args()

    try:
        print(f"\n{'='*60}")
        print(f"STARTING FINANCIAL ANALYSIS")
        print(f"{'='*60}")
        print(f"Input: {args.input}")
        print(f"Transcription model: {args.transcribe_model}")
        print(f"Analysis model: {args.summary_model}")
        print(f"{'='*60}\n")
        sys.stdout.flush()
        
        print("STEP 1: TRANSCRIBING AUDIO...")
        sys.stdout.flush()
        import time
        step1_start = time.time()
        
        transcript = transcribe_audio(args.input, model=args.transcribe_model)
        step1_time = time.time() - step1_start
        print(f"[SUCCESS] Transcription complete! Generated {len(transcript):,} characters of text (took {step1_time:.1f}s)\n")
        sys.stdout.flush()
        
        print("STEP 2: CREATING FINANCIAL ANALYSIS...")
        sys.stdout.flush()
        step2_start = time.time()
        
        summary = create_financial_summary(transcript, model=args.summary_model)
        
        # Clean up any remaining formatting issues
        import re
        summary = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', summary)  # Convert **text** to <b>text</b>
        summary = re.sub(r'^##\s+(.+)$', r'<b>\1</b>', summary, flags=re.MULTILINE)  # Convert ## headers
        
        step2_time = time.time() - step2_start
        print(f"[SUCCESS] Financial analysis complete! Generated {len(summary):,} characters of analysis (took {step2_time:.1f}s)\n")
        sys.stdout.flush()

        # Create combined document
        combined_content = f"""FINANCIAL ANALYSIS SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {args.input}

{summary}

================================================================================
FULL TRANSCRIPT
================================================================================

{transcript}
"""

        # Save to file
        os.makedirs("output", exist_ok=True)
        base = args.input
        if is_url(base):
            base = base.split('/')[-1].split('?')[0]
        base = sanitize_filename(base)
        
        output_path = f"output/{base}_financial_analysis.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(combined_content)

        print("=" * 80)
        print(combined_content)
        print("=" * 80)
        print(f"\nAnalysis saved to: {output_path}")
        sys.stdout.flush()
        
        # Create PDF report
        print("\nSTEP 3: CREATING PDF REPORT...")
        sys.stdout.flush()
        
        pdf_path = create_pdf_report(summary, transcript, output_path, args.input)
        if pdf_path:
            print(f"PDF report created: {pdf_path}")
        else:
            print("PDF generation failed, text report available")
        sys.stdout.flush()
        
        # Send email if requested
        if args.email:
            send_email_summary(summary, transcript, args.email, args.subject)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()