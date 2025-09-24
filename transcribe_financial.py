#!/usr/bin/env python3
"""
Financial Audio Transcription Tool
Optimized for macro themes, trade ideas, and market analysis
"""
import argparse
import sys
import os
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
    cmd = ["ffmpeg", "-i", audio_path]
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = result.stderr.decode()
        for line in output.split('\n'):
            if 'Duration:' in line:
                time_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
        raise ValueError(f"Could not find duration in ffmpeg output")
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
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return temp_audio_path
    except subprocess.CalledProcessError as e:
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
    
    # Handle YouTube URLs
    if is_youtube_url(url):
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
        input_path = download_file(input_path)
        temp_paths.append(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    api_key = load_api_key()
    if not api_key:
        raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or create .env file")
    
    client = openai.OpenAI(api_key=api_key)

    try:
        chunks = get_audio_chunks(input_path)
        transcript_parts = []

        print(f"Audio will be processed in {len(chunks)} chunk(s)")
        
        for i, (start, chunk_duration) in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)} (from {int(start)}s to {int(start+chunk_duration)}s)...")
            
            temp_chunk_path = extract_audio_chunk(input_path, start, chunk_duration)
            temp_paths.append(temp_chunk_path)
            
            with open(temp_chunk_path, "rb") as audio_file:
                print(f"Sending chunk {i+1} to OpenAI for transcription...")
                transcript = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file
                )
                print(f"Chunk {i+1} transcription completed: {len(transcript.text)} characters")
                transcript_parts.append(transcript.text)
            
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
    
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""You are a professional financial analyst writing a clean, structured investment report. Analyze the following transcript and provide actionable investment insights in a professional format.

**FORMATTING REQUIREMENTS:**
- Use clean bullet points with • symbol only
- No markdown headers (##, ###) or asterisks (*) 
- No random formatting characters
- Write in professional, institutional language
- Structure information clearly with numbered sections and subsections
- CRITICAL: Include exact quotes from the transcript to support each key point

**ANALYSIS STRUCTURE:**

1. Market Views
Provide 3-4 bullet points analyzing:
• Economic trends and policy implications for markets
  Supporting Quote: "[Exact quote from transcript about economic conditions]"
• Sector dynamics and structural changes  
  Supporting Quote: "[Exact quote from transcript about sector trends]"
• Geopolitical factors affecting asset allocation
  Supporting Quote: "[Exact quote from transcript about geopolitical impacts]"
• Central bank positioning and monetary policy impact
  Supporting Quote: "[Exact quote from transcript about monetary policy]"

2. Trade Ideas and Position Commentary
For each investment opportunity mentioned, provide:
• Investment thesis: WHY this is attractive now with specific reasoning
  Supporting Quote: "[Exact quote from transcript explaining the opportunity]"
• Risk assessment: Key vulnerabilities and what could go wrong
  Supporting Quote: "[Exact quote from transcript about risks or concerns]"
• Timing considerations: Catalysts, cycle positioning, entry points
  Supporting Quote: "[Exact quote from transcript about timing]"
• Implementation: Best vehicles (stocks, ETFs, sectors) with rationale
  Supporting Quote: "[Exact quote from transcript about specific investments]"

3. Strategic Takeaways  
Summarize:
• Key actionable insights for portfolio positioning
  Supporting Quote: "[Exact quote from transcript with strategic guidance]"
• Risk management considerations
  Supporting Quote: "[Exact quote from transcript about risk management]"
• Timing and implementation guidance
  Supporting Quote: "[Exact quote from transcript about implementation]"

**WRITING STYLE:**
- Professional institutional tone
- Specific data points and company names when mentioned
- Clear cause-and-effect reasoning
- Forward-looking implications
- No speculative language - focus on analytical framework
- MANDATORY: Include verbatim quotes in quotation marks to support each bullet point

Transcript:
{transcript}

Provide the analysis in the exact format shown above with clean bullet points, numbered sections, and supporting quotes from the transcript for each key point."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Financial analysis failed: {e}")

def markdown_to_html(text: str) -> str:
    """Convert clean text format to HTML for email formatting."""
    import re
    
    # Convert numbered sections to headers
    text = re.sub(r'^(\d+\.\s+[^•\n]+)$', r'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 25px;">\1</h2>', text, flags=re.MULTILINE)
    
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

def main():
    parser = argparse.ArgumentParser(description="Financial Audio Transcription and Analysis Tool")
    parser.add_argument("--input", required=True, help="Path, URL, or sharing link to audio/video file (supports Dropbox, Google Drive, Zoom, YouTube)")
    parser.add_argument("--email", help="Email address to send results to")
    parser.add_argument("--subject", help="Email subject line")
    parser.add_argument("--transcribe-model", default="whisper-1", help="Whisper model to use for transcription")
    parser.add_argument("--summary-model", default="gpt-4o", help="GPT model to use for financial analysis")
    parser.add_argument("--link", action="store_true", help="Treat input as a sharing link (Dropbox, Google Drive, etc.)")
    args = parser.parse_args()

    try:
        print(f"Starting financial analysis for: {args.input}")
        transcript = transcribe_audio(args.input, model=args.transcribe_model)
        print("Transcription complete.\n")
        
        print("Creating financial analysis...")
        summary = create_financial_summary(transcript, model=args.summary_model)
        print("Financial analysis complete.\n")

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
        
        # Send email if requested
        if args.email:
            send_email_summary(summary, transcript, args.email, args.subject)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()