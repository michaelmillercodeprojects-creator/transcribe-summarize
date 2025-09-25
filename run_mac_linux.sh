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
    echo "You need an OpenAI API key to use this tool."
    echo "Would you like to add it now?"
    echo
    echo -n "Enter your OpenAI API key (or press Enter to continue without): "
    read ADD_KEY
    
    if [ ! -z "$ADD_KEY" ]; then
        echo "OPENAI_API_KEY=$ADD_KEY" > .env
        echo -e "${GREEN}API key saved to .env file!${NC}"
        echo
    else
        echo
        echo "You can add your API key later by:"
        echo "1. Creating a .env file in this folder"
        echo "2. Adding: OPENAI_API_KEY=your_key_here"
        echo
        echo "Get your API key from: https://platform.openai.com/api-keys"
        echo
    fi
    read -p "Press Enter to continue..."
fi

# Run the application
$PYTHON_CMD run_app.py

echo
read -p "Press Enter to exit..."