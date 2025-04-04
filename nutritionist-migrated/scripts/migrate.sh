#!/bin/bash

# Create necessary directories
mkdir -p data
mkdir -p static
mkdir -p templates

# Copy existing templates
cp -r ../templates/* templates/

# Copy existing static files
cp -r ../static/* static/ 2>/dev/null || :

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update it with your configuration."
fi

# Initialize database
python -c "
from app import Base, engine
Base.metadata.create_all(bind=engine)
print('Database initialized successfully')
"

echo "Migration completed successfully!"
echo "Next steps:"
echo "1. Update your .env file with the correct configuration"
echo "2. Run the application with: uvicorn app:app --reload" 