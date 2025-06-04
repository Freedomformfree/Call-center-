#!/bin/bash

# 🚀 VoiceConnect Pro - One-Click Startup Script
# Run this to set up and launch the complete project

echo "🤖 VoiceConnect Pro - Starting Setup..."
echo "========================================"

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Run the Python setup script
echo "🔄 Running setup script..."
python3 run.py

echo "✅ Setup complete!"