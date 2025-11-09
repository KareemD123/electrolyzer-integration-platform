#!/bin/bash
# Backend startup script

# Activate virtual environment
source venv/bin/activate

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Create data directory if it doesn't exist
mkdir -p app/data

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
