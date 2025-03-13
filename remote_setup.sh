#!/bin/bash

set -e  # Exit if any command fails

echo "🔄 Checking for Python & virtual environment setup..."

# Install required system packages (fixes externally managed environment issues)
sudo apt update
sudo apt install -y python3-venv python3-pip

# Ensure the virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔄 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Fix "externally managed environment" issue
echo "🔄 Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --break-system-packages

echo "✅ Remote setup complete!"

