#!/bin/bash
# Setup Supervisor for LibriSeVoc API Server

set -e

echo "🔧 Setting up Supervisor for LibriSeVoc API Server..."

# Get current directory
CURRENT_DIR=$(pwd)
VENV_PATH="$CURRENT_DIR/venv"
USER_NAME=$(whoami)

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please run the setup first to create the virtual environment"
    exit 1
fi

# Install supervisor in the virtual environment
echo "📦 Installing Supervisor..."
source venv/bin/activate
pip install supervisor

# Create supervisor configuration directory
mkdir -p supervisor_conf

# Update supervisor config with actual paths
cat > supervisor_conf/librisevoc.conf << EOF
[program:librisevoc-api]
command=$VENV_PATH/bin/python server.py
directory=$CURRENT_DIR
user=$USER_NAME
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$CURRENT_DIR/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
stderr_logfile=$CURRENT_DIR/supervisor_error.log
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=3
environment=PATH="$VENV_PATH/bin"
killasgroup=true
stopasgroup=true
EOF

# Create supervisord main config
cat > supervisor_conf/supervisord.conf << EOF
[unix_http_server]
file=$CURRENT_DIR/supervisor.sock

[supervisord]
logfile=$CURRENT_DIR/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=$CURRENT_DIR/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix://$CURRENT_DIR/supervisor.sock

[include]
files = $CURRENT_DIR/supervisor_conf/*.conf
EOF

# Create management scripts
cat > start_with_supervisor.sh << 'EOF'
#!/bin/bash
# Start LibriSeVoc API Server with Supervisor

CURRENT_DIR=$(pwd)

echo "🚀 Starting LibriSeVoc API Server with Supervisor..."

# Activate virtual environment
source venv/bin/activate

# Start supervisord
supervisord -c supervisor_conf/supervisord.conf

# Wait a moment for startup
sleep 2

# Check status
supervisorctl -c supervisor_conf/supervisord.conf status

echo "✅ Server management commands:"
echo "  Status:  supervisorctl -c supervisor_conf/supervisord.conf status"
echo "  Stop:    supervisorctl -c supervisor_conf/supervisord.conf stop librisevoc-api"
echo "  Start:   supervisorctl -c supervisor_conf/supervisord.conf start librisevoc-api"
echo "  Restart: supervisorctl -c supervisor_conf/supervisord.conf restart librisevoc-api"
echo "  Logs:    supervisorctl -c supervisor_conf/supervisord.conf tail -f librisevoc-api"
echo "  Shutdown: supervisorctl -c supervisor_conf/supervisord.conf shutdown"
echo ""
echo "📍 Server URL: http://0.0.0.0:8000"
echo "📍 Logs: supervisor.log"
EOF

chmod +x start_with_supervisor.sh

echo "✅ Supervisor setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the server: ./start_with_supervisor.sh"
echo "2. Check status: supervisorctl -c supervisor_conf/supervisord.conf status"
echo "3. View logs: tail -f supervisor.log"
echo ""
echo "🎯 The server will automatically restart if it crashes!"
