// Financial Transcription Tool - Web App JavaScript

// Global application state
window.FinancialTranscription = {
    currentJobId: null,
    pollInterval: null,
    
    // Initialize application
    init: function() {
        this.setupEventListeners();
        this.checkSystemStatus();
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Add drag and drop support for file uploads
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            this.setupFileDropZone(fileInput);
        }
        
        // Add form validation
        this.setupFormValidation();
    },
    
    // Setup drag and drop for file uploads
    setupFileDropZone: function(fileInput) {
        const dropZone = fileInput.parentElement;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            }, false);
        });
        
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this.updateFileInputLabel(fileInput, files[0].name);
            }
        }, false);
    },
    
    // Prevent default drag behaviors
    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },
    
    // Update file input label with filename
    updateFileInputLabel: function(input, filename) {
        const label = input.closest('.mb-3').querySelector('.form-text');
        if (label) {
            label.textContent = `Selected: ${filename}`;
            label.style.color = '#198754';
            label.style.fontWeight = '500';
        }
    },
    
    // Setup form validation
    setupFormValidation: function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    },
    
    // Check system status
    checkSystemStatus: function() {
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                if (!data.api_key_configured) {
                    this.showApiKeyWarning();
                }
            })
            .catch(error => {
                console.warn('Could not check system status:', error);
            });
    },
    
    // Show API key warning
    showApiKeyWarning: function() {
        const alertHtml = `
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>API Key Required:</strong> Please configure your OpenAI API key in 
                <a href="/settings" class="alert-link">Settings</a> to use the transcription service.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('main .container');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
        }
    },
    
    // Utility functions
    utils: {
        // Format file size
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Format duration
        formatDuration: function(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (hours > 0) {
                return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            } else {
                return `${minutes}:${secs.toString().padStart(2, '0')}`;
            }
        },
        
        // Show toast notification
        showToast: function(message, type = 'info') {
            const toastHtml = `
                <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            let toastContainer = document.querySelector('.toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }
            
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            const toastElement = toastContainer.lastElementChild;
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
            
            // Remove toast element after it's hidden
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.FinancialTranscription.init();
});

// Additional CSS for drag and drop
const dragDropCSS = `
    .drag-over {
        border-color: #0d6efd !important;
        background-color: #f0f8ff !important;
    }
    
    .was-validated .form-control:invalid {
        border-color: #dc3545;
    }
    
    .was-validated .form-control:valid {
        border-color: #198754;
    }
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = dragDropCSS;
document.head.appendChild(style);