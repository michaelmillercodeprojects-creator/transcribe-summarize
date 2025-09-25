#!/bin/bash

echo "Starting Financial Transcription Tool..."
echo

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Python is not installed or not in PATH!${NC}"
    echo "Please run install_mac_linux.sh first."
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo
    echo "You need to create a .env file with your OpenAI API key:"
    echo "1. Create a file named '.env' in this folder"
    echo "2. Add this line: OPENAI_API_KEY=your_api_key_here"
    echo "3. Replace 'your_api_key_here' with your actual OpenAI API key"
    echo
    echo "Get your API key from: https://platform.openai.com/api-keys"
    echo
    read -p "Press Enter to continue anyway..."
fi

# Run the application
$PYTHON_CMD run_app.py

echo
read -p "Press Enter to exit..."