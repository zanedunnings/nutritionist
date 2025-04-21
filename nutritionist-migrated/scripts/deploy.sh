#!/bin/bash

# 🚀 Set Variables - EDIT THESE FOR YOUR PROJECT
PROJECT_NAME="nutritionist" # Change this for each new project
LOCAL_PROJECT_PATH="."  # Current directory (nutritionist-migrated)
REMOTE_USER="root"
REMOTE_HOST="${SERVER_IP}" #env var
REMOTE_PROJECT_PATH="/root/${PROJECT_NAME}-migrated"  # Updated to use migrated version
SSH_KEY_PATH="~/.ssh/id_ed25519"  # Change if your key is different
PORT="8000"  # Update this to match your service file port

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ -f .env ]; then
  source .env
fi

if [ -z "$REMOTE_HOST" ]; then
  echo "Error: REMOTE_HOST not set. Please set it in .env file"
  exit 1
fi

echo -e "${BLUE}🔄 Syncing files from local to remote for ${PROJECT_NAME}...${NC}"

rsync -avz --delete \
    --exclude 'venv/' \
    --exclude 'data/' \
    --exclude '.git/' \
    --exclude '.env' \
    --exclude '__pycache__/' \
    --exclude '.pytest_cache/' \
    --exclude 'venv311/' \
    -e "ssh -i $SSH_KEY_PATH" \
    $LOCAL_PROJECT_PATH $REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_PATH

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to sync files to remote server!${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 Running remote setup script...${NC}"
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST << EOF
    set -e  # Exit if any command fails
    
    # Stop and disable old service if it exists
    echo "🛑 Stopping old service..."
    systemctl stop ${PROJECT_NAME} || true
    systemctl disable ${PROJECT_NAME} || true
    
    # Remove old service file
    echo "🗑️ Removing old service file..."
    rm -f /etc/systemd/system/${PROJECT_NAME}.service
    
    # Remove old virtual environment
    echo "🗑️ Removing old virtual environment..."
    rm -rf ${REMOTE_PROJECT_PATH}/venv
    
    cd $REMOTE_PROJECT_PATH
    
    echo "💻 Ensuring scripts are executable..."
    chmod +x scripts/remote_setup.sh
    
    echo "🔧 Running remote setup script..."
    ./scripts/remote_setup.sh
    
    if [ $? -ne 0 ]; then
        echo "❌ Remote setup script failed!"
        exit 1
    fi
    
    echo "🔄 Reloading systemd and restarting service..."
    systemctl daemon-reload
    systemctl enable ${PROJECT_NAME}
    systemctl start ${PROJECT_NAME}
    
    # Sleep to give the service time to start
    sleep 2
    
    # Check if service started successfully
    if systemctl is-active --quiet ${PROJECT_NAME}; then
        echo "✅ Service ${PROJECT_NAME} started successfully!"
    else
        echo "❌ Service ${PROJECT_NAME} failed to start!"
        echo "--- Service Status ---"
        systemctl status ${PROJECT_NAME} --no-pager
        echo "--- Last 20 Log Lines ---"
        journalctl -u ${PROJECT_NAME} -n 20 --no-pager
        exit 1
    fi
    
    # Test if the API is responding
    echo "🔍 Testing API health endpoint..."
    if curl -s http://localhost:${PORT}/health > /dev/null; then
        echo "✅ API is responding correctly!"
    else
        echo "⚠️ API is not responding on port ${PORT}. Check logs for details."
        echo "--- Last 20 Log Lines ---"
        journalctl -u ${PROJECT_NAME} -n 20 --no-pager
    fi
    
    echo "📊 Memory usage:"
    free -h
    
    echo "💾 Disk usage:"
    df -h | grep -E "Filesystem|/$"
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed! Check the output above for details.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}" 