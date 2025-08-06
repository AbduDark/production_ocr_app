
"""
Production OCR Flask Application
Enhanced error handling and production-ready configuration
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionOCREngine:
    """Production OCR engine with comprehensive error handling"""
    
    def __init__(self):
        self.engines = {}
        self.fallback_available = False
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available OCR engines with fallback"""
        engines_tried = []
        
        # Try EasyOCR
        try:
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['en', 'ja', 'ko'], gpu=False)
            engines_tried.append("EasyOCR - Success")
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            engines_tried.append(f"EasyOCR - Failed: {str(e)}")
            logger.warning(f"EasyOCR not available: {e}")
        
        # Try PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.engines['paddleocr'] = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            engines_tried.append("PaddleOCR - Success")
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            engines_tried.append(f"PaddleOCR - Failed: {str(e)}")
            logger.warning(f"PaddleOCR not available: {e}")
        
        # Try Tesseract
        try:
            import pytesseract
            # Test if tesseract is actually available
            pytesseract.get_tesseract_version()
            self.engines['tesseract'] = pytesseract
            engines_tried.append("Tesseract - Success")
            logger.info("Tesseract initialized successfully")
        except Exception as e:
            engines_tried.append(f"Tesseract - Failed: {str(e)}")
            logger.warning(f"Tesseract not available: {e}")
        
        # Always have OpenCV as fallback
        try:
            import cv2
            self.engines['opencv'] = cv2
            self.fallback_available = True
            engines_tried.append("OpenCV Fallback - Available")
            logger.info("OpenCV fallback initialized")
        except Exception as e:
            engines_tried.append(f"OpenCV - Failed: {str(e)}")
            logger.error("Even OpenCV fallback failed!")
        
        logger.info(f"OCR Engine initialization summary: {engines_tried}")
        
        if not self.engines:
            logger.critical("No OCR engines available! Application may not function properly.")
    
    def is_ready(self):
        """Check if at least one OCR engine is available"""
        return len(self.engines) > 0
    
    def extract_text(self, image_array, mode='normal', languages=['en']):
        """Extract text with comprehensive error handling"""
        if not self.is_ready():
            return "No OCR engines available. Please install easyocr, paddleocr, or tesseract."
        
        results = []
        errors = []
        
        try:
            # Try each engine based on mode
            if mode == 'high_accuracy':
                engines_to_try = list(self.engines.keys())
            else:
                # Normal mode - try best engines first
                engines_to_try = [eng for eng in ['easyocr', 'paddleocr', 'tesseract'] if eng in self.engines]
                if not engines_to_try and 'opencv' in self.engines:
                    engines_to_try = ['opencv']
            
            for engine_name in engines_to_try:
                try:
                    if engine_name == 'easyocr':
                        result = self._extract_with_easyocr(image_array, languages)
                    elif engine_name == 'paddleocr':
                        result = self._extract_with_paddleocr(image_array)
                    elif engine_name == 'tesseract':
                        result = self._extract_with_tesseract(image_array, languages)
                    elif engine_name == 'opencv':
                        result = self._extract_with_opencv_fallback(image_array)
                    
                    if result and result.strip():
                        if mode == 'high_accuracy':
                            results.append(f"[{engine_name.upper()}]\n{result.strip()}")
                        else:
                            results.append(result.strip())
                            break  # For normal mode, stop after first success
                            
                except Exception as e:
                    error_msg = f"{engine_name} failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            if results:
                final_result = '\n\n'.join(results)
                logger.info(f"OCR extraction successful with {len(results)} engine(s)")
                return final_result
            else:
                error_summary = '; '.join(errors) if errors else "No text detected"
                logger.warning(f"OCR extraction failed: {error_summary}")
                return f"Text extraction failed. Errors: {error_summary}"
                
        except Exception as e:
            logger.error(f"Critical OCR error: {e}")
            return f"Critical OCR error: {str(e)}"
    
    def _extract_with_easyocr(self, image_array, languages):
        """Extract with EasyOCR"""
        reader = self.engines['easyocr']
        results = reader.readtext(image_array)
        text_lines = [text for (bbox, text, confidence) in results if confidence > 0.1]
        return '\n'.join(text_lines)
    
    def _extract_with_paddleocr(self, image_array):
        """Extract with PaddleOCR"""
        ocr = self.engines['paddleocr']
        results = ocr.ocr(image_array, cls=True)
        text_lines = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1 and line[1][1] > 0.1:
                    text_lines.append(line[1][0])
        return '\n'.join(text_lines)
    
    def _extract_with_tesseract(self, image_array, languages):
        """Extract with Tesseract"""
        pytesseract = self.engines['tesseract']
        lang_map = {'en': 'eng', 'ja': 'jpn', 'ko': 'kor'}
        tesseract_langs = [lang_map.get(lang, 'eng') for lang in languages]
        lang_string = '+'.join(tesseract_langs)
        
        # Convert numpy array to PIL Image
        if len(image_array.shape) == 3:
            image_pil = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
        else:
            image_pil = Image.fromarray(image_array)
        
        text = pytesseract.image_to_string(image_pil, lang=lang_string)
        return text.strip()
    
    def _extract_with_opencv_fallback(self, image_array):
        """Basic fallback using OpenCV"""
        try:
            cv2 = self.engines['opencv']
            
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_array.copy()
            
            # Basic text region detection
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                if 0.2 < aspect_ratio < 5.0 and w > 10 and h > 10:
                    text_regions += 1
            
            if text_regions > 0:
                return f"Detected {text_regions} potential text regions. For full text extraction, please install advanced OCR engines (easyocr, paddleocr, or tesseract)."
            else:
                return "No clear text regions detected. Please try a clearer image or install advanced OCR engines."
                
        except Exception as e:
            return f"Basic text detection failed: {str(e)}"

