#!/usr/bin/env python3
"""
Transcription Service Module
Core financial transcription logic extracted for web application use
"""

import os
import sys
import tempfile
import time
from typing import Optional, Dict, Any

# Add parent directory to path to import from main transcribe_financial.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcribe_financial import (
    load_api_key,
    transcribe_audio,
    create_financial_summary,
    send_email_summary,
    create_pdf_report,
    download_file,
    is_url
)

class TranscriptionService:
    """Service class for handling financial transcription requests"""
    
    def __init__(self):
        self.jobs = {}  # In-memory job storage (use Redis/database in production)
    
    def create_job(self, job_id: str, input_source: str, job_type: str = "file") -> Dict[str, Any]:
        """Create a new transcription job"""
        job = {
            'id': job_id,
            'input_source': input_source,
            'type': job_type,
            'status': 'created',
            'progress': 0,
            'message': 'Job created',
            'created_at': time.time(),
            'transcript': None,
            'summary': None,
            'error': None
        }
        self.jobs[job_id] = job
        return job
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status by ID"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, progress: int = None, message: str = None, error: str = None):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status
            if progress is not None:
                self.jobs[job_id]['progress'] = progress
            if message is not None:
                self.jobs[job_id]['message'] = message
            if error is not None:
                self.jobs[job_id]['error'] = error
            self.jobs[job_id]['updated_at'] = time.time()
    
    def process_transcription(self, job_id: str, input_source: str, email_recipient: str = None, 
                            transcribe_model: str = "whisper-1", summary_model: str = "gpt-4o") -> Dict[str, Any]:
        """Process a transcription job"""
        try:
            # Check API key
            api_key = load_api_key()
            if not api_key:
                self.update_job_status(job_id, 'failed', 0, 
                                     'OpenAI API key not configured. Please go to Settings to configure your API key.', 
                                     'API key not found')
                return self.jobs[job_id]
            
            # Update job status
            self.update_job_status(job_id, 'processing', 10, 'Starting transcription...')
            
            # Step 1: Transcribe audio
            self.update_job_status(job_id, 'processing', 20, 'Transcribing audio...')
            transcript = transcribe_audio(input_source, model=transcribe_model)
            
            if not transcript or len(transcript.strip()) < 10:
                self.update_job_status(job_id, 'failed', 0, 'Transcription failed or returned empty result', 
                                     'Empty transcript')
                return self.jobs[job_id]
            
            self.jobs[job_id]['transcript'] = transcript
            self.update_job_status(job_id, 'processing', 60, f'Transcription complete ({len(transcript)} characters). Creating financial analysis...')
            
            # Step 2: Create financial summary
            self.update_job_status(job_id, 'processing', 70, 'Generating financial analysis...')
            summary = create_financial_summary(transcript, model=summary_model)
            
            if not summary:
                self.update_job_status(job_id, 'failed', 0, 'Financial analysis failed', 
                                     'Summary generation failed')
                return self.jobs[job_id]
            
            self.jobs[job_id]['summary'] = summary
            self.update_job_status(job_id, 'processing', 90, 'Financial analysis complete. Finalizing...')
            
            # Step 3: Save outputs
            os.makedirs('web/output', exist_ok=True)
            
            # Create filename based on job_id and timestamp
            timestamp = int(time.time())
            base_filename = f"financial_analysis_{job_id}_{timestamp}"
            
            # Save transcript
            transcript_path = f"web/output/{base_filename}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            # Save summary
            summary_path = f"web/output/{base_filename}_summary.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            # Create PDF report
            pdf_path = f"web/output/{base_filename}_report.pdf"
            try:
                create_pdf_report(summary, transcript, pdf_path, input_source)
                self.jobs[job_id]['pdf_path'] = pdf_path
            except Exception as e:
                print(f"Warning: PDF creation failed: {e}")
            
            self.jobs[job_id]['transcript_path'] = transcript_path
            self.jobs[job_id]['summary_path'] = summary_path
            
            # Step 4: Send email if requested
            if email_recipient:
                try:
                    self.update_job_status(job_id, 'processing', 95, 'Sending email report...')
                    send_email_summary(summary, transcript, email_recipient, 
                                     subject=f"Financial Analysis Report - {job_id}")
                    self.update_job_status(job_id, 'completed', 100, 'Analysis complete. Email sent successfully.')
                except Exception as e:
                    self.update_job_status(job_id, 'completed', 100, 
                                         f'Analysis complete. Email failed: {str(e)}')
            else:
                self.update_job_status(job_id, 'completed', 100, 'Analysis complete.')
            
            return self.jobs[job_id]
            
        except Exception as e:
            error_msg = str(e)
            self.update_job_status(job_id, 'failed', 0, f'Processing failed: {error_msg}', error_msg)
            return self.jobs[job_id]

# Global service instance
transcription_service = TranscriptionService()