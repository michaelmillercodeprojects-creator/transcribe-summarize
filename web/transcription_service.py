#!/usr/bin/env python3
"""
Transcription Service Module
Core transcription and analysis functionality extracted for web application use
"""

import os
import sys
import subprocess
import tempfile
import threading
import time
import smtplib
from datetime import datetime
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Third-party imports with error handling
try:
    import openai
    from dotenv import load_dotenv
    import requests
    import yt_dlp
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError as e:
    print(f"Missing required package: {e}")
    raise

load_dotenv()

class TranscriptionService:
    """Service class for handling transcription and analysis operations"""
    
    def __init__(self, settings: Dict[str, Any] = None):
        """Initialize the transcription service with settings"""
        self.settings = settings or {}
        self.client = None
        
    def load_api_key(self) -> str:
        """Load OpenAI API key from settings or environment"""
        api_key = self.settings.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise EnvironmentError("OpenAI API key not found. Please configure in settings.")
        return api_key
    
    def get_client(self):
        """Get or create OpenAI client"""
        if not self.client:
            api_key = self.load_api_key()
            self.client = openai.OpenAI(api_key=api_key)
        return self.client
    
    def update_progress(self, job_id: str, progress: str, jobs_dict: Dict):
        """Update job progress"""
        if job_id in jobs_dict:
            jobs_dict[job_id]['progress'] = progress
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file using ffprobe."""
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
               "-of", "csv=p=0", audio_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Could not determine audio duration: {e}")
    
    def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        temp_fd, temp_audio_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)
        
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", 
            "-ar", "16000", "-ac", "1", "-b:a", "32k",
            temp_audio_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, timeout=300)
            if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
                raise RuntimeError("Audio extraction produced empty file")
            return temp_audio_path
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise RuntimeError("ffmpeg timed out during audio extraction")
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}")
    
    def extract_audio_chunk(self, video_path: str, start_time: float, duration: float) -> str:
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
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, timeout=120)
            
            if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
                raise RuntimeError("Audio extraction produced empty file")
            
            return temp_audio_path
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise RuntimeError("ffmpeg timed out while extracting audio chunk")
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise RuntimeError(f"ffmpeg audio extraction failed: {e.stderr.decode()}")
    
    def get_audio_chunks(self, audio_path: str, max_duration: float = 600) -> list:
        """Split audio into chunks for processing."""
        duration = self.get_audio_duration(audio_path)
        
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
    
    def download_from_url(self, url: str, job_id: str = None, jobs_dict: Dict = None) -> str:
        """Download audio/video from URL using yt-dlp"""
        if jobs_dict and job_id:
            self.update_progress(job_id, "Downloading from URL...", jobs_dict)
        
        os.makedirs("audio", exist_ok=True)
        outtmpl = "audio/downloaded_%(title)s.%(ext)s"
        
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", outtmpl]
        
        try:
            subprocess.run(cmd, check=True, timeout=600)
            
            import glob
            mp3_files = glob.glob("audio/downloaded_*.mp3")
            if not mp3_files:
                raise RuntimeError("yt-dlp did not produce any .mp3 files")
            return max(mp3_files, key=os.path.getctime)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Download failed: {e}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Download timed out after 10 minutes")
    
    def transcribe_audio(self, input_path: str, model: str = "whisper-1", 
                        job_id: str = None, jobs_dict: Dict = None) -> str:
        """Transcribe audio file using OpenAI Whisper API."""
        temp_paths = []
        
        try:
            if jobs_dict and job_id:
                self.update_progress(job_id, "Starting transcription...", jobs_dict)
            
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            file_size = os.path.getsize(input_path)
            print(f"Processing file: {os.path.basename(input_path)} ({file_size:,} bytes)")
            
            client = self.get_client()
            
            # Test API connection
            try:
                models = client.models.list()
                print("OpenAI API connection successful")
            except Exception as e:
                raise RuntimeError(f"Failed to connect to OpenAI API: {e}")
            
            chunks = self.get_audio_chunks(input_path)
            transcript_parts = []
            
            print(f"Audio will be processed in {len(chunks)} chunk(s)")
            
            for i, (start, chunk_duration) in enumerate(chunks):
                if jobs_dict and job_id:
                    self.update_progress(job_id, f"Processing chunk {i+1}/{len(chunks)}...", jobs_dict)
                
                print(f"Processing chunk {i+1}/{len(chunks)}")
                print(f"Time range: {int(start)}s to {int(start+chunk_duration)}s")
                
                try:
                    temp_chunk_path = self.extract_audio_chunk(input_path, start, chunk_duration)
                    temp_paths.append(temp_chunk_path)
                    
                    with open(temp_chunk_path, "rb") as audio_file:
                        file_size = os.path.getsize(temp_chunk_path)
                        print(f"Uploading chunk {i+1} to OpenAI ({file_size:,} bytes)")
                        
                        start_time = time.time()
                        
                        transcript = client.audio.transcriptions.create(
                            model=model,
                            file=audio_file
                        )
                        
                        elapsed = time.time() - start_time
                        print(f"Chunk {i+1} completed: {len(transcript.text)} characters ({elapsed:.1f}s)")
                        
                        transcript_parts.append(transcript.text)
                        
                except Exception as e:
                    print(f"Error processing chunk {i+1}: {e}")
                    raise RuntimeError(f"Failed to process audio chunk {i+1}/{len(chunks)}: {e}")
                
                if temp_chunk_path and os.path.exists(temp_chunk_path):
                    os.remove(temp_chunk_path)
            
            return "\n\n".join(transcript_parts)
            
        finally:
            for p in temp_paths:
                if p and os.path.exists(p):
                    os.remove(p)
    
    def create_financial_summary(self, transcript: str, model: str = "gpt-4o") -> str:
        """Create focused financial summary with macro themes and trade ideas."""
        client = self.get_client()
        
        print(f"Creating analysis with model: {model}")
        print(f"Transcript length: {len(transcript):,} characters")
        
        analysis_prompt = """You are a senior financial analyst specializing in macro themes and market insights. Analyze this audio transcript and create a comprehensive investment research report.

