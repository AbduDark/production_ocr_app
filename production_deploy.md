
# Production Deployment Guide

## Deployment on Replit (Recommended)

### Step 1: Upload to Replit
1. Create a new Repl on Replit
2. Upload all files from `production_ocr_app/` folder
3. Ensure file structure is maintained

### Step 2: Configure Replit
1. Set the run command in `.replit` file:
   ```
   run = "python3 app.py"
   ```

2. The app will automatically install dependencies from `pyproject.toml`

### Step 3: Deploy
1. Click the "Deploy" button in Replit
2. Choose "Autoscale" deployment
3. Configure settings:
   - **Run command**: `python3 app.py`
   - **Build command**: Leave empty
   - **Machine**: 1vCPU, 2GB RAM (minimum)

## Alternative Deployment Options

### 1. VPS/Cloud Server Deployment

**Requirements:**
- Ubuntu 20.04+ or similar Linux distribution
- 2GB RAM minimum (4GB recommended)
- 10GB disk space
- Python 3.8+

**Installation:**
```bash
# Clone or upload your application
cd /var/www/
sudo mkdir ocr-service
cd ocr-service

# Copy application files
# (Upload your production_ocr_app files here)

# Run installation script
chmod +x install_and_run.sh
sudo ./install_and_run.sh

# For production, use systemd service
sudo cp ocr-service.service /etc/systemd/system/
sudo systemctl enable ocr-service
sudo systemctl start ocr-service
```

**Create systemd service file** (`ocr-service.service`):
```ini
[Unit]
Description=OCR Text Extraction Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ocr-service
Environment=PATH=/var/www/ocr-service/venv/bin
Environment=FLASK_ENV=production
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Nginx Reverse Proxy (Production)

**Install Nginx:**
```bash
sudo apt-get install nginx
```

**Configure Nginx** (`/etc/nginx/sites-available/ocr-service`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
    
    location /static {
        alias /var/www/ocr-service/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/ocr-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs temp results

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/status || exit 1

# Run application
CMD ["python3", "app.py"]
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  ocr-service:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
    volumes:
      - ./logs:/app/logs
      - ./results:/app/results
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
    depends_on:
      - ocr-service
    restart: unless-stopped
```

**Deploy with Docker:**
```bash
docker-compose up -d
```

## Security Configuration

### 1. SSL/HTTPS Setup (Let's Encrypt)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall Configuration
```bash
# Enable UFW
sudo ufw enable

# Allow necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

# Block direct access to Flask port
sudo ufw deny 5000
```

### 3. Environment Variables
Create `.env` file:
```bash
# Flask configuration
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-here
DEBUG=False

# Service configuration
PORT=5000
HOST=127.0.0.1
MAX_CONTENT_LENGTH=16777216

# OCR configuration
OCR_TIMEOUT=300
MAX_WORKERS=4
```

Load in application:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Monitoring and Maintenance

### 1. Log Management
```bash
# Logrotate configuration
sudo nano /etc/logrotate.d/ocr-service

# Content:
/var/www/ocr-service/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload ocr-service
    endscript
}
```

### 2. Performance Monitoring
```bash
# Monitor system resources
htop
df -h
free -h

# Monitor application
sudo journalctl -u ocr-service -f

# Monitor nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Database Backup (if applicable)
```bash
# For result storage (if implemented)
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/ocr-service"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/ocr-backup-$DATE.tar.gz /var/www/ocr-service/results/

# Keep only last 30 days
find $BACKUP_DIR -name "ocr-backup-*.tar.gz" -mtime +30 -delete
```

## Scaling Considerations

### 1. Load Balancing
For high traffic, use multiple instances:

```yaml
# docker-compose-scaled.yml
version: '3.8'

services:
  ocr-service:
    build: .
    environment:
      - FLASK_ENV=production
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - ocr-service
```

### 2. Redis for Task Queue (Advanced)
For high-volume processing, implement Redis-based task queue:

```python
# Add to requirements.txt
redis==4.5.1
celery==5.3.1

# Worker configuration
from celery import Celery

celery = Celery('ocr_worker', broker='redis://localhost:6379')

@celery.task
def process_image_async(image_data, settings):
    # Async processing logic
    pass
```

## Troubleshooting Production Issues

### Common Problems:

1. **High Memory Usage**
   ```bash
   # Monitor memory
   watch -n 1 free -h
   
   # Restart service if needed
   sudo systemctl restart ocr-service
   ```

2. **Disk Space Issues**
   ```bash
   # Clean temp files
   find /var/www/ocr-service/temp -type f -mtime +1 -delete
   
   # Clean old logs
   sudo logrotate -f /etc/logrotate.d/ocr-service
   ```

3. **Performance Issues**
   ```bash
   # Check process stats
   sudo systemctl status ocr-service
   
   # Adjust worker count
   # Modify gunicorn command: -w 4 (workers)
   ```

4. **OCR Engine Failures**
   ```bash
   # Test OCR engines
   python3 -c "import easyocr; print('EasyOCR OK')"
   python3 -c "import paddleocr; print('PaddleOCR OK')"
   python3 -c "import pytesseract; print('Tesseract OK')"
   ```

## Maintenance Schedule

### Daily:
- Check application logs
- Monitor disk space
- Verify service status

### Weekly:
- Update system packages
- Clean temporary files
- Review performance metrics

### Monthly:
- Update Python dependencies
- Security audit
- Backup configuration files

For additional support, refer to the main README.md file and application logs.