class ImageProcessor:
    """Production image processor with enhanced error handling"""
    
    @staticmethod
    def preprocess_image(image_data):
        """Preprocess image with comprehensive error handling"""
        try:
            # Convert to numpy array
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = image_data
            
            if image is None:
                raise ValueError("Could not decode image")
            
            # Resize if too large
            height, width = image.shape[:2]
            max_dimension = 2048
            
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Basic enhancement
            # Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive threshold
            processed = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            logger.info("Image preprocessing completed successfully")
            return processed
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original or a basic fallback
            try:
                if isinstance(image_data, bytes):
                    nparr = np.frombuffer(image_data, np.uint8)
                    fallback = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                    if fallback is not None:
                        return fallback
                raise e
            except:
                raise ValueError(f"Image processing completely failed: {str(e)}")

# Initialize global components
try:
    ocr_engine = ProductionOCREngine()
    logger.info("OCR engine initialized")
except Exception as e:
    logger.critical(f"Failed to initialize OCR engine: {e}")
    ocr_engine = None

# Flask app configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key-change-this')

# Storage for processing tasks
processing_tasks = {}
task_cleanup_threshold = 3600  # 1 hour

def cleanup_old_tasks():
    """Clean up old tasks to prevent memory leaks"""
    current_time = time.time()
    tasks_to_remove = []
    
    for task_id, task in processing_tasks.items():
        task_age = current_time - task.get('created_at', current_time)
        if task_age > task_cleanup_threshold:
            tasks_to_remove.append(task_id)
    
    for task_id in tasks_to_remove:
        try:
            del processing_tasks[task_id]
            logger.info(f"Cleaned up old task: {task_id}")
        except KeyError:
            pass

@app.route('/')
def index():
    """Main page with enhanced error handling"""
    try:
        # Check OCR engine status
        ocr_status = "ready" if ocr_engine and ocr_engine.is_ready() else "limited"
        return render_template('index.html', ocr_status=ocr_status)
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return f"Error loading application: {str(e)}", 500