STRUCTURE YOUR ANALYSIS AS FOLLOWS:

## EXECUTIVE SUMMARY
Brief 2-3 sentence overview of key investment themes

## KEY THEMES & MARKET INSIGHTS
- Identify and elaborate on 3-5 major macro themes
- Include specific market sectors, geographies, or asset classes mentioned
- Note any timeline or catalyst mentions

## TRADE IDEAS & INVESTMENT OPPORTUNITIES
- Extract specific trade ideas, stock picks, or investment strategies
- Include any mentioned price targets, entry/exit points
- Note risk management suggestions

## SUPPORTING EVIDENCE & QUOTES
For each major point, include relevant quotes from the original audio to support your analysis.

## RISK FACTORS
- Key risks or concerns mentioned
- Market or economic headwinds discussed

Focus on actionable insights for institutional investors. Be specific about sectors, companies, and timeframes when mentioned. If specific numbers, dates, or targets are mentioned, include them prominently."""

        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"Please analyze this financial audio transcript:\n\n{transcript}"}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            elapsed = time.time() - start_time
            analysis = response.choices[0].message.content
            print(f"Analysis completed: {len(analysis)} characters ({elapsed:.1f}s)")
            
            return analysis
            
        except Exception as e:
            raise RuntimeError(f"Failed to create financial analysis: {e}")
    
    def send_email_report(self, analysis: str, transcript: str, 
                         subject: str = "Financial Audio Analysis Report") -> Dict[str, Any]:
        """Send email report with analysis and transcript"""
        try:
            # Get email settings
            email_address = self.settings.get('email_address')
            email_password = self.settings.get('email_password')
            output_email = self.settings.get('output_email')
            
            if not all([email_address, email_password, output_email]):
                return {'success': False, 'message': 'Email configuration incomplete'}
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = output_email
            msg['Subject'] = subject
            
            # Email body with analysis
            body = f"""
            <html>
            <body>
            <h2>Financial Audio Analysis Report</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
            {analysis.replace('\n', '<br>')}
            </div>
            
            <h3>Full Transcript</h3>
            <div style="background-color: #f9f9f9; padding: 15px; font-family: monospace; white-space: pre-wrap;">
            {transcript}
            </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_address, email_password)
                server.send_message(msg)
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Email failed: {str(e)}'}
    
    def test_email_credentials(self) -> Dict[str, Any]:
        """Test email credentials"""
        try:
            email_address = self.settings.get('email_address')
            email_password = self.settings.get('email_password')
            
            if not email_address or not email_password:
                return {'success': False, 'message': 'Email credentials not configured'}
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_address, email_password)
            
            return {'success': True, 'message': 'Email credentials verified successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Email test failed: {str(e)}'}
    
    def process_file(self, file_path: str, job_id: str = None, jobs_dict: Dict = None) -> Dict[str, Any]:
        """Process uploaded file"""
        try:
            # Transcribe
            self.update_progress(job_id, "Transcribing audio...", jobs_dict)
            transcript = self.transcribe_audio(file_path, job_id=job_id, jobs_dict=jobs_dict)
            
            # Analyze
            self.update_progress(job_id, "Creating financial analysis...", jobs_dict)
            analysis = self.create_financial_summary(transcript)
            
            # Send email if configured
            email_result = None
            if self.settings.get('send_email', False):
                self.update_progress(job_id, "Sending email report...", jobs_dict)
                email_result = self.send_email_report(analysis, transcript)
            
            return {
                'transcript': transcript,
                'analysis': analysis,
                'email_result': email_result
            }
            
        except Exception as e:
            raise RuntimeError(f"Processing failed: {str(e)}")
    
    def process_url(self, url: str, job_id: str = None, jobs_dict: Dict = None) -> Dict[str, Any]:
        """Process URL"""
        try:
            # Download
            downloaded_file = self.download_from_url(url, job_id=job_id, jobs_dict=jobs_dict)
            
            try:
                # Process the downloaded file
                result = self.process_file(downloaded_file, job_id=job_id, jobs_dict=jobs_dict)
                return result
                
            finally:
                # Clean up downloaded file
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                    
        except Exception as e:
            raise RuntimeError(f"URL processing failed: {str(e)}")