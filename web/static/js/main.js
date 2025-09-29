// Main JavaScript functionality for Financial Transcription Suite

class TranscriptionApp {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSettings();
    }

    bindEvents() {
        // File input change
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                this.toggleUploadButton();
            });
        }

        // URL input change
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.addEventListener('input', () => {
                this.toggleUrlButton();
            });
        }

        // Upload button
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                this.handleFileUpload();
            });
        }

        // Process URL button
        const processUrlBtn = document.getElementById('processUrlBtn');
        if (processUrlBtn) {
            processUrlBtn.addEventListener('click', () => {
                this.handleUrlProcess();
            });
        }

        // Settings form
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }

        // Test email button
        const testEmailBtn = document.getElementById('testEmailBtn');
        if (testEmailBtn) {
            testEmailBtn.addEventListener('click', () => {
                this.testEmail();
            });
        }

        // Email checkbox
        const sendEmailCheckbox = document.getElementById('sendEmail');
        if (sendEmailCheckbox) {
            sendEmailCheckbox.addEventListener('change', () => {
                this.toggleEmailSettings();
            });
        }
    }

    toggleUploadButton() {
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        
        if (fileInput && uploadBtn) {
            uploadBtn.disabled = !fileInput.files[0];
        }
    }

    toggleUrlButton() {
        const urlInput = document.getElementById('urlInput');
        const processUrlBtn = document.getElementById('processUrlBtn');
        
        if (urlInput && processUrlBtn) {
            processUrlBtn.disabled = !urlInput.value.trim();
        }
    }

    toggleEmailSettings() {
        const sendEmailCheckbox = document.getElementById('sendEmail');
        const emailSettings = document.getElementById('emailSettings');
        
        if (sendEmailCheckbox && emailSettings) {
            if (sendEmailCheckbox.checked) {
                emailSettings.classList.remove('d-none');
            } else {
                emailSettings.classList.add('d-none');
            }
        }
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showAlert('Please select a file', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            this.showProcessingStatus('Uploading file...');
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentJobId = data.job_id;
                this.startPolling();
            } else {
                this.hideProcessingStatus();
                this.showAlert('Upload failed: ' + data.error, 'danger');
            }
        } catch (error) {
            this.hideProcessingStatus();
            this.showAlert('Upload failed: ' + error.message, 'danger');
        }
    }

    async handleUrlProcess() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput.value.trim();
        
        if (!url) {
            this.showAlert('Please enter a URL', 'warning');
            return;
        }

        try {
            this.showProcessingStatus('Processing URL...');
            
            const response = await fetch('/api/process-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (data.success) {
                this.currentJobId = data.job_id;
                this.startPolling();
            } else {
                this.hideProcessingStatus();
                this.showAlert('URL processing failed: ' + data.error, 'danger');
            }
        } catch (error) {
            this.hideProcessingStatus();
            this.showAlert('URL processing failed: ' + error.message, 'danger');
        }
    }

    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/job-status/${this.currentJobId}`);
                const data = await response.json();

                if (data.status === 'processing') {
                    this.updateStatus(data.progress);
                } else if (data.status === 'completed') {
                    this.stopPolling();
                    this.hideProcessingStatus();
                    this.showResults(data.result);
                } else if (data.status === 'error') {
                    this.stopPolling();
                    this.hideProcessingStatus();
                    this.showAlert('Processing failed: ' + data.error, 'danger');
                }
            } catch (error) {
                this.stopPolling();
                this.hideProcessingStatus();
                this.showAlert('Status check failed: ' + error.message, 'danger');
            }
        }, 2000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    showProcessingStatus(message) {
        const statusDiv = document.getElementById('processing-status');
        const statusMessage = document.getElementById('status-message');
        const uploadBtn = document.getElementById('uploadBtn');
        const processUrlBtn = document.getElementById('processUrlBtn');
        
        if (statusDiv) {
            statusDiv.classList.remove('d-none');
        }
        
        if (statusMessage) {
            statusMessage.textContent = message;
        }
        
        if (uploadBtn) uploadBtn.disabled = true;
        if (processUrlBtn) processUrlBtn.disabled = true;
    }

    updateStatus(message) {
        const statusMessage = document.getElementById('status-message');
        if (statusMessage) {
            statusMessage.textContent = message;
        }
    }

    hideProcessingStatus() {
        const statusDiv = document.getElementById('processing-status');
        const uploadBtn = document.getElementById('uploadBtn');
        const processUrlBtn = document.getElementById('processUrlBtn');
        
        if (statusDiv) {
            statusDiv.classList.add('d-none');
        }
        
        // Re-enable buttons based on input state
        this.toggleUploadButton();
        this.toggleUrlButton();
    }

    showResults(result) {
        // Show analysis
        const analysisContent = document.getElementById('analysis-content');
        if (analysisContent) {
            analysisContent.innerHTML = this.formatMarkdown(result.analysis);
        }
        
        // Show transcript
        const transcriptContent = document.getElementById('transcript-content');
        if (transcriptContent) {
            transcriptContent.innerHTML = `<pre class="transcript-text">${this.escapeHtml(result.transcript)}</pre>`;
        }
        
        // Show results section
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.classList.remove('d-none');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }

        // Show email status if available
        if (result.email_result) {
            if (result.email_result.success) {
                this.showAlert('Analysis completed and email sent successfully!', 'success');
            } else {
                this.showAlert('Analysis completed. Email failed: ' + result.email_result.message, 'warning');
            }
        } else {
            this.showAlert('Analysis completed successfully!', 'success');
        }
    }

    formatMarkdown(text) {
        // Simple markdown to HTML conversion
        return text
            .replace(/### (.*)/g, '<h5 class="text-primary mt-4 mb-3">$1</h5>')
            .replace(/## (.*)/g, '<h4 class="text-primary mt-4 mb-3">$1</h4>')
            .replace(/# (.*)/g, '<h3 class="text-primary mt-4 mb-3">$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/- (.*)/g, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.*)$/gm, '<p>$1</p>')
            .replace(/<p><li>/g, '<ul><li>')
            .replace(/<\/li><\/p>/g, '</li></ul>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Try to find an existing alert container, or create one
        let alertContainer = document.querySelector('.alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.className = 'alert-container';
            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(alertContainer, container.firstChild);
            }
        }
        
        alertContainer.innerHTML = alertHtml;
        
        // Auto-dismiss after 5 seconds for success/info alerts
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                const alert = alertContainer.querySelector('.alert');
                if (alert) {
                    alert.classList.remove('show');
                }
            }, 5000);
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/get-settings');
            const settings = await response.json();
            
            // Populate settings form if it exists
            if (document.getElementById('settingsForm')) {
                this.populateSettingsForm(settings);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    populateSettingsForm(settings) {
        const fields = [
            'openaiApiKey',
            'sendEmail',
            'emailAddress',
            'emailPassword',
            'outputEmail',
            'vimeoClientId',
            'vimeoClientSecret',
            'vimeoAccessToken'
        ];

        fields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                const settingKey = fieldId.replace(/([A-Z])/g, '_$1').toLowerCase();
                
                if (element.type === 'checkbox') {
                    element.checked = settings[settingKey] || false;
                } else {
                    element.value = settings[settingKey] || '';
                }
            }
        });

        // Show email settings if enabled
        this.toggleEmailSettings();
    }

    async saveSettings() {
        const settings = {
            openai_api_key: document.getElementById('openaiApiKey').value,
            send_email: document.getElementById('sendEmail').checked,
            email_address: document.getElementById('emailAddress').value,
            email_password: document.getElementById('emailPassword').value,
            output_email: document.getElementById('outputEmail').value,
            vimeo_client_id: document.getElementById('vimeoClientId').value,
            vimeo_client_secret: document.getElementById('vimeoClientSecret').value,
            vimeo_access_token: document.getElementById('vimeoAccessToken').value
        };

        try {
            const response = await fetch('/api/save-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();

            if (data.success) {
                this.showSettingsStatus('Settings saved successfully!', 'success');
            } else {
                this.showSettingsStatus('Error saving settings: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showSettingsStatus('Error saving settings: ' + error.message, 'danger');
        }
    }

    async testEmail() {
        const testEmailBtn = document.getElementById('testEmailBtn');
        
        if (!testEmailBtn) return;
        
        const originalHtml = testEmailBtn.innerHTML;
        testEmailBtn.disabled = true;
        testEmailBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Testing...';

        try {
            // First save current settings
            await this.saveSettings();
            
            // Then test email
            const response = await fetch('/api/test-email', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showSettingsStatus('Email test successful!', 'success');
            } else {
                this.showSettingsStatus('Email test failed: ' + data.message, 'danger');
            }
        } catch (error) {
            this.showSettingsStatus('Email test failed: ' + error.message, 'danger');
        } finally {
            testEmailBtn.disabled = false;
            testEmailBtn.innerHTML = originalHtml;
        }
    }

    showSettingsStatus(message, type) {
        const statusDiv = document.getElementById('settingsStatus');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.transcriptionApp = new TranscriptionApp();
});