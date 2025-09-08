#!/bin/bash
# Run LibriSeVoc API Server in Background with Process Management

set -e

SERVER_NAME="librisevoc-server"
PID_FILE="/tmp/${SERVER_NAME}.pid"
LOG_FILE="server.log"

# Function to start server
start_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "❌ Server is already running (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    echo "🚀 Starting LibriSeVoc API Server in background..."
    
    # Check virtual environment
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Please run setup first."
        exit 1
    fi
    
    # Activate virtual environment and start server
    source venv/bin/activate
    mkdir -p uploads
    
    # Start server in background
    nohup python server.py > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait a moment to check if server started successfully
    sleep 2
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ Server started successfully!"
        echo "📍 PID: $SERVER_PID"
        echo "📍 Server URL: http://0.0.0.0:8000"
        echo "📍 Log file: $LOG_FILE"
        echo "📍 PID file: $PID_FILE"
        echo ""
        echo "Use './run_server_background.sh stop' to stop the server"
        echo "Use './run_server_background.sh status' to check server status"
        echo "Use './run_server_background.sh logs' to view logs"
    else
        echo "❌ Failed to start server. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to stop server
stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Server is not running (no PID file found)"
        exit 1
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 Stopping LibriSeVoc API Server (PID: $PID)..."
        kill $PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️  Forcing server shutdown..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Server stopped successfully"
    else
        echo "❌ Server process not found (PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

# Function to check server status
check_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "✅ Server is running (PID: $PID)"
        echo "📍 Server URL: http://0.0.0.0:8000"
        echo "📍 Log file: $LOG_FILE"
        
        # Try to check if server is responding
        if command -v curl >/dev/null 2>&1; then
            echo "📊 Health check:"
            curl -s http://localhost:8000/ | head -3 || echo "❌ Server not responding"
        fi
    else
        echo "❌ Server is not running"
        if [ -f "$PID_FILE" ]; then
            echo "🧹 Cleaning up stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Last 50 lines of server logs:"
        echo "=================================="
        tail -50 "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
    fi
}

# Function to restart server
restart_server() {
    echo "🔄 Restarting LibriSeVoc API Server..."
    stop_server 2>/dev/null || true
    sleep 2
    start_server
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server in background"
        echo "  stop    - Stop the running server"
        echo "  restart - Restart the server"
        echo "  status  - Check if server is running"
        echo "  logs    - Show recent server logs"
        exit 1
        ;;
esac
