#!/usr/bin/env python3
"""
LibriSeVoc API Server
A Flask web server for synthetic voice detection using the RawNet model.
"""

import os
import sys
import json
import subprocess
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
import time
from datetime import datetime
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'model.pth'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_audio_from_url(url, request_id):
    """Download audio file from URL and return local path."""
    try:
        logger.info(f"[{request_id}] Downloading audio from URL: {url}")
        
        # Parse URL to get filename
        parsed_url = urlparse(url)
        url_filename = os.path.basename(parsed_url.path)
        
        # If no filename in URL, generate one
        if not url_filename or '.' not in url_filename:
            url_filename = f"downloaded_audio_{request_id}.mp3"
        
        # Check if file extension is allowed
        if not allowed_file(url_filename):
            return None, f"Invalid file type in URL. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Create secure filename
        secure_name = secure_filename(url_filename)
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{request_id}_{secure_name}"
        local_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Download file with timeout and size limit
        headers = {
            'User-Agent': 'LibriSeVoc-API/1.0'
        }
        
        response = requests.get(
            url, 
            headers=headers,
            timeout=30,  # 30 second timeout
            stream=True
        )
        response.raise_for_status()
        
        # Check content length if provided
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB limit
            return None, "File too large. Maximum size is 100MB."
        
        # Download and save file
        total_size = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    total_size += len(chunk)
                    # Check size limit during download
                    if total_size > 100 * 1024 * 1024:  # 100MB limit
                        f.close()
                        os.remove(local_path)
                        return None, "File too large. Maximum size is 100MB."
                    f.write(chunk)
        
        logger.info(f"[{request_id}] Downloaded {total_size} bytes to {local_path}")
        return local_path, None
        
    except requests.exceptions.Timeout:
        return None, "Download timeout. URL took too long to respond."
    except requests.exceptions.RequestException as e:
        return None, f"Failed to download from URL: {str(e)}"
    except Exception as e:
        return None, f"Error downloading file: {str(e)}"

def run_evaluation(audio_file_path):
    """Run the evaluation script and return results."""
    try:
        # Build command with proper paths (no extra quotes needed for subprocess)
        cmd = [
            'python', 'eval.py',
            '--input_path', audio_file_path,
            '--model_path', MODEL_PATH
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Audio file path: {audio_file_path}")
        logger.info(f"Model path: {MODEL_PATH}")
        logger.info(f"Audio file exists: {os.path.exists(audio_file_path)}")
        logger.info(f"Model file exists: {os.path.exists(MODEL_PATH)}")
        
        # Run the evaluation
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            logger.error(f"Evaluation failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return None, f"Evaluation failed: {result.stderr}"
        
        logger.info(f"Evaluation completed successfully")
        logger.info(f"STDOUT: {result.stdout}")
        
        return result.stdout, None
        
    except subprocess.TimeoutExpired:
        error_msg = "Evaluation timed out after 5 minutes"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error running evaluation: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'LibriSeVoc API',
        'timestamp': datetime.now().isoformat(),
        'model_available': os.path.exists(MODEL_PATH)
    })

@app.route('/evaluate', methods=['POST'])
def evaluate_audio():
    """
    Evaluate audio file for synthetic voice detection.
    
    Expected request formats:
    1. File upload: multipart/form-data with 'audio' file field
    2. JSON with filename: {"filename": "path/to/audio.wav"}
    3. JSON with URL: {"url": "https://example.com/audio.mp3"}
    """
    try:
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_id}] New evaluation request received")
        
        # Check if model exists
        if not os.path.exists(MODEL_PATH):
            return jsonify({
                'error': f'Model file not found: {MODEL_PATH}',
                'request_id': request_id
            }), 500
        
        audio_file_path = None
        cleanup_file = False
        
        # Handle file upload
        if 'audio' in request.files:
            file = request.files['audio']
            if file.filename == '':
                return jsonify({
                    'error': 'No file selected',
                    'request_id': request_id
                }), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = int(time.time())
                unique_filename = f"{timestamp}_{request_id}_{filename}"
                audio_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(audio_file_path)
                cleanup_file = True
                logger.info(f"[{request_id}] File uploaded: {audio_file_path}")
            else:
                return jsonify({
                    'error': 'Invalid file type. Allowed: ' + ', '.join(ALLOWED_EXTENSIONS),
                    'request_id': request_id
                }), 400
        
        # Handle JSON request with filename or URL
        elif request.is_json:
            data = request.get_json()
            
            # Handle URL download
            if 'url' in data:
                url = data['url']
                logger.info(f"[{request_id}] Processing URL request: {url}")
                
                # Download file from URL
                downloaded_path, error = download_audio_from_url(url, request_id)
                if error:
                    return jsonify({
                        'error': error,
                        'request_id': request_id
                    }), 400
                
                audio_file_path = downloaded_path
                cleanup_file = True
                logger.info(f"[{request_id}] Downloaded file from URL: {audio_file_path}")
            
            # Handle local filename
            elif 'filename' in data:
                audio_file_path = data['filename']
                if not os.path.exists(audio_file_path):
                    return jsonify({
                        'error': f'File not found: {audio_file_path}',
                        'request_id': request_id
                    }), 400
                
                logger.info(f"[{request_id}] Using existing file: {audio_file_path}")
            
            else:
                return jsonify({
                    'error': 'Missing filename or url in request',
                    'request_id': request_id
                }), 400
        
        else:
            return jsonify({
                'error': 'No audio file provided. Use file upload, JSON with filename, or JSON with URL.',
                'request_id': request_id
            }), 400
        
        # Run evaluation
        start_time = time.time()
        output, error = run_evaluation(audio_file_path)
        processing_time = time.time() - start_time
        
        # Cleanup uploaded file if needed
        if cleanup_file and os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                logger.info(f"[{request_id}] Cleaned up uploaded file")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to cleanup file: {e}")
        
        if error:
            return jsonify({
                'error': error,
                'request_id': request_id
            }), 500
        
        # Parse output (customize based on your eval.py output format)
        response_data = {
            'request_id': request_id,
            'status': 'success',
            'processing_time_seconds': round(processing_time, 2),
            'raw_output': output.strip(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to extract structured results from output
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'Multi classification result' in line:
                    response_data['multi_classification'] = line.split(': ', 1)[1] if ': ' in line else line
                elif 'Binary classification result' in line:
                    response_data['binary_classification'] = line.split(': ', 1)[1] if ': ' in line else line
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to parse output structure: {e}")
        
        logger.info(f"[{request_id}] Evaluation completed in {processing_time:.2f}s")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'request_id': request_id
        }), 500

@app.route('/status', methods=['GET'])
def server_status():
    """Get server status and configuration."""
    return jsonify({
        'server': 'LibriSeVoc API',
        'version': '1.0.0',
        'model_path': MODEL_PATH,
        'model_exists': os.path.exists(MODEL_PATH),
        'upload_folder': UPLOAD_FOLDER,
        'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'uptime': time.time(),
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'error': 'File too large. Maximum size is 100MB.',
        'max_size_mb': 100
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET / - Health check',
            'POST /evaluate - Evaluate audio file (upload, filename, or URL)',
            'GET /status - Server status'
        ]
    }), 404

if __name__ == '__main__':
    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Model file not found: {MODEL_PATH}")
        logger.warning("Make sure to place your trained model at this path before starting the server")
    
    # Check if eval.py exists
    if not os.path.exists('eval.py'):
        logger.error("eval.py not found in current directory")
        sys.exit(1)
    
    logger.info("Starting LibriSeVoc API Server on port 8000")
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    
    # Run the server
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,
        threaded=True
    )
