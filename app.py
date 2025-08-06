
"""
Production OCR Flask Application
Optimized for Railway Limited Plan and Replit deployment
"""

import os
import sys
import uuid
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import numpy as np
import cv2
from PIL import Image
import io
import traceback
import gc

# Configure logging for production
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Only console output
)
logger = logging.getLogger(__name__)

class OptimizedOCREngine:
    """Lightweight OCR engine optimized for limited resources"""
    
    def __init__(self):
        self.engines = {}
        self.fallback_available = False
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available OCR engines with memory optimization"""
        # Try EasyOCR first (most reliable)
        try:
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['en'], gpu=False)  # Only English to save memory
            logger.info("EasyOCR initialized")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")
        
        # Try Tesseract as backup
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.engines['tesseract'] = pytesseract
            logger.info("Tesseract initialized")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
        
        # Always have OpenCV fallback
        try:
            import cv2
            self.engines['opencv'] = cv2
            self.fallback_available = True
            logger.info("OpenCV fallback available")
        except Exception as e:
            logger.error(f"OpenCV failed: {e}")
        
        if not self.engines:
            logger.critical("No OCR engines available!")
    
    def is_ready(self):
        return len(self.engines) > 0
    
    def extract_text(self, image_array, mode='normal', languages=['en']):
        """Extract text with memory management"""
        if not self.is_ready():
            return "No OCR engines available"
        
        try:
            # Use only the best available engine to save memory
            if 'easyocr' in self.engines:
                reader = self.engines['easyocr']
                results = reader.readtext(image_array)
                text_lines = [text for (bbox, text, confidence) in results if confidence > 0.3]
                result = '\n'.join(text_lines)
            elif 'tesseract' in self.engines:
                pytesseract = self.engines['tesseract']
                if len(image_array.shape) == 3:
                    image_pil = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
                else:
                    image_pil = Image.fromarray(image_array)
                result = pytesseract.image_to_string(image_pil, lang='eng').strip()
            else:
                # OpenCV fallback
                result = self._opencv_fallback(image_array)
            
            # Force garbage collection
            gc.collect()
            return result if result.strip() else "No text detected"
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            gc.collect()
            return f"OCR processing failed: {str(e)}"
    
    def _opencv_fallback(self, image_array):
        """Minimal OpenCV fallback"""
        try:
            cv2 = self.engines['opencv']
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_array.copy()
            
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                if 0.2 < aspect_ratio < 5.0 and w > 10 and h > 10:
                    text_regions += 1
            
            if text_regions > 0:
                return f"Detected {text_regions} text regions. Install EasyOCR for full text extraction."
            return "No clear text regions detected."
            
        except Exception as e:
            return f"Basic text detection failed: {str(e)}"

class LightweightImageProcessor:
    """Memory-optimized image processor"""
    
    @staticmethod
    def preprocess_image(image_data, max_size=1024):
        """Lightweight image preprocessing"""
        try:
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = image_data
            
            if image is None:
                raise ValueError("Could not decode image")
            
            # Aggressive resizing for memory efficiency
            height, width = image.shape[:2]
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Simple grayscale conversion
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Basic enhancement only
            enhanced = cv2.medianBlur(gray, 3)
            processed = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            return processed
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ValueError(f"Image processing failed: {str(e)}")

# Initialize components
ocr_engine = OptimizedOCREngine()
image_processor = LightweightImageProcessor()

# Flask app configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB limit for Railway
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'railway-production-key')

# In-memory task storage (no file system usage)
processing_tasks = {}

def cleanup_tasks():
    """Aggressive task cleanup for memory management"""
    current_time = time.time()
    tasks_to_remove = [
        task_id for task_id, task in processing_tasks.items()
        if current_time - task.get('created_at', current_time) > 1800  # 30 minutes
    ]
    
    for task_id in tasks_to_remove:
        processing_tasks.pop(task_id, None)
    
    # Force garbage collection
    gc.collect()

@app.route('/')
def index():
    """Main page"""
    try:
        cleanup_tasks()
        ocr_status = "ready" if ocr_engine.is_ready() else "limited"
        return render_template('index.html', ocr_status=ocr_status)
    except Exception as e:
        logger.error(f"Index page error: {e}")
        return f"Application error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'ocr_ready': ocr_engine.is_ready(),
        'active_tasks': len(processing_tasks)
    })

@app.route('/status')
def get_status():
    """Service status"""
    try:
        cleanup_tasks()
        engines_status = [{'name': name, 'status': 'available'} for name in ocr_engine.engines.keys()]
        
        return jsonify({
            'status': 'ready' if ocr_engine.is_ready() else 'limited',
            'engines': engines_status,
            'active_tasks': len(processing_tasks),
            'memory_optimized': True
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload with strict limits"""
    try:
        cleanup_tasks()
        
        if not ocr_engine.is_ready():
            return jsonify({'error': 'OCR service unavailable'}), 503
        
        # Limit concurrent tasks for Railway
        if len(processing_tasks) >= 2:
            return jsonify({'error': 'Server busy. Please try again in a few minutes.'}), 429
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        mode = 'normal'  # Force normal mode only
        languages = ['en']  # Force English only
        
        # Limit to 3 files max for Railway
        if len(files) > 3:
            return jsonify({'error': 'Maximum 3 files allowed'}), 400
        
        valid_files = []
        for file in files:
            if file.filename:
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext in allowed_extensions:
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size <= app.config['MAX_CONTENT_LENGTH']:
                        valid_files.append(file)
        
        if not valid_files:
            return jsonify({'error': 'No valid files found'}), 400
        
        task_id = str(uuid.uuid4())
        processing_tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'files_processed': 0,
            'total_files': len(valid_files),
            'results': [],
            'created_at': time.time()
        }
        
        # Process synchronously for Railway (no threading issues)
        thread = threading.Thread(
            target=process_images_sync,
            args=(task_id, valid_files),
            daemon=True
        )
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum 8MB per file.'}), 413
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """Get processing progress"""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = processing_tasks[task_id]
        return jsonify(task)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<task_id>')
