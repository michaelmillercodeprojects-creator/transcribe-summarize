#!/usr/bin/env python3
"""
Financial Transcription Web Application
Flask-based web interface for financial audio transcription and analysis
"""

import os
import sys
import uuid
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcription_service import transcription_service
from transcribe_financial import load_api_key, is_url

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'web/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'mp4', 'mov', 'avi', 'webm', 'flv', 'mkv'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('web/output', exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_settings():
    """Load application settings from .env file"""
    settings = {
        'openai_api_key': load_api_key(),
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_password': os.getenv('SENDER_PASSWORD', ''),
        'output_email': os.getenv('OUTPUT_EMAIL', '')
    }
    return settings

def save_settings(settings):
    """Save application settings to .env file"""
    try:
        env_lines = []
        
        # Read existing .env file
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not any(line.startswith(key + '=') for key in settings.keys()):
                        env_lines.append(line)
        
        # Add new settings
        for key, value in settings.items():
            if value:  # Only save non-empty values
                if key == 'openai_api_key':
                    env_lines.append(f'OPENAI_API_KEY={value}')
                elif key == 'sender_email':
                    env_lines.append(f'SENDER_EMAIL={value}')
                elif key == 'sender_password':
                    env_lines.append(f'SENDER_PASSWORD={value}')
                elif key == 'output_email':
                    env_lines.append(f'OUTPUT_EMAIL={value}')
        
        # Write back to .env file
        with open('.env', 'w') as f:
            f.write('\\n'.join(env_lines) + '\\n')
        
        # Update environment variables
        for key, value in settings.items():
            if value:
                if key == 'openai_api_key':
                    os.environ['OPENAI_API_KEY'] = value
                elif key == 'sender_email':
                    os.environ['SENDER_EMAIL'] = value
                elif key == 'sender_password':
                    os.environ['SENDER_PASSWORD'] = value
                elif key == 'output_email':
                    os.environ['OUTPUT_EMAIL'] = value
        
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

@app.route('/')
def index():
    """Main page with file upload and URL processing forms"""
    return render_template('index.html')

@app.route('/settings')
def settings():
    """Settings page for API keys and email configuration"""
    current_settings = load_settings()
    return render_template('settings.html', settings=current_settings)

@app.route('/save_settings', methods=['POST'])
def save_settings_route():
    """Save application settings"""
    settings = {
        'openai_api_key': request.form.get('openai_api_key', '').strip(),
        'sender_email': request.form.get('sender_email', '').strip(),
        'sender_password': request.form.get('sender_password', '').strip(),
        'output_email': request.form.get('output_email', '').strip()
    }
    
    if save_settings(settings):
        flash('Settings saved successfully!', 'success')
    else:
        flash('Error saving settings. Please try again.', 'error')
    
    return redirect(url_for('settings'))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Check API key
        api_key = load_api_key()
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured. Please go to Settings to configure your API key.'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Create job
        job_id = str(uuid.uuid4())
        job = transcription_service.create_job(job_id, filepath, 'file')
        
        # Get email recipient from form
        email_recipient = request.form.get('email_recipient', '').strip()
        
        # Start processing in background thread
        def process_job():
            transcription_service.process_transcription(
                job_id, filepath, email_recipient
            )
        
        thread = threading.Thread(target=process_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'File uploaded successfully. Processing started.',
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/process_url', methods=['POST'])
def process_url():
    """Handle URL processing"""
    try:
        url = request.form.get('url', '').strip()
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        if not is_url(url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Check API key
        api_key = load_api_key()
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured. Please go to Settings to configure your API key.'}), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        job = transcription_service.create_job(job_id, url, 'url')
        
        # Get email recipient from form
        email_recipient = request.form.get('email_recipient', '').strip()
        
        # Start processing in background thread
        def process_job():
            transcription_service.process_transcription(
                job_id, url, email_recipient
            )
        
        thread = threading.Thread(target=process_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'URL processing started.',
            'url': url
        })
        
    except Exception as e:
        return jsonify({'error': f'URL processing failed: {str(e)}'}), 500

@app.route('/job_status/<job_id>')
def job_status(job_id):
    """Get job status"""
    job = transcription_service.get_job_status(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)

@app.route('/download/<job_id>/<file_type>')
def download_file(job_id, file_type):
    """Download job results"""
    job = transcription_service.get_job_status(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    try:
        if file_type == 'transcript':
            filepath = job.get('transcript_path')
            filename = f"transcript_{job_id}.txt"
        elif file_type == 'summary':
            filepath = job.get('summary_path')
            filename = f"summary_{job_id}.txt"
        elif file_type == 'pdf':
            filepath = job.get('pdf_path')
            filename = f"report_{job_id}.pdf"
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_key_configured': bool(load_api_key())
    })

if __name__ == '__main__':
    print("Starting Financial Transcription Web Application...")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"API key configured: {bool(load_api_key())}")
    print("Access the application at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)