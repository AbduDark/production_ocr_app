
# OCR Service - Railway Optimized

Production-ready OCR text extraction service optimized for Railway limited plan and Replit deployment.

## Features

- **Memory Optimized**: Reduced memory footprint for limited hosting
- **Railway Ready**: Configured for Railway's free tier limitations
- **Multiple OCR Engines**: EasyOCR, Tesseract, OpenCV fallback
- **File Upload**: Support for PNG, JPG, JPEG, BMP (max 8MB)
- **Real-time Progress**: Track processing status
- **Download Results**: Get extracted text as downloadable file

## Quick Deploy on Replit

1. **Fork/Upload**: Upload all files to a new Repl
2. **Run**: Click the Run button - dependencies install automatically
3. **Deploy**: Use Replit's Deploy feature for production

## Deploy on Railway (Alternative)

1. **Connect Repository**: Connect your GitHub repo to Railway
2. **Environment Variables**: Set `SECRET_KEY` in Railway dashboard
3. **Deploy**: Railway automatically detects Flask and deploys

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Configuration

### Environment Variables
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Flask secret key for sessions

### Resource Limits (Railway Optimized)
- **File Size**: 8MB maximum per file
- **Concurrent Files**: 3 files maximum per upload
- **Concurrent Tasks**: 2 tasks maximum
- **Image Size**: Auto-resized to 1024px max dimension
- **OCR Languages**: English only (memory optimization)

## API Endpoints

### POST /upload
Upload images for OCR processing
- **Files**: Up to 3 image files (PNG, JPG, JPEG, BMP)
- **Returns**: Task ID for progress tracking

### GET /progress/{task_id}
Check processing progress
- **Returns**: Status, progress percentage, results count

### GET /download/{task_id}
Download extracted text
- **Returns**: Text file with all extracted content

### GET /health
Health check endpoint for Railway
- **Returns**: Service status and OCR availability

## Memory Optimization Features

- **Aggressive Cleanup**: Automatic task cleanup after 30 minutes
- **Single Engine Priority**: Uses best available OCR engine only
- **Image Compression**: Auto-resize large images
- **Memory Management**: Force garbage collection after processing
- **Synchronous Processing**: Optimized for Railway's threading model

## Supported OCR Engines

1. **EasyOCR** (Primary): Best accuracy, English only for memory efficiency
2. **Tesseract** (Backup): System-dependent installation
3. **OpenCV** (Fallback): Basic text region detection

## Production Features

- **Error Handling**: Comprehensive error responses
- **Logging**: Production-level logging (warnings and errors only)
- **Rate Limiting**: Built-in concurrent task limiting
- **Security**: File validation and secure filename handling
- **Health Monitoring**: `/health` endpoint for monitoring

## Railway Deployment Notes

- **Memory**: Optimized for Railway's 512MB limit
- **Disk Usage**: No persistent file storage used
- **Networking**: Configured for Railway's proxy setup
- **Scaling**: Single instance optimized (no horizontal scaling needed)

## Troubleshooting

### Common Issues

**Memory Errors on Railway**
- Reduce image sizes before upload
- Process fewer files simultaneously
- Service automatically cleans up old tasks

**OCR Engine Not Available**
- EasyOCR installs automatically from requirements.txt
- Tesseract requires system installation (available on Railway)
- OpenCV fallback always available

**Upload Failures**
- Check file size (8MB maximum)
- Ensure valid image format (PNG, JPG, JPEG, BMP)
- Wait for previous tasks to complete

### Performance Tips

- **Image Quality**: 300 DPI recommended for best OCR results
- **File Format**: PNG for best quality, JPEG for smaller size
- **Image Size**: Service auto-optimizes, but smaller images process faster
- **Concurrent Processing**: Maximum 2 tasks to prevent memory issues

## Support

This application is optimized for Railway limited plans and Replit hosting. For deployment issues, check:

1. Environment variables are set correctly
2. All dependencies installed from requirements.txt
3. Health check endpoint `/health` returns success
4. Check Railway/Replit logs for detailed error messages

## Security

- File size and type validation
- Secure filename handling
- No persistent file storage
- Memory cleanup after processing
- Production-level error handling
