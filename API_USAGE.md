# LibriSeVoc API Server Usage Guide

## Overview
This API server provides HTTP endpoints for synthetic voice detection using the RawNet model. It runs on port 8000 and accepts audio files for evaluation.

## Quick Start

### 1. Setup and Start Server
```bash
# Make sure you're in the LibriSeVoc directory
cd LibriSeVoc

# Activate virtual environment
source venv/bin/activate

# Start server (foreground)
python server.py

# OR start in background
chmod +x run_server_background.sh
./run_server_background.sh start
```

### 2. Test the Server
```bash
# Health check
curl http://localhost:8000/

# Server status
curl http://localhost:8000/status
```

## API Endpoints

### GET / - Health Check
Returns basic server health information.

**Response:**
```json
{
  "status": "healthy",
  "service": "LibriSeVoc API",
  "timestamp": "2024-01-01T12:00:00",
  "model_available": true
}
```

### GET /status - Server Status
Returns detailed server configuration and status.

**Response:**
```json
{
  "server": "LibriSeVoc API",
  "version": "1.0.0",
  "model_path": "model.pth",
  "model_exists": true,
  "upload_folder": "uploads",
  "max_file_size_mb": 100,
  "allowed_extensions": ["wav", "mp3", "flac", "ogg", "m4a"]
}
```

### POST /evaluate - Evaluate Audio File
Evaluates an audio file for synthetic voice detection.

#### Method 1: File Upload
Upload an audio file directly:

```bash
curl -X POST \
  -F "audio=@/path/to/your/audio.wav" \
  http://localhost:8000/evaluate
```

#### Method 2: JSON with Filename
Reference an existing file on the server:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename": "Mira Talking White Background.wav"}' \
  http://localhost:8000/evaluate
```

#### Response Format
```json
{
  "request_id": "abc123ef",
  "status": "success",
  "processing_time_seconds": 2.34,
  "raw_output": "Multi classification result: ...\nBinary classification result: ...",
  "multi_classification": "gt:0.1, wavegrad:0.2, diffwave:0.1, ...",
  "binary_classification": "fake:0.3, real:0.7",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Server Management

### Background Server Control
```bash
# Start server in background
./run_server_background.sh start

# Check server status
./run_server_background.sh status

# View recent logs
./run_server_background.sh logs

# Stop server
./run_server_background.sh stop

# Restart server
./run_server_background.sh restart
```

### Manual Server Control
```bash
# Start server in foreground (development)
python server.py

# Start with custom port (if needed)
# Edit server.py and change port=8000 to desired port
```

## Example Usage Scripts

### Python Client Example
```python
import requests
import json

# Method 1: Upload file
with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/evaluate',
        files={'audio': f}
    )
    result = response.json()
    print(json.dumps(result, indent=2))

# Method 2: Use existing file
response = requests.post(
    'http://localhost:8000/evaluate',
    json={'filename': 'Mira Talking White Background.wav'}
)
result = response.json()
print(json.dumps(result, indent=2))
```

### Bash/cURL Examples
```bash
# Upload and evaluate audio file
curl -X POST \
  -F "audio=@audio.wav" \
  http://localhost:8000/evaluate | jq

# Evaluate existing file on server
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename": "Mira Talking White Background.wav"}' \
  http://localhost:8000/evaluate | jq

# Health check
curl http://localhost:8000/ | jq
```

### JavaScript/Node.js Example
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// Upload file
const form = new FormData();
form.append('audio', fs.createReadStream('audio.wav'));

axios.post('http://localhost:8000/evaluate', form, {
  headers: form.getHeaders()
}).then(response => {
  console.log(JSON.stringify(response.data, null, 2));
}).catch(error => {
  console.error('Error:', error.response.data);
});

// Use existing file
axios.post('http://localhost:8000/evaluate', {
  filename: 'Mira Talking White Background.wav'
}).then(response => {
  console.log(JSON.stringify(response.data, null, 2));
}).catch(error => {
  console.error('Error:', error.response.data);
});
```

## Configuration

### File Limits
- Maximum file size: 100MB
- Supported formats: WAV, MP3, FLAC, OGG, M4A
- Processing timeout: 5 minutes per request

### Server Configuration
- Host: 0.0.0.0 (accepts connections from any IP)
- Port: 8000
- Threading: Enabled for concurrent requests
- Logging: Both file (server.log) and console

### Required Files
- `model.pth` - Your trained RawNet model
- `eval.py` - Evaluation script
- `server.py` - API server code
- Virtual environment with all dependencies

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -tulpn | grep :8000

# Check if model file exists
ls -la model.pth

# Check if virtual environment is activated
which python
```

### Evaluation Errors
```bash
# Check server logs
tail -f server.log

# Test evaluation script directly
python eval.py --input_path "test.wav" --model_path "model.pth"
```

### Permission Issues
```bash
# Make scripts executable
chmod +x start_server.sh
chmod +x run_server_background.sh

# Check file permissions
ls -la *.sh *.py
```

## Production Deployment

### Using systemd (Linux)
Create `/etc/systemd/system/librisevoc.service`:

```ini
[Unit]
Description=LibriSeVoc API Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/LibriSeVoc
ExecStart=/path/to/LibriSeVoc/venv/bin/python server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable librisevoc
sudo systemctl start librisevoc
sudo systemctl status librisevoc
```

### Using Docker
```dockerfile
FROM ubuntu:22.04
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y python3.12 python3.12-venv
RUN python3.12 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
EXPOSE 8000
CMD ["./venv/bin/python", "server.py"]
```

### Using PM2 (Node.js Process Manager)
```bash
npm install -g pm2
pm2 start server.py --interpreter python3 --name librisevoc-api
pm2 startup
pm2 save
```
