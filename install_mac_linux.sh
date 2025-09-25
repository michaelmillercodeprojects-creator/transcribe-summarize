#!/bin/bash

echo "========================================"
echo "Financial Transcription Tool Installer"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Python is not installed or not in PATH.${NC}"
        echo
        echo "Please install Python first:"
        echo
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "On macOS:"
            echo "1. Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "2. Install Python: brew install python"
            echo "OR download from: https://www.python.org/downloads/"
        else
            echo "On Ubuntu/Debian:"
            echo "sudo apt update && sudo apt install python3 python3-pip"
            echo
            echo "On CentOS/RHEL:"
            echo "sudo yum install python3 python3-pip"
            echo
            echo "On Arch Linux:"
            echo "sudo pacman -S python python-pip"
        fi
        echo
        echo "After installation, run this script again."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}Python found! Using: $PYTHON_CMD${NC}"
echo

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
MIN_VERSION="3.8"

if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
    echo -e "${RED}Python $PYTHON_VERSION detected. Python 3.8+ required.${NC}"
    echo "Please upgrade Python and try again."
    exit 1
fi

echo "Installing requirements..."
echo

# Upgrade pip first
echo "Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip --user

# Install requirements
echo "Installing required packages..."
$PYTHON_CMD -m pip install -r requirements.txt --user

if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}ERROR: Failed to install requirements!${NC}"
    echo "Please check your internet connection and try again."
    echo "You may also need to install development tools:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "xcode-select --install"
    else
        echo "sudo apt install build-essential python3-dev (Ubuntu/Debian)"
    fi
    exit 1
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "You can now run the application:"
echo -e "${YELLOW}- Run: $PYTHON_CMD run_app.py${NC}"
echo
echo "Make sure to:"
echo "1. Create a .env file with your OpenAI API key"
echo "2. Add: OPENAI_API_KEY=your_key_here"
echo
echo "Press Enter to continue..."
read