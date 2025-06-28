#!/bin/bash

# FinTrack Deployment Script

echo "🚀 Deploying FinTrack - Personal Finance Dashboard"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Check if MongoDB is running (optional)
if command -v mongod &> /dev/null; then
    if pgrep -x "mongod" > /dev/null; then
        echo "✅ MongoDB is running"
    else
        echo "⚠️  MongoDB is not running. The app will use session storage."
        echo "   To use MongoDB, start it with: sudo systemctl start mongod"
    fi
else
    echo "⚠️  MongoDB is not installed. The app will use session storage."
fi

# Run the application
echo "🌐 Starting FinTrack..."
echo "   The app will be available at: http://localhost:8501"
echo "   Press Ctrl+C to stop the server"
echo ""

streamlit run connect.py --server.port 8501 --server.address 0.0.0.0 