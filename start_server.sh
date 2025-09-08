#!/bin/bash
# LibriSeVoc API Server Startup Script

set -e

echo "🚀 Starting LibriSeVoc API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if model file exists
if [ ! -f "model.pth" ]; then
    echo "⚠️  Warning: model.pth not found. Please place your trained model in the current directory."
    echo "   The server will start but /evaluate endpoint will return errors until model is available."
fi

# Check if eval.py exists
if [ ! -f "eval.py" ]; then
    echo "❌ eval.py not found. Cannot start server."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

# Start the server
echo "✅ Starting server on port 8000..."
echo "📍 Server will be available at: http://0.0.0.0:8000"
echo "📍 Health check: http://0.0.0.0:8000/"
echo "📍 Status: http://0.0.0.0:8000/status"
echo "📍 Evaluate: POST http://0.0.0.0:8000/evaluate"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

python server.py
