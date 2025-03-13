#!/bin/bash

set -e  # Exit on error

echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Check if the service is already running
if sudo systemctl is-active --quiet nutritionist; then
    echo "♻️ Nutritionist service is running. Restarting..."
    sudo systemctl restart nutritionist
else
    echo "🚀 Nutritionist service is not running. Starting..."
    sudo systemctl enable nutritionist
    sudo systemctl start nutritionist
fi

echo "📊 Checking service status..."
sudo systemctl status nutritionist --no-pager

