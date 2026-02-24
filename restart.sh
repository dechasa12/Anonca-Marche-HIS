#!/bin/bash
echo "🔄 Restarting AOU Marche HIS..."

# Kill process on port 8000
echo "Killing process on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Wait a moment
sleep 2

# Start the server
echo "Starting server..."
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python backend/python/main_integrated.py
