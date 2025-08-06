
# OCR Text Extraction Service

A production-ready web application for extracting text from images using multiple OCR engines.

## Features

- **Multiple OCR Engines**: Supports EasyOCR, PaddleOCR, and Tesseract OCR
- **Multi-language Support**: English, Japanese, and Korean text recognition
- **High Accuracy Mode**: Uses multiple engines for maximum precision
- **Batch Processing**: Process multiple images simultaneously
- **Web Interface**: Modern, responsive web interface
- **Error Handling**: Comprehensive error handling and recovery
- **Production Ready**: Optimized for deployment and scaling

## Supported Image Formats

- PNG, JPG, JPEG, BMP, TIFF, GIF, WEBP
- Maximum file size: 16MB per image
- Automatic image preprocessing and optimization

## Quick Start

### 1. Download and Extract

```bash
# Extract the application files to your desired directory
cd production_ocr_app
```

### 2. Install Dependencies

**Option A: Automatic Installation (Recommended)**
```bash
chmod +x install_and_run.sh
./install_and_run.sh
```

**Option B: Manual Installation**
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-jpn tesseract-ocr-kor
sudo apt-get install -y python3-pip python3-dev libgl1-mesa-glx

# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Run the Application

```bash
python3 app.py
```

The application will be available at `http://localhost:5000`

## Deployment Options

### 1. Development Server (Local Testing)
```bash
python3 app.py
```

### 2. Production Server with Gunicorn
```bash
# Install Gunicorn
pip3 install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Docker Deployment (Optional)
```bash
# Create Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-jpn tesseract-ocr-kor libgl1-mesa-glx
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

# Build and run
docker build -t ocr-service .
docker run -p 5000:5000 ocr-service
```

### 4. Replit Deployment (Recommended for Cloud)
1. Upload files to Replit
2. Run the application
3. Use Replit's deployment feature for production hosting

## API Endpoints

### POST /upload
Upload images for OCR processing
- **Files**: Multiple image files
- **Mode**: "normal" or "high_accuracy"
- **Languages**: Array of language codes ["en", "ja", "ko"]
- **Returns**: Task ID for tracking progress

### GET /progress/{task_id}
Check processing progress
- **Returns**: Progress status, percentage, and estimated time

### GET /download/{task_id}
Download extracted text results
- **Returns**: Text file with all extracted text

### GET /status
Check service status
- **Returns**: Available OCR engines and service health

## Configuration

### Environment Variables
```bash
# Flask configuration
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here

# Service configuration
export PORT=5000
export MAX_CONTENT_LENGTH=16777216  # 16MB

# OCR configuration
export OCR_TIMEOUT=300  # 5 minutes
```

### File Structure
```
production_ocr_app/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── style.css        # Styling
│   └── script.js        # Frontend JavaScript
├── logs/                # Application logs
├── temp/               # Temporary file storage
├── results/            # Results storage
├── requirements.txt    # Python dependencies
├── install_and_run.sh  # Installation script
└── README.md          # This file
```

## Troubleshooting

### Common Issues

**1. OCR Engines Not Available**
```bash
# Install missing OCR engines
pip3 install easyocr paddleocr pytesseract

# For Tesseract system dependency
sudo apt-get install tesseract-ocr
```

**2. OpenCV Issues**
```bash
# Install OpenCV dependencies
sudo apt-get install libgl1-mesa-glx libglib2.0-0
pip3 install opencv-python
```

**3. Memory Issues**
- Reduce image size before processing
- Use normal mode instead of high accuracy
- Process fewer images simultaneously

**4. Permission Issues**
```bash
# Create directories with proper permissions
mkdir -p logs temp results
chmod 755 logs temp results
```

### Logs and Debugging

Application logs are stored in:
- `logs/app.log` - Main application log
- Console output - Real-time processing information

Enable debug mode for development:
```bash
export FLASK_DEBUG=true
python3 app.py
```

## Performance Optimization

### For High Volume Processing
1. **Use Gunicorn with multiple workers**:
   ```bash
   gunicorn -w 4 --worker-class gevent app:app
   ```

2. **Optimize OCR settings**:
   - Use normal mode for speed
   - Process images in smaller batches
   - Implement image caching

3. **Hardware Requirements**:
   - Minimum: 2GB RAM, 1 CPU core
   - Recommended: 4GB RAM, 2+ CPU cores
   - GPU acceleration (optional for EasyOCR)

### Image Processing Tips
- **Optimal image resolution**: 300 DPI
- **File formats**: PNG for best quality, JPEG for smaller files
- **Image preprocessing**: The app automatically enhances images

## Security Considerations

### For Production Deployment
1. **Change secret key**:
   ```bash
   export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
   ```

2. **Enable HTTPS** (with reverse proxy like Nginx)

3. **File upload limits**: Already configured (16MB max)

4. **Input validation**: Comprehensive validation included

5. **Rate limiting**: Consider implementing for public deployments

## Support and Maintenance

### Regular Maintenance
- Clear temp files: `rm -rf temp/*`
- Rotate logs: `logrotate` configuration
- Update dependencies: `pip3 install -r requirements.txt --upgrade`

### Monitoring
- Check `/status` endpoint for health monitoring
- Monitor disk space in `temp/` and `logs/` directories
- Track processing times and error rates

## License

This application is provided as-is for educational and commercial use. 
OCR engines have their own licenses:
- EasyOCR: Apache 2.0 License
- PaddleOCR: Apache 2.0 License  
- Tesseract: Apache 2.0 License

## Version History

- **v1.0** - Initial production release
- Multiple OCR engine support
- Web interface and API
- Production-ready configuration
- Comprehensive error handling

For updates and support, refer to the application logs and documentation.
