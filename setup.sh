#!/bin/bash

echo "Setting up Zyte API Scraper..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please add your Zyte API key to the .env file"
else
    echo ".env file already exists"
fi

echo "Setup complete! You can now run the scraper with:"
echo "docker-compose run scraper https://example.com"