def download_results(task_id):
    """Download results"""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = processing_tasks[task_id]
        if task['status'] != 'completed':
            return jsonify({'error': 'Task not completed'}), 400
        
        if not task['results']:
            return jsonify({'error': 'No results available'}), 404
        
        # Create results
        results_lines = [
            f"OCR Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50, ""
        ]
        
        for i, result in enumerate(task['results'], 1):
            results_lines.extend([
                f"File {i}: {result['filename']}",
                "-" * 30,
                result['text'],
                ""
            ])
        
        results_content = '\n'.join(results_lines)
        output = io.BytesIO(results_content.encode('utf-8'))
        output.seek(0)
        
        filename = f"ocr_results_{task_id[:8]}.txt"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

def process_images_sync(task_id, files):
    """Synchronous processing optimized for Railway"""
    try:
        task = processing_tasks[task_id]
        task['status'] = 'processing'
        
        for i, file in enumerate(files):
            try:
                task['progress'] = int((i / len(files)) * 100)
                task['files_processed'] = i
                
                file_data = file.read()
                filename = secure_filename(file.filename)
                
                # Process image with memory optimization
                processed_image = image_processor.preprocess_image(file_data)
                text = ocr_engine.extract_text(processed_image, 'normal', ['en'])
                
                task['results'].append({
                    'filename': filename,
                    'text': text,
                    'processed_at': datetime.now().isoformat()
                })
                
                # Force cleanup after each file
                del file_data, processed_image
                gc.collect()
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                task['results'].append({
                    'filename': secure_filename(file.filename),
                    'text': f"Error: {str(e)}",
                    'processed_at': datetime.now().isoformat()
                })
        
        task['status'] = 'completed'
        task['progress'] = 100
        task['files_processed'] = len(files)
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        task['status'] = 'error'
        task['error'] = str(e)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        # Railway/Replit configuration
        port = int(os.environ.get('PORT', 5000))
        
        logger.info("Starting optimized OCR service for Railway/Replit")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except Exception as e:
        logger.critical(f"Failed to start: {e}")
        sys.exit(1)
