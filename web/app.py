#!/usr/bin/env python3
"""
Financial Audio Transcription - Web Application
Flask web application for transcribing financial audio/video content
"""

import os
import json
import uuid
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our transcription service
from transcription_service import TranscriptionService

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'mp3', 'wav', 'mp4', 'avi', 'mov', 'mkv', 'flv', 'webm', 'm4a', 'aac', 'ogg'
}

# Store for active jobs
active_jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/save-settings', methods=['POST'])
def save_settings():
    """Save user settings"""
    try:
        settings = request.get_json()
        
        # Store in session for now (in production, use secure database)
        session['settings'] = settings
        
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-settings')
def get_settings():
    """Get user settings"""
    return jsonify(session.get('settings', {}))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        print(f"Upload request received: {request.files}")  # Debug logging
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file = request.files['file']
        print(f"File: {file.filename}, size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")  # Debug
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{job_id}_{filename}"
        file_path = app.config['UPLOAD_FOLDER'] / unique_filename
        file.save(file_path)
        
        # Start processing
        settings = session.get('settings', {})
        service = TranscriptionService(settings)
        
        def process_file():
            try:
                active_jobs[job_id] = {
                    'status': 'processing',
                    'progress': 'Starting transcription...',
                    'result': None,
                    'error': None
                }
                
                # Check if OpenAI API key is configured
                if not settings.get('openai_api_key'):
                    raise Exception("OpenAI API key not configured. Please go to Settings to configure your API key.")
                
                result = service.process_file(str(file_path), job_id, active_jobs)
                
                active_jobs[job_id].update({
                    'status': 'completed',
                    'progress': 'Transcription completed',
                    'result': result
                })
                
                # Clean up uploaded file
                try:
                    os.remove(file_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"Error processing file: {e}")  # Debug logging
                active_jobs[job_id].update({
                    'status': 'error',
                    'error': str(e)
                })
        
        # Start processing in background
        thread = threading.Thread(target=process_file)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'job_id': job_id,
            'message': 'File uploaded successfully. Processing started.'
        })
        
    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'File too large (max 500MB)'}), 413
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process-url', methods=['POST'])
def process_url():
    """Handle URL processing"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Start processing
        settings = session.get('settings', {})
        service = TranscriptionService(settings)
        
        def process_url_task():
            try:
                active_jobs[job_id] = {
                    'status': 'processing',
                    'progress': 'Downloading from URL...',
                    'result': None,
                    'error': None
                }
                
                # Check if OpenAI API key is configured
                if not settings.get('openai_api_key'):
                    raise Exception("OpenAI API key not configured. Please go to Settings to configure your API key.")
                
                result = service.process_url(url, job_id, active_jobs)
                
                active_jobs[job_id].update({
                    'status': 'completed',
                    'progress': 'Transcription completed',
                    'result': result
                })
                
            except Exception as e:
                print(f"Error processing URL: {e}")  # Debug logging
                active_jobs[job_id].update({
                    'status': 'error',
                    'error': str(e)
                })
        
        # Start processing in background
        thread = threading.Thread(target=process_url_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'job_id': job_id,
            'message': 'URL processing started.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/job-status/<job_id>')
def job_status(job_id):
    """Get job status"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(active_jobs[job_id])

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test email configuration"""
    try:
        settings = session.get('settings', {})
        service = TranscriptionService(settings)
        
        result = service.test_email_credentials()
        
        return jsonify({
            'success': result['success'],
            'message': result['message']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large (max 500MB)'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)