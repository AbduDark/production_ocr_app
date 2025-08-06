
#!/bin/bash

# OCR Service Installation and Setup Script
# This script installs dependencies and runs the OCR service

echo "==================================="
echo "OCR Service Installation Script"
echo "==================================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Create logs directory
echo "Creating necessary directories..."
mkdir -p logs temp results

# Install system dependencies for OCR engines
echo "Installing system dependencies..."

# Update package list
if command -v apt-get &> /dev/null; then
    echo "Detected Ubuntu/Debian system"
    sudo apt-get update
    
    # Install Tesseract OCR
    echo "Installing Tesseract OCR..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-jpn tesseract-ocr-kor
    
    # Install other dependencies
    sudo apt-get install -y python3-pip python3-dev
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
    
elif command -v yum &> /dev/null; then
    echo "Detected CentOS/RHEL system"
    sudo yum update -y
    
    # Install Tesseract OCR
    sudo yum install -y epel-release
    sudo yum install -y tesseract tesseract-langpack-eng tesseract-langpack-jpn tesseract-langpack-kor
    
    # Install other dependencies
    sudo yum install -y python3-pip python3-devel
    sudo yum install -y mesa-libGL glib2 libSM libXext libXrender libgomp
    
elif command -v brew &> /dev/null; then
    echo "Detected macOS system"
    
    # Install Tesseract OCR
    echo "Installing Tesseract OCR..."
    brew install tesseract tesseract-lang
    
else
    echo "Warning: Unknown system. You may need to install Tesseract OCR manually."
    echo "Visit: https://github.com/tesseract-ocr/tesseract"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade pip

# Install core requirements first
echo "Installing core requirements..."
pip3 install Flask==3.0.3 Werkzeug==3.0.3
pip3 install opencv-python==4.11.0.86 Pillow==11.3.0 numpy==2.3.2

# Install OCR engines with error handling
echo "Installing OCR engines..."

# Try to install EasyOCR
echo "Installing EasyOCR..."
if pip3 install easyocr==1.7.1; then
    echo "✓ EasyOCR installed successfully"
else
    echo "⚠ EasyOCR installation failed"
fi

# Try to install PaddleOCR
echo "Installing PaddleOCR..."
if pip3 install paddlepaddle==2.6.0 paddleocr==2.7.3; then
    echo "✓ PaddleOCR installed successfully"
else
    echo "⚠ PaddleOCR installation failed"
fi

# Try to install pytesseract
echo "Installing pytesseract..."
if pip3 install pytesseract==0.3.10; then
    echo "✓ pytesseract installed successfully"
else
    echo "⚠ pytesseract installation failed"
fi

# Install optional dependencies
echo "Installing optional dependencies..."
pip3 install python-dateutil==2.8.2

# Install production server
echo "Installing Gunicorn for production..."
if pip3 install gunicorn==21.2.0; then
    echo "✓ Gunicorn installed successfully"
else
    echo "⚠ Gunicorn installation failed"
fi

echo ""
echo "==================================="
echo "Installation completed!"
echo "==================================="

# Check OCR engines
echo "Checking OCR engines availability..."

# Check EasyOCR
if python3 -c "import easyocr; print('✓ EasyOCR: Available')" 2>/dev/null; then
    echo "✓ EasyOCR: Available"
else
    echo "✗ EasyOCR: Not available"
fi

# Check PaddleOCR
if python3 -c "import paddleocr; print('✓ PaddleOCR: Available')" 2>/dev/null; then
    echo "✓ PaddleOCR: Available"
else
    echo "✗ PaddleOCR: Not available"
fi

# Check Tesseract
if python3 -c "import pytesseract; pytesseract.get_tesseract_version(); print('✓ Tesseract: Available')" 2>/dev/null; then
    echo "✓ Tesseract: Available"
else
    echo "✗ Tesseract: Not available"
fi

# Check OpenCV
if python3 -c "import cv2; print('✓ OpenCV: Available')" 2>/dev/null; then
    echo "✓ OpenCV: Available"
else
    echo "✗ OpenCV: Not available"
fi

echo ""
echo "==================================="
echo "Starting OCR Service..."
echo "==================================="

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Start the service
echo "Starting Flask application on http://0.0.0.0:5000"
echo "Press Ctrl+C to stop the service"
echo ""

python3 app.py
