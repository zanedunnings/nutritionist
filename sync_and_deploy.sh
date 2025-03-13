#!/bin/bash

# 🚀 Set Variables
LOCAL_PROJECT_PATH="."  # Change this
REMOTE_USER="root"
REMOTE_HOST="5.161.86.187"  # Change this
REMOTE_PROJECT_PATH="/root/nutritionist"
SSH_KEY_PATH="~/.ssh/id_ed25519"  # Change if needed

echo "🔄 Syncing files from local to remote..."
rsync -avz --delete \
    --exclude 'venv/' \
    --exclude 'meal_plans.db' \
    -e "ssh -i $SSH_KEY_PATH" \
    $LOCAL_PROJECT_PATH $REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_PATH

echo "🔄 Running remote setup script..."
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST << EOF
    set -e  # Exit if any command fails
    cd $REMOTE_PROJECT_PATH

    # Ensure the script is executable
    chmod +x remote_setup.sh

    # Run the remote setup script
    ./remote_setup.sh

    # Restart the FastAPI service
    sudo systemctl restart nutritionist
EOF

echo "✅ Deployment complete!"
