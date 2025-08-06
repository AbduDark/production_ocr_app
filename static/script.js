
/**
 * OCR Service Frontend JavaScript
 * Production-ready with comprehensive error handling
 */

class OCRService {
    constructor() {
        this.files = [];
        this.currentTaskId = null;
        this.progressInterval = null;
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/tiff', 'image/gif', 'image/webp'];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkServiceStatus();
        this.setupDragAndDrop();
    }
    
    bindEvents() {
        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
        
        // Upload area click
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        // Process button
        document.getElementById('processBtn').addEventListener('click', () => {
            this.startProcessing();
        });
        
        // Stop button
        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopProcessing();
        });
        
        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadResults();
        });
        
        // Clear button
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clearResults();
        });
    }
    
    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
        });
        
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    async checkServiceStatus() {
        try {
            const response = await fetch('/status');
            const status = await response.json();
            
            const statusAlert = document.getElementById('statusAlert');
            const statusMessage = document.getElementById('statusMessage');
            
            if (status.status === 'ready') {
                statusAlert.className = 'alert alert-success';
                statusMessage.innerHTML = `<strong>Service Ready</strong> - Available engines: ${status.engines.map(e => e.name).join(', ')}`;
            } else if (status.status === 'limited') {
                statusAlert.className = 'alert alert-warning';
                statusMessage.innerHTML = '<strong>Limited Service</strong> - Some OCR engines unavailable. Basic text detection available.';
            } else {
                statusAlert.className = 'alert alert-danger';
                statusMessage.innerHTML = '<strong>Service Error</strong> - OCR service unavailable.';
            }
        } catch (error) {
            console.error('Status check failed:', error);
            const statusAlert = document.getElementById('statusAlert');
            const statusMessage = document.getElementById('statusMessage');
            statusAlert.className = 'alert alert-danger';
            statusMessage.innerHTML = '<strong>Connection Error</strong> - Cannot connect to OCR service.';
        }
    }
    
    handleFiles(fileList) {
        const newFiles = Array.from(fileList).filter(file => {
            // Validate file type
            if (!this.allowedTypes.includes(file.type)) {
                this.showError(`File "${file.name}" is not a supported image format.`);
                return false;
            }
            
            // Validate file size
            if (file.size > this.maxFileSize) {
                this.showError(`File "${file.name}" is too large. Maximum size is 16MB.`);
                return false;
            }
            
            // Check for duplicates
            if (this.files.some(f => f.name === file.name && f.size === file.size)) {
                this.showError(`File "${file.name}" is already added.`);
                return false;
            }
            
            return true;
        });
        
        this.files = [...this.files, ...newFiles];
        this.updateFileList();
        this.updateProcessButton();
    }
    
    updateFileList() {
        const fileList = document.getElementById('fileList');
        
        if (this.files.length === 0) {
            fileList.innerHTML = '';
            return;
        }
        
        fileList.innerHTML = this.files.map((file, index) => `
            <div class="file-item fade-in">
                <span class="file-name">${this.escapeHtml(file.name)}</span>
                <span class="file-size">${this.formatFileSize(file.size)}</span>
                <i class="fas fa-times file-remove" onclick="ocrService.removeFile(${index})"></i>
            </div>
        `).join('');
    }
    
    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFileList();
        this.updateProcessButton();
    }
    
    updateProcessButton() {
        const processBtn = document.getElementById('processBtn');
        const hasFiles = this.files.length > 0;
        const hasLanguages = this.getSelectedLanguages().length > 0;
        
        processBtn.disabled = !hasFiles || !hasLanguages;
        
        if (!hasFiles) {
            processBtn.innerHTML = '<i class="fas fa-upload"></i> Select Images First';
        } else if (!hasLanguages) {
            processBtn.innerHTML = '<i class="fas fa-language"></i> Select Languages';
        } else {
            processBtn.innerHTML = `<i class="fas fa-play"></i> Process ${this.files.length} Image(s)`;
        }
    }
    
    getSelectedLanguages() {
        const languages = [];
        if (document.getElementById('langEn').checked) languages.push('en');
        if (document.getElementById('langJa').checked) languages.push('ja');
        if (document.getElementById('langKo').checked) languages.push('ko');
        return languages;
    }
    
    async startProcessing() {
        if (this.files.length === 0 || this.getSelectedLanguages().length === 0) {
            this.showError('Please select files and languages before processing.');
            return;
        }
        
        try {
            this.showProcessingState(true);
            
            const formData = new FormData();
            this.files.forEach(file => formData.append('files', file));
            
            const mode = document.getElementById('ocrMode').value;
            formData.append('mode', mode);
            
            this.getSelectedLanguages().forEach(lang => {
                formData.append('languages', lang);
            });
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
            
            const result = await response.json();
            this.currentTaskId = result.task_id;
            this.startProgressMonitoring();
            
        } catch (error) {
            console.error('Processing failed:', error);
            this.showError(`Processing failed: ${error.message}`);
            this.showProcessingState(false);
        }
    }
    
    startProgressMonitoring() {
        this.progressInterval = setInterval(() => {
            this.checkProgress();
        }, 1000);
    }
    
    async checkProgress() {
        if (!this.currentTaskId) return;
        
        try {
            const response = await fetch(`/progress/${this.currentTaskId}`);
            if (!response.ok) {
                throw new Error('Progress check failed');
            }
            
            const progress = await response.json();
            this.updateProgress(progress);
            
            if (progress.status === 'completed') {
                this.onProcessingComplete(progress);
            } else if (progress.status === 'error') {
                this.onProcessingError(progress);
            }
            
        } catch (error) {
            console.error('Progress check failed:', error);
            this.stopProgressMonitoring();
            this.showProcessingState(false);
        }
    }
    
    updateProgress(progress) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const timeEstimate = document.getElementById('timeEstimate');
        
        progressBar.style.width = `${progress.progress}%`;
        progressBar.textContent = `${progress.progress}%`;
        
        progressText.textContent = `Processing file ${progress.files_processed + 1} of ${progress.total_files}`;
        
        if (progress.estimated_remaining) {
            timeEstimate.textContent = `Estimated time remaining: ${progress.estimated_remaining}s`;
        } else {
            timeEstimate.textContent = '';
        }
    }
    
    onProcessingComplete(progress) {
        this.stopProgressMonitoring();
        this.showProcessingState(false);
        this.displayResults(progress.results);
        this.showSuccess(`Processing completed! Extracted text from ${progress.results.length} files.`);
        
        // Enable download button
        document.getElementById('downloadBtn').disabled = false;
    }
    
    onProcessingError(progress) {
        this.stopProgressMonitoring();
        this.showProcessingState(false);
        this.showError(`Processing failed: ${progress.error || 'Unknown error'}`);
    }
    
    stopProcessing() {
        this.stopProgressMonitoring();
        this.showProcessingState(false);
        this.currentTaskId = null;
    }
    
    stopProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    showProcessingState(isProcessing) {
        const processBtn = document.getElementById('processBtn');
        const stopBtn = document.getElementById('stopBtn');
        const progressSection = document.getElementById('progressSection');
        
        if (isProcessing) {
            processBtn.disabled = true;
            stopBtn.disabled = false;
            progressSection.style.display = 'block';
            processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        } else {
            processBtn.disabled = false;
            stopBtn.disabled = true;
            progressSection.style.display = 'none';
            this.updateProcessButton();
        }
    }
    
    displayResults(results) {
        const emptyState = document.getElementById('emptyState');
        const resultsContent = document.getElementById('resultsContent');
        
        emptyState.style.display = 'none';
        resultsContent.style.display = 'block';
        
        resultsContent.innerHTML = results.map((result, index) => `
            <div class="result-item fade-in" style="animation-delay: ${index * 0.1}s">
                <div class="result-header">
                    <h5 class="result-filename">${this.escapeHtml(result.filename)}</h5>
                    ${result.processed_at ? `<span class="result-timestamp">${new Date(result.processed_at).toLocaleString()}</span>` : ''}
                </div>
                <div class="result-text">${this.escapeHtml(result.text)}</div>
            </div>
        `).join('');
    }
    
    async downloadResults() {
        if (!this.currentTaskId) {
            this.showError('No results available for download.');
            return;
        }
        
        try {
            const response = await fetch(`/download/${this.currentTaskId}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ocr_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showSuccess('Results downloaded successfully!');
            
        } catch (error) {
            console.error('Download failed:', error);
            this.showError(`Download failed: ${error.message}`);
        }
    }
    
    clearResults() {
        const emptyState = document.getElementById('emptyState');
        const resultsContent = document.getElementById('resultsContent');
        
        emptyState.style.display = 'block';
        resultsContent.style.display = 'none';
        resultsContent.innerHTML = '';
        
        document.getElementById('downloadBtn').disabled = true;
        this.currentTaskId = null;
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} fade-in`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.maxWidth = '400px';
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'check-circle'}"></i>
            ${this.escapeHtml(message)}
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Also log to console
        if (type === 'error') {
            console.error(message);
        } else {
            console.log(message);
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the service when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ocrService = new OCRService();
    
    // Update process button when language selection changes
    ['langEn', 'langJa', 'langKo'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            window.ocrService.updateProcessButton();
        });
    });
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});
