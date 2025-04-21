#!/bin/bash

# This script runs on the remote server after files are synced
PROJECT_NAME="nutritionist" # Make sure this matches your project name in deploy.sh

echo "🔧 Setting up remote environment..."

# Ensure Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir

# Verify SQLAlchemy installation
if ! python3 -c "import sqlalchemy" &> /dev/null; then
    echo "❌ SQLAlchemy installation failed"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data

# Create static directories if they don't exist
if [ ! -d "static" ]; then
    echo "📁 Creating static directories..."
    mkdir -p static/css
    mkdir -p static/js
    mkdir -p static/images
fi

# Create empty database file if it doesn't exist
if [ ! -f "data/${PROJECT_NAME}.db" ]; then
    echo "🗄️ Creating database file..."
    touch "data/${PROJECT_NAME}.db"
fi

# Create and configure systemd service
echo "⚙️ Configuring systemd service..."
cat > /etc/systemd/system/nutritionist.service << EOL
[Unit]
Description=Nutritionist App
After=network.target

[Service]
User=root
WorkingDirectory=/root/nutritionist-migrated
Environment="PATH=/root/nutritionist-migrated/venv/bin"
Environment="PYTHONPATH=/root/nutritionist-migrated"
ExecStart=/root/nutritionist-migrated/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=nutritionist

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and start service
echo "🔄 Reloading systemd..."
systemctl daemon-reload
systemctl enable nutritionist

# Stop any existing service
echo "🛑 Stopping existing service..."
systemctl stop nutritionist || true

# Start the service
echo "🚀 Starting service..."
systemctl start nutritionist

# Check service status
echo "📊 Checking service status..."
systemctl status nutritionist

echo "✅ Remote setup complete!" 