@app.route('/status')
def get_status():
    """Get application status"""
    try:
        if not ocr_engine:
            return jsonify({
                'status': 'error',
                'message': 'OCR engine not initialized',
                'engines': []
            })
        
        engines_status = []
        if ocr_engine.engines:
            for engine_name in ocr_engine.engines.keys():
                engines_status.append({
                    'name': engine_name,
                    'status': 'available'
                })
        
        return jsonify({
            'status': 'ready' if ocr_engine.is_ready() else 'limited',
            'message': 'OCR service is operational',
            'engines': engines_status,
            'active_tasks': len(processing_tasks)
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload with enhanced validation and error handling"""
    try:
        # Clean up old tasks
        cleanup_old_tasks()
        
        if not ocr_engine:
            return jsonify({'error': 'OCR engine not available'}), 503
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        mode = request.form.get('mode', 'normal')
        languages = request.form.getlist('languages') or ['en']
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Validate files
        valid_files = []
        for file in files:
            if file.filename:
                # Check file extension
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in allowed_extensions:
                    logger.warning(f"Rejected file with invalid extension: {file.filename}")
                    continue
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset
                
                if file_size > app.config['MAX_CONTENT_LENGTH']:
                    logger.warning(f"Rejected oversized file: {file.filename} ({file_size} bytes)")
                    continue
                
                valid_files.append(file)
        
        if not valid_files:
            return jsonify({'error': 'No valid image files found'}), 400
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task
        processing_tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'files_processed': 0,
            'total_files': len(valid_files),
            'results': [],
            'error': None,
            'created_at': time.time()
        }
        
        # Start processing in background
        thread = threading.Thread(
            target=process_images_background,
            args=(task_id, valid_files, mode, languages),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started processing task {task_id} with {len(valid_files)} files")
        return jsonify({'task_id': task_id})
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """Get processing progress with error handling"""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = processing_tasks[task_id]
        
        # Add estimated time remaining
        if task['status'] == 'processing' and task['files_processed'] > 0:
            elapsed_time = time.time() - task.get('created_at', time.time())
            avg_time_per_file = elapsed_time / task['files_processed']
            remaining_files = task['total_files'] - task['files_processed']
            estimated_remaining = avg_time_per_file * remaining_files
            task['estimated_remaining'] = round(estimated_remaining, 1)
        
        return jsonify(task)
    except Exception as e:
        logger.error(f"Progress check error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<task_id>')
def download_results(task_id):
    """Download results with enhanced error handling"""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task = processing_tasks[task_id]
        if task['status'] != 'completed':
            return jsonify({'error': 'Task not completed'}), 400
        
        if not task['results']:
            return jsonify({'error': 'No results available'}), 404
        
        # Create results content
        results_lines = []
        results_lines.append(f"OCR Results - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results_lines.append("=" * 50)
        results_lines.append("")
        
        for i, result in enumerate(task['results'], 1):
            results_lines.append(f"File {i}: {result['filename']}")
            results_lines.append("-" * 30)
            results_lines.append(result['text'])
            results_lines.append("")
        
        results_content = '\n'.join(results_lines)
        
        # Create in-memory file
        output = io.BytesIO()
        output.write(results_content.encode('utf-8'))
        output.seek(0)
        
        filename = f"ocr_results_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

def process_images_background(task_id, files, mode, languages):
    """Background processing with comprehensive error handling"""
    try:
        task = processing_tasks[task_id]
        task['status'] = 'processing'
        
        for i, file in enumerate(files):
            try:
                task['progress'] = int((i / len(files)) * 100)
                task['files_processed'] = i
                
                # Read file data
                file_data = file.read()
                filename = secure_filename(file.filename)
                
                logger.info(f"Processing file {i+1}/{len(files)}: {filename}")
                
                # Process image
                processed_image = ImageProcessor.preprocess_image(file_data)
                
                # Perform OCR
                text = ocr_engine.extract_text(processed_image, mode, languages)
                
                # Store result
                task['results'].append({
                    'filename': filename,
                    'text': text,
                    'processed_at': datetime.now().isoformat()
                })
                
                logger.info(f"Successfully processed {filename}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                # Continue with error result
                task['results'].append({
                    'filename': secure_filename(file.filename) if file.filename else f"file_{i+1}",
                    'text': f"Error processing file: {str(e)}",
                    'processed_at': datetime.now().isoformat()
                })
        
        # Mark as completed
        task['status'] = 'completed'
        task['progress'] = 100
        task['files_processed'] = len(files)
        task['completed_at'] = time.time()
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in background processing: {e}")
        task['status'] = 'error'
        task['error'] = str(e)
        task['completed_at'] = time.time()

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Ensure directories exist
def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'temp', 'results']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == '__main__':
    try:
        create_directories()
        logger.info("Starting OCR Flask application")
        
        # Production configuration
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)